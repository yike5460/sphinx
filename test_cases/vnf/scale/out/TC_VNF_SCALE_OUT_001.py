import logging

from api.generic import constants
from test_cases import TestCase
from api.generic.traffic import Traffic
from api.generic.vnfm import Vnfm

# Instantiate logger
LOG = logging.getLogger(__name__)


class TC_VNF_SCALE_OUT_001(TestCase):
    """
    TC_VNF_SCALE_OUT_001 Scale-Out VNF instance

    Sequence:
    1. Instantiate the VNF without load
    2. Validate VNF instantiation state is INSTANTIATED and VNF state is STARTED
    3. Start the low traffic load
    4. Validate the provided functionality and all traffic goes through
    5. Trigger a resize of the VNF resources
    6. Validate VNF has resized by adding VNFCs
    7. Determine if and length of service disruption
    8. Generate more traffic to validate the higher capacity
    9. Validate increased capacity without loss
    """

    def setup(self):
        LOG.info('Starting setup for TC_VNF_SCALE_OUT_001')

        # Create objects needed by the test.
        self.vnfm = Vnfm(vendor=self.tc_input['vnfm_params']['type'], **self.tc_input['vnfm_params']['client_config'])
        self.traffic = Traffic(self.tc_input['traffic_params']['type'],
                               **self.tc_input['traffic_params']['client_config'])
        self.register_for_cleanup(self.traffic.destroy)

        # Initialize test case result.
        self.tc_result['overall_status'] = constants.TEST_PASSED
        self.tc_result['error_info'] = 'No errors'

        LOG.info('Finished setup for TC_VNF_SCALE_OUT_001')

        return True

    def run(self):
        LOG.info('Starting TC_VNF_SCALE_OUT_001')

        # --------------------------------------------------------------------------------------------------------------
        # 1. Instantiate the VNF without load
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Instantiating the VNF without load')
        self.time_record.START('instantiate_vnf')
        self.vnf_instance_id = self.vnfm.vnf_create_and_instantiate(
                                                                vnfd_id=self.tc_input['vnfd_id'], flavour_id=None,
                                                                vnf_instance_name=self.tc_input['vnf']['instance_name'],
                                                                vnf_instance_description=None)
        if self.vnf_instance_id is None:
            LOG.error('TC_VNF_SCALE_OUT_001 execution failed')
            LOG.debug('Unexpected VNF instantiation ID')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'VNF instantiation operation failed'
            return False

        self.time_record.END('instantiate_vnf')

        self.tc_result['durations']['instantiate_vnf'] = self.time_record.duration('instantiate_vnf')

        self.register_for_cleanup(self.vnfm.vnf_terminate_and_delete, vnf_instance_id=self.vnf_instance_id,
                                  termination_type='graceful')

        # --------------------------------------------------------------------------------------------------------------
        # 2. Validate VNF instantiation state is INSTANTIATED and VNF state is STARTED
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating VNF instantiation state is INSTANTIATED')
        vnf_info = self.vnfm.vnf_query(filter={'vnf_instance_id': self.vnf_instance_id})
        if vnf_info.instantiation_state != constants.VNF_INSTANTIATED:
            LOG.error('TC_VNF_SCALE_OUT_001 execution failed')
            LOG.debug('Unexpected VNF instantiation state')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'VNF instantiation state was not "%s" after the VNF was instantiated' \
                                           % constants.VNF_INSTANTIATED
            return False

        LOG.info('Validating VNF state is STARTED')
        if vnf_info.instantiated_vnf_info.vnf_state != constants.VNF_STARTED:
            LOG.error('TC_VNF_SCALE_OUT_001 execution failed')
            LOG.debug('Unexpected VNF state')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'VNF state was not "%s" after the VNF was instantiated' % \
                                           constants.VNF_STARTED
            return False

        self.tc_result['resources']['Initial'] = self.vnfm.get_allocated_vresources(self.vnf_instance_id)

        # --------------------------------------------------------------------------------------------------------------
        # 3. Start the low traffic load
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Starting the low traffic load')
        if not self.traffic.configure(traffic_load='LOW_TRAFFIC_LOAD',
                                      traffic_config=self.tc_input['traffic_params']['traffic_config']):
            LOG.error('TC_VNF_SCALE_OUT_001 execution failed')
            LOG.debug('Low traffic load and traffic configuration parameter could not be applied')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Low traffic load and traffic configuration parameter could not be applied'
            return False

        # Configure stream destination MAC address(es)
        dest_mac_addr_list = ''
        for ext_cp_info in vnf_info.instantiated_vnf_info.ext_cp_info:
            if ext_cp_info.cpd_id == self.tc_input['traffic_params']['traffic_config']['left_cp_name']:
                dest_mac_addr_list += ext_cp_info.address[0] + ' '
        self.traffic.config_traffic_stream(dest_mac_addr_list)

        if not self.traffic.start(return_when_emission_starts=True):
            LOG.error('TC_VNF_SCALE_OUT_001 execution failed')
            LOG.debug('Traffic could not be started')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Low traffic could not be started'
            return False

        self.register_for_cleanup(self.traffic.stop)

        # --------------------------------------------------------------------------------------------------------------
        # 4. Validate the provided functionality and all traffic goes through
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating the provided functionality and all traffic goes through')
        if not self.traffic.does_traffic_flow(delay_time=5):
            LOG.error('TC_VNF_SCALE_OUT_001 execution failed')
            LOG.debug('Traffic is not flowing')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Low traffic did not flow'
            return False

        if self.traffic.any_traffic_loss():
            LOG.error('TC_VNF_SCALE_OUT_001 execution failed')
            LOG.debug('Traffic is flowing with packet loss')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Low traffic flew with packet loss'
            return False

        self.tc_result['scaling_out']['traffic_before'] = 'LOW_TRAFFIC_LOAD'

        if not self.vnfm.validate_allocated_vresources(self.tc_input['vnfd_id'], self.vnf_instance_id):
            LOG.error('TC_VNF_SCALE_OUT_001 execution failed')
            LOG.debug('Could not validate allocated vResources')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Could not validate allocated vResources'
            return False

        # --------------------------------------------------------------------------------------------------------------
        # 5. Trigger a resize of the VNF resources
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Triggering a resize of the VNF resources')
        self.time_record.START('scale_out_vnf')
        if self.vnfm.vnf_scale_sync(self.vnf_instance_id, scale_type='out',
                                    aspect_id=self.tc_input['scaling']['aspect'],
                                    additional_param={'scaling_policy_name': self.tc_input['scaling']['policies'][0]}) \
                != constants.OPERATION_SUCCESS:
            LOG.error('TC_VNF_SCALE_OUT_001 execution failed')
            LOG.debug('Could not scale out VNF')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Could not scale out VNF'
            return False

        self.time_record.END('scale_out_vnf')

        self.tc_result['durations']['scale_out_vnf'] = self.time_record.duration('scale_out_vnf')

        self.tc_result['resources']['After scale out'] = self.vnfm.get_allocated_vresources(self.vnf_instance_id)

        self.tc_result['scaling_out']['status'] = 'Success'

        # --------------------------------------------------------------------------------------------------------------
        # 6. Validate VNF has resized by adding VNFCs
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating VNF has resized by adding VNFCs')
        vnf_info = self.vnfm.vnf_query(filter={'vnf_instance_id': self.vnf_instance_id})
        if len(vnf_info.instantiated_vnf_info.vnfc_resource_info) != self.tc_input['scaling']['default_instances'] + \
                                                                     self.tc_input['scaling']['increment']:
            LOG.error('TC_VNF_SCALE_OUT_001 execution failed')
            LOG.debug('VNFCs not added after VNF scaled out')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'VNFCs not added after VNF scaled out'
            return False

        self.tc_result['scaling_out']['level'] = self.tc_input['scaling']['default_instances'] + \
                                                 self.tc_input['scaling']['increment']

        # --------------------------------------------------------------------------------------------------------------
        # 7. Determine if and length of service disruption
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Determining if and length of service disruption')
        self.tc_result['durations']['service_disruption'] = self.traffic.calculate_service_disruption_length()

        # --------------------------------------------------------------------------------------------------------------
        # 8. Generate more traffic to validate the higher capacity
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Generating more traffic to validate the higher capacity')

        # Stop traffic.
        if not self.traffic.stop():
            LOG.error('TC_VNF_SCALE_OUT_001 execution failed')
            LOG.debug('Traffic could not be stopped')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Low traffic could not be stopped'
            return False

        # Configure stream destination MAC address(es).
        dest_mac_addr_list = ''
        for ext_cp_info in vnf_info.instantiated_vnf_info.ext_cp_info:
            if ext_cp_info.cpd_id == self.tc_input['traffic_params']['traffic_config']['left_cp_name']:
                dest_mac_addr_list += ext_cp_info.address[0] + ' '

        self.traffic.config_traffic_stream(dest_mac_addr_list)
        self.traffic.config_traffic_load('NORMAL_TRAFFIC_LOAD')

        # Start traffic.
        if not self.traffic.start(return_when_emission_starts=True):
            LOG.error('TC_VNF_SCALE_OUT_001 execution failed')
            LOG.debug('Traffic could not be started')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Normal traffic could not be started'
            return False

        # --------------------------------------------------------------------------------------------------------------
        # 9. Validate increased capacity without loss
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating increased capacity without loss')
        if not self.traffic.does_traffic_flow(delay_time=5):
            LOG.error('TC_VNF_SCALE_OUT_001 execution failed')
            LOG.debug('Traffic is not flowing')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Normal traffic did not flow'
            return False

        if self.traffic.any_traffic_loss():
            LOG.error('TC_VNF_SCALE_OUT_001 execution failed')
            LOG.debug('Traffic is flowing with packet loss')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Normal traffic flew with packet loss'
            return False

        self.tc_result['scaling_out']['traffic_after'] = 'NORMAL_TRAFFIC_LOAD'

        LOG.info('TC_VNF_SCALE_OUT_001 execution completed successfully')

        return True
