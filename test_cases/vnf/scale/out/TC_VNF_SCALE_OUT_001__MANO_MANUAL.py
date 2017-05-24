import logging

from api.generic import constants
from api.generic.mano import Mano
from api.generic.traffic import Traffic
from api.structures.objects import ScaleNsData, ScaleNsByStepsData
from test_cases import TestCase
from utils.misc import generate_name

# Instantiate logger
LOG = logging.getLogger(__name__)


class TC_VNF_SCALE_OUT_001__MANO_MANUAL(TestCase):
    """
    TC_VNF_SCALE_OUT_001__MANO_MANUAL Scale-out VNF instance with manual scaling event generated by MANO

    Sequence:
    1. Instantiate the NS
    2. Validate NS state is INSTANTIATED
    3. Validate VNF instantiation state is INSTANTIATED and VNF state is STARTED
    4. Start the low traffic load
    5. Validate the provided functionality and all traffic goes through
    6. Trigger a resize of the NS resources by instructing the MANO to scale out the NS
    7. Validate NS has resized by adding VNFs
    8. Determine if and length of service disruption
    9. Start the normal traffic load
    10. Validate increased capacity without loss
    """

    def setup(self):
        LOG.info('Starting setup for TC_VNF_SCALE_OUT_001__MANO_MANUAL')

        # Create objects needed by the test.
        self.mano = Mano(vendor=self.tc_input['mano_params']['type'], **self.tc_input['mano_params']['client_config'])
        self.traffic = Traffic(self.tc_input['traffic_params']['type'],
                               **self.tc_input['traffic_params']['client_config'])
        self.register_for_cleanup(self.traffic.destroy)

        # Initialize test case result.
        self.tc_result['overall_status'] = constants.TEST_PASSED
        self.tc_result['error_info'] = 'No errors'
        self.tc_result['events']['instantiate_ns'] = dict()
        self.tc_result['events']['scale_out_ns'] = dict()
        self.tc_result['events']['service_disruption'] = dict()

        LOG.info('Finished setup for TC_VNF_SCALE_OUT_001__MANO_MANUAL')

        return True

    def run(self):
        LOG.info('Starting TC_VNF_SCALE_OUT_001__MANO_MANUAL')

        # --------------------------------------------------------------------------------------------------------------
        # 1. Instantiate the NS
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Instantiating the NS')
        self.time_record.START('instantiate_ns')
        self.ns_instance_id = self.mano.ns_create_and_instantiate(nsd_id=self.tc_input['nsd_id'],
                                                                  ns_name=generate_name(self.tc_input['ns']['name']),
                                                                  ns_description=None, flavour_id=None)
        if self.ns_instance_id is None:
            LOG.error('TC_VNF_SCALE_OUT_001__MANO_MANUAL execution failed')
            LOG.debug('Unexpected NS instantiation ID')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'NS instantiation operation failed'
            return False

        self.time_record.END('instantiate_ns')

        self.tc_result['events']['instantiate_ns']['duration'] = self.time_record.duration('instantiate_ns')

        self.register_for_cleanup(self.mano.ns_terminate_and_delete, ns_instance_id=self.ns_instance_id)

        # --------------------------------------------------------------------------------------------------------------
        # 2. Validate NS state is INSTANTIATED
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating NS state is INSTANTIATED')
        ns_info = self.mano.ns_query(filter={'ns_instance_id': self.ns_instance_id})
        if ns_info.ns_state != constants.NS_INSTANTIATED:
            LOG.error('TC_VNF_SCALE_OUT_001__MANO_MANUAL execution failed')
            LOG.debug('Unexpected NS state')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'NS state was not "%s" after the NS was instantiated' \
                                           % constants.NS_INSTANTIATED
            return False

        # --------------------------------------------------------------------------------------------------------------
        # 3. Validate VNF instantiation state is INSTANTIATED and VNF state is STARTED
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating VNF instantiation state is INSTANTIATED')

        # Get the instance ID of the VNF inside the NS
        self.vnf_instance_id = ns_info.vnf_info_id[0]

        vnf_info = self.mano.vnf_query(filter={'vnf_instance_id': self.vnf_instance_id})
        if vnf_info.instantiation_state != constants.VNF_INSTANTIATED:
            LOG.error('TC_VNF_SCALE_OUT_001__MANO_MANUAL execution failed')
            LOG.debug('Unexpected VNF instantiation state')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'VNF instantiation state was not "%s" after the VNF was instantiated' \
                                           % constants.VNF_INSTANTIATED
            return False

        LOG.info('Validating VNF state is STARTED')
        if vnf_info.instantiated_vnf_info.vnf_state != constants.VNF_STARTED:
            LOG.error('TC_VNF_SCALE_OUT_001__MANO_MANUAL execution failed')
            LOG.debug('Unexpected VNF state')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'VNF state was not "%s" after the VNF was instantiated' % \
                                           constants.VNF_STARTED
            return False

        self.tc_result['resources']['Initial'] = self.mano.get_allocated_vresources(self.vnf_instance_id)

        # --------------------------------------------------------------------------------------------------------------
        # 4. Start the low traffic load
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Starting the low traffic load')
        if not self.traffic.configure(traffic_load='LOW_TRAFFIC_LOAD',
                                      traffic_config=self.tc_input['traffic_params']['traffic_config']):
            LOG.error('TC_VNF_SCALE_OUT_001__MANO_MANUAL execution failed')
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
            LOG.error('TC_VNF_SCALE_OUT_001__MANO_MANUAL execution failed')
            LOG.debug('Traffic could not be started')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Low traffic could not be started'
            return False

        self.register_for_cleanup(self.traffic.stop)

        # --------------------------------------------------------------------------------------------------------------
        # 5. Validate the provided functionality and all traffic goes through
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating the provided functionality and all traffic goes through')
        if not self.traffic.does_traffic_flow(delay_time=5):
            LOG.error('TC_VNF_SCALE_OUT_001__MANO_MANUAL execution failed')
            LOG.debug('Traffic is not flowing')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Low traffic did not flow'
            return False

        if self.traffic.any_traffic_loss():
            LOG.error('TC_VNF_SCALE_OUT_001__MANO_MANUAL execution failed')
            LOG.debug('Traffic is flowing with packet loss')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Low traffic flew with packet loss'
            return False

        self.tc_result['scaling_out']['traffic_before'] = 'LOW_TRAFFIC_LOAD'

        if not self.mano.validate_allocated_vresources(self.tc_input['vnfd_id'], self.vnf_instance_id):
            LOG.error('TC_VNF_SCALE_OUT_001__MANO_MANUAL execution failed')
            LOG.debug('Could not validate allocated vResources')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Could not validate allocated vResources'
            return False

        # --------------------------------------------------------------------------------------------------------------
        # 6. Trigger a resize of the NS resources by instructing the MANO to scale out the NS
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Triggering a resize of the NS resources by instructing the MANO to scale out the NS')

        # Build the ScaleNsData information element
        scale_ns_data = ScaleNsData()
        scale_ns_data.scale_ns_by_steps_data = ScaleNsByStepsData()
        scale_ns_data.scale_ns_by_steps_data.scaling_direction = 'scale_out'
        scale_ns_data.scale_ns_by_steps_data.aspect_id = self.tc_input['scaling']['aspect']
        scale_ns_data.scale_ns_by_steps_data.number_of_steps = self.tc_input['scaling']['increment']

        self.time_record.START('scale_out_ns')
        if self.mano.ns_scale_sync(self.ns_instance_id, scale_type='scale_ns', scale_ns_data=scale_ns_data) \
                != constants.OPERATION_SUCCESS:
            LOG.error('TC_VNF_SCALE_OUT_001__MANO_MANUAL execution failed')
            LOG.debug('MANO could not scale out the NS')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'MANO could not scale out the NS'
            self.tc_result['scaling_out']['status'] = 'Fail'
            return False

        self.time_record.END('scale_out_ns')

        self.tc_result['events']['scale_out_ns']['duration'] = self.time_record.duration('scale_out_ns')

        self.tc_result['resources']['After scale out'] = dict()
        ns_info = self.mano.ns_query(filter={'ns_instance_id': self.ns_instance_id})
        for vnf_instance_id in ns_info.vnf_info_id:
            self.tc_result['resources']['After scale out'].update(self.mano.get_allocated_vresources(vnf_instance_id))

        self.tc_result['scaling_out']['status'] = 'Success'

        # --------------------------------------------------------------------------------------------------------------
        # 7. Validate NS has resized by adding VNFs
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating NS has resized by adding VNFs')
        if len(ns_info.vnf_info_id) != self.tc_input['scaling']['default_instances'] + \
                self.tc_input['scaling']['increment']:
            LOG.error('TC_VNF_SCALE_OUT_001__MANO_MANUAL execution failed')
            LOG.debug('VNFs not added after NS scaled out')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'VNFs not added after NS scaled out'
            return False

        self.tc_result['scaling_out']['level'] = self.tc_input['scaling']['default_instances'] + \
                                                 self.tc_input['scaling']['increment']

        # --------------------------------------------------------------------------------------------------------------
        # 8. Determine if and length of service disruption
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Determining if and length of service disruption')
        self.tc_result['events']['service_disruption']['duration'] = self.traffic.calculate_service_disruption_length()

        # --------------------------------------------------------------------------------------------------------------
        # 9. Start the normal traffic load
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Starting the normal traffic load')

        # Stop the low traffic load.
        if not self.traffic.stop():
            LOG.error('TC_VNF_SCALE_OUT_001__MANO_MANUAL execution failed')
            LOG.debug('Traffic could not be stopped')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Low traffic could not be stopped'
            return False

        # Configure stream destination MAC address(es).
        dest_mac_addr_list = ''
        for vnf_instance_id in ns_info.vnf_info_id:
            vnf_info = self.mano.vnf_query(filter={'vnf_instance_id': vnf_instance_id})
            for ext_cp_info in vnf_info.instantiated_vnf_info.ext_cp_info:
                if ext_cp_info.cpd_id == self.tc_input['traffic_params']['traffic_config']['left_cp_name']:
                    dest_mac_addr_list += ext_cp_info.address[0] + ' '

        self.traffic.config_traffic_stream(dest_mac_addr_list)
        self.traffic.config_traffic_load('NORMAL_TRAFFIC_LOAD')

        # Start the normal traffic load.
        if not self.traffic.start(return_when_emission_starts=True):
            LOG.error('TC_VNF_SCALE_OUT_001__MANO_MANUAL execution failed')
            LOG.debug('Traffic could not be started')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Normal traffic could not be started'
            return False

        # --------------------------------------------------------------------------------------------------------------
        # 10. Validate increased capacity without loss
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating increased capacity without loss')
        if not self.traffic.does_traffic_flow(delay_time=5):
            LOG.error('TC_VNF_SCALE_OUT_001__MANO_MANUAL execution failed')
            LOG.debug('Traffic is not flowing')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Normal traffic did not flow'
            return False

        if self.traffic.any_traffic_loss():
            LOG.error('TC_VNF_SCALE_OUT_001__MANO_MANUAL execution failed')
            LOG.debug('Traffic is flowing with packet loss')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Normal traffic flew with packet loss'
            return False

        self.tc_result['scaling_out']['traffic_after'] = 'NORMAL_TRAFFIC_LOAD'

        LOG.info('TC_VNF_SCALE_OUT_001__MANO_MANUAL execution completed successfully')

        return True
