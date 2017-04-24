import logging
import time

from api.generic import constants
from api.generic.mano import Mano
from api.generic.traffic import Traffic
from test_cases import TestCase

# Instantiate logger
LOG = logging.getLogger(__name__)


class TC_VNF_COMPLEX_001(TestCase):
    """
    TC_VNF_COMPLEX_001 VNF Start and Scaling with max traffic load

    Sequence:
    1. Start the max traffic load
    2. Instantiate the VNF
    3. Validate VNF instantiation state is INSTANTIATED and VNF state is STARTED
    4. Wait for the VNF to scale out to the maximum
    5. Calculate the time for the activation
    6. Validate traffic flows with no dropped packets
    7. Validate allocated vResources
    8. Stop the VNF
    9. Validate that no traffic flows once stop is completed
    """

    def setup(self):
        LOG.info('Starting setup for TC_VNF_COMPLEX_001')

        # Create objects needed by the test.
        self.mano = Mano(vendor=self.tc_input['mano_params']['type'], **self.tc_input['mano_params']['client_config'])
        self.traffic = Traffic(self.tc_input['traffic_params']['type'],
                               **self.tc_input['traffic_params']['client_config'])
        self.register_for_cleanup(self.traffic.destroy)

        # Initialize test case result.
        self.tc_result['overall_status'] = constants.TEST_PASSED
        self.tc_result['error_info'] = 'No errors'
        self.tc_result['events']['instantiate_vnf'] = dict()
        self.tc_result['events']['scale_out_vnf'] = dict()
        self.tc_result['events']['stop_vnf'] = dict()
        self.tc_result['events']['traffic_activation'] = dict()
        self.tc_result['events']['traffic_deactivation'] = dict()

        LOG.info('Finished setup for TC_VNF_COMPLEX_001')

        return True

    def run(self):
        LOG.info('Starting TC_VNF_COMPLEX_001')

        # --------------------------------------------------------------------------------------------------------------
        # 1. Start the max traffic load
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Starting the max traffic load')
        if not self.traffic.configure(traffic_load='MAX_TRAFFIC_LOAD',
                                      traffic_config=self.tc_input['traffic_params']['traffic_config']):
            LOG.error('TC_VNF_COMPLEX_001 execution failed')
            LOG.debug('Max traffic load and traffic configuration parameter could not be applied')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Max traffic load and traffic configuration parameter could not be applied'
            return False

        if not self.traffic.start(return_when_emission_starts=True):
            LOG.error('TC_VNF_COMPLEX_001 execution failed')
            LOG.debug('Traffic could not be started')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Max traffic could not be started'
            return False

        self.register_for_cleanup(self.traffic.stop)

        # --------------------------------------------------------------------------------------------------------------
        # 2. Instantiate the VNF
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Instantiating the VNF')
        self.time_record.START('instantiate_vnf')
        self.vnf_instance_id = self.mano.vnf_create_and_instantiate(
                                                                vnfd_id=self.tc_input['vnfd_id'], flavour_id=None,
                                                                vnf_instance_name=self.tc_input['vnf']['instance_name'],
                                                                vnf_instance_description=None)
        if self.vnf_instance_id is None:
            LOG.error('TC_VNF_COMPLEX_001 execution failed')
            LOG.debug('Unexpected VNF instantiation ID')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'VNF instantiation operation failed'
            return False

        self.time_record.END('instantiate_vnf')

        self.tc_result['events']['instantiate_vnf']['duration'] = self.time_record.duration('instantiate_vnf')

        self.register_for_cleanup(self.mano.vnf_terminate_and_delete, vnf_instance_id=self.vnf_instance_id,
                                  termination_type='graceful')

        # --------------------------------------------------------------------------------------------------------------
        # 3. Validate VNF instantiation state is INSTANTIATED and VNF state is STARTED
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating VNF instantiation state is INSTANTIATED')
        vnf_info = self.mano.vnf_query(filter={'vnf_instance_id': self.vnf_instance_id})
        if vnf_info.instantiation_state != constants.VNF_INSTANTIATED:
            LOG.error('TC_VNF_COMPLEX_001 execution failed')
            LOG.debug('Unexpected VNF instantiation state')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'VNF instantiation state was not "%s" after the VNF was instantiated' \
                                           % constants.VNF_INSTANTIATED
            return False

        LOG.info('Validating VNF state is STARTED')
        if vnf_info.instantiated_vnf_info.vnf_state != constants.VNF_STARTED:
            LOG.error('TC_VNF_COMPLEX_001 execution failed')
            LOG.debug('Unexpected VNF state')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'VNF state was not "%s" after the VNF was instantiated' % \
                                           constants.VNF_STARTED
            return False

        self.tc_result['resources']['Initial'] = self.mano.get_allocated_vresources(self.vnf_instance_id)

        self.tc_result['scaling_out']['traffic_before'] = 'MAX_TRAFFIC_LOAD'

        # --------------------------------------------------------------------------------------------------------------
        # 4. Wait for the VNF to scale out to the maximum
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Waiting for the VNF to scale out to the maximum')
        # The scale out duration will include:
        # - the time it takes the VNF CPU load to increase (caused by the max traffic load)
        # - the time after which the scaling alarm is triggered
        # - the time it takes the VNF to scale out
        self.time_record.START('scale_out_vnf')
        elapsed_time = 0
        while elapsed_time < constants.SCALE_INTERVAL:
            vnf_info = self.mano.vnf_query(filter={'vnf_instance_id': self.vnf_instance_id})
            if len(vnf_info.instantiated_vnf_info.vnfc_resource_info) == self.tc_input['scaling']['max_instances']:
                break
            else:
                time.sleep(constants.POLL_INTERVAL)
                elapsed_time += constants.POLL_INTERVAL
            if elapsed_time == constants.SCALE_INTERVAL:
                LOG.error('TC_VNF_COMPLEX_001 execution failed')
                LOG.debug('VNF has not scaled out to the maximum')
                self.tc_result['overall_status'] = constants.TEST_FAILED
                self.tc_result['error_info'] = 'VNF has not scaled out to the maximum'
                self.tc_result['scaling_out']['status'] = 'Fail'
                return False

        self.time_record.END('scale_out_vnf')

        self.tc_result['scaling_out']['level'] = self.tc_input['scaling']['max_instances']

        self.tc_result['events']['scale_out_vnf']['duration'] = self.time_record.duration('scale_out_vnf')

        self.tc_result['resources']['After scale out'] = self.mano.get_allocated_vresources(self.vnf_instance_id)

        self.tc_result['scaling_out']['status'] = 'Success'

        # --------------------------------------------------------------------------------------------------------------
        # 5. Calculate the time for activation
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Calculating the time for traffic activation')
        self.tc_result['events']['traffic_activation']['duration'] = self.traffic.calculate_activation_time()

        # --------------------------------------------------------------------------------------------------------------
        # 6. Validate traffic flows with no dropped packets
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating traffic flows with no dropped packets')
        # Because the VNF scaled out, we need to reconfigure traffic so that it passes through all VNFCs.

        # Stop the max traffic load.
        if not self.traffic.stop():
            LOG.error('TC_VNF_COMPLEX_001 execution failed')
            LOG.debug('Traffic could not be stopped')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Max traffic could not be stopped'
            return False

        # Configure stream destination MAC address(es).
        dest_mac_addr_list = ''
        for ext_cp_info in vnf_info.instantiated_vnf_info.ext_cp_info:
            if ext_cp_info.cpd_id == self.tc_input['traffic_params']['traffic_config']['left_cp_name']:
                dest_mac_addr_list += ext_cp_info.address[0] + ' '

        self.traffic.config_traffic_stream(dest_mac_addr_list)
        self.traffic.clear_counters()

        # Start the max traffic load.
        if not self.traffic.start(return_when_emission_starts=True):
            LOG.error('TC_VNF_COMPLEX_001 execution failed')
            LOG.debug('Traffic could not be started')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Max traffic could not be started'
            return False

        if not self.traffic.does_traffic_flow(delay_time=5):
            LOG.error('TC_VNF_COMPLEX_001 execution failed')
            LOG.debug('Traffic is not flowing')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Max traffic did not flow'
            return False

        if self.traffic.any_traffic_loss():
            LOG.error('TC_VNF_COMPLEX_001 execution failed')
            LOG.debug('Traffic is flowing with packet loss')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Max traffic flew with packet loss'
            return False

        self.tc_result['scaling_out']['traffic_after'] = 'MAX_TRAFFIC_LOAD'

        # --------------------------------------------------------------------------------------------------------------
        # 7. Validate allocated vResources
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating allocated vResources')
        if not self.mano.validate_allocated_vresources(self.tc_input['vnfd_id'], self.vnf_instance_id):
            LOG.error('TC_VNF_COMPLEX_001 execution failed')
            LOG.debug('Could not validate allocated vResources')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Could not validate allocated vResources'
            return False

        # --------------------------------------------------------------------------------------------------------------
        # 8. Stop the VNF
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Stopping the VNF')
        # Clearing counters so traffic deactivation time is accurate
        self.traffic.clear_counters()
        self.time_record.START('stop_vnf')
        if self.mano.vnf_operate_sync(self.vnf_instance_id, change_state_to='stop') != constants.OPERATION_SUCCESS:
            LOG.error('TC_VNF_COMPLEX_001 execution failed')
            LOG.debug('Could not stop the VNF')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Could not stop the VNF'
            return False
        self.time_record.END('stop_vnf')

        self.tc_result['events']['stop_vnf']['duration'] = self.time_record.duration('stop_vnf')

        self.tc_result['events']['traffic_deactivation']['duration'] = self.traffic.calculate_deactivation_time()

        # --------------------------------------------------------------------------------------------------------------
        # 9. Validate that no traffic flows once stop is completed
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating that no traffic flows once stop is completed')
        if self.traffic.does_traffic_flow(delay_time=5):
            LOG.error('TC_VNF_COMPLEX_001 execution failed')
            LOG.debug('Traffic is still flowing')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Traffic still flew after VNF was stopped'
            return False

        LOG.info('TC_VNF_COMPLEX_001 execution completed successfully')

        return True