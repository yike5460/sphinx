import logging
import time

from api.generic import constants
from api.generic.mano import Mano
from api.generic.traffic import Traffic
from test_cases import TestCase
from utils.misc import generate_name

# Instantiate logger
LOG = logging.getLogger(__name__)


class TC_VNFC_SCALE_OUT_005_2(TestCase):
    """
    TC_VNFC_SCALE_OUT_005_2 Removal of virtualized specialized hardware acceleration for VNFC scale-in with on-demand 
    scaling event generated by VNF

    Sequence:
    1. Instantiate the VNF
    2. Validate VNF instantiation state is INSTANTIATED and VNF state is STARTED
    3. Start the low traffic load
    4. Validate traffic flows through without issues
    5. Trigger a resize of the VNF resources to use more specialized hardware by increasing the traffic load to the 
       maximum
    6. Validate VNF has resized
    7. Validate increased capacity without traffic loss
    8. Validate that MANO has allocated more specialized hardware resources and added new VNFCs
    9. Trigger a resize of the VNF resources to use less specialized hardware by decreasing the traffic load to the 
       minimum
    10. Validate VNF has resized and has decreased its capacity and removed VNFCs
    11. Validate that MANO has allocated less specialized hardware resources and the previous specialized hardware 
        resources have been freed up
    12. Determine the service disruption during the resizing
    13. Validate traffic flows through without issues
    """

    def setup(self):
        LOG.info('Starting setup for TC_VNFC_SCALE_OUT_005_2')

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
        self.tc_result['events']['service_disruption'] = dict()
        self.tc_result['events']['scale_in_vnf'] = dict()

        LOG.info('Finished setup for TC_VNFC_SCALE_OUT_005_2')

        return True

    def run(self):
        LOG.info('Starting TC_VNFC_SCALE_OUT_005_2')
        # TODO: Check the VNFD to see if hardware acceleration is present. This check will be added after we create an
        # internal representation for the VNFD.

        # --------------------------------------------------------------------------------------------------------------
        # 1. Instantiate the VNF
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Instantiating the VNF')
        self.time_record.START('instantiate_vnf')
        self.vnf_instance_id = self.mano.vnf_create_and_instantiate(
                                                 vnfd_id=self.tc_input['vnfd_id'], flavour_id=None,
                                                 vnf_instance_name=generate_name(self.tc_input['vnf']['instance_name']),
                                                 vnf_instance_description=None)
        if self.vnf_instance_id is None:
            LOG.error('TC_VNFC_SCALE_OUT_005_2 execution failed')
            LOG.debug('Unexpected VNF instantiation ID')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'VNF instantiation operation failed'
            return False

        self.time_record.END('instantiate_vnf')

        self.tc_result['events']['instantiate_vnf']['duration'] = self.time_record.duration('instantiate_vnf')

        self.register_for_cleanup(self.mano.vnf_terminate_and_delete, vnf_instance_id=self.vnf_instance_id,
                                  termination_type='graceful')

        # --------------------------------------------------------------------------------------------------------------
        # 2. Validate VNF instantiation state is INSTANTIATED and VNF state is STARTED
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating VNF instantiation state is INSTANTIATED')
        vnf_info = self.mano.vnf_query(filter={'vnf_instance_id': self.vnf_instance_id})
        if vnf_info.instantiation_state != constants.VNF_INSTANTIATED:
            LOG.error('TC_VNFC_SCALE_OUT_005_2 execution failed')
            LOG.debug('Unexpected VNF instantiation state')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'VNF instantiation state was not "%s" after the VNF was instantiated' \
                                           % constants.VNF_INSTANTIATED
            return False

        LOG.info('Validating VNF state is STARTED')
        if vnf_info.instantiated_vnf_info.vnf_state != constants.VNF_STARTED:
            LOG.error('TC_VNFC_SCALE_OUT_005_2 execution failed')
            LOG.debug('Unexpected VNF state')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'VNF state was not "%s" after the VNF was instantiated' % \
                                           constants.VNF_STARTED
            return False

        self.tc_result['resources']['Initial'] = self.mano.get_allocated_vresources(self.vnf_instance_id)

        # --------------------------------------------------------------------------------------------------------------
        # 3. Start the low traffic load
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Starting the low traffic load')
        if not self.traffic.configure(traffic_load='LOW_TRAFFIC_LOAD',
                                      traffic_config=self.tc_input['traffic_params']['traffic_config']):
            LOG.error('TC_VNFC_SCALE_OUT_005_2 execution failed')
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
            LOG.error('TC_VNFC_SCALE_OUT_005_2 execution failed')
            LOG.debug('Traffic could not be started')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Low traffic could not be started'
            return False

        self.register_for_cleanup(self.traffic.stop)

        # --------------------------------------------------------------------------------------------------------------
        # 4. Validate traffic flows through without issues
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating traffic flows through without issues')
        if not self.traffic.does_traffic_flow(delay_time=5):
            LOG.error('TC_VNFC_SCALE_OUT_005_2 execution failed')
            LOG.debug('Traffic is not flowing')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Low traffic did not flow'
            return False

        if self.traffic.any_traffic_loss():
            LOG.error('TC_VNFC_SCALE_OUT_005_2 execution failed')
            LOG.debug('Traffic is flowing with packet loss')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Low traffic flew with packet loss'
            return False

        if not self.mano.validate_allocated_vresources(self.tc_input['vnfd_id'], self.vnf_instance_id):
            LOG.error('TC_VNFC_SCALE_OUT_005_2 execution failed')
            LOG.debug('Could not validate allocated vResources')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Could not validate allocated vResources'
            return False

        self.tc_result['scaling_out']['traffic_before'] = 'LOW_TRAFFIC_LOAD'

        # --------------------------------------------------------------------------------------------------------------
        # 5. Trigger a resize of the VNF resources to use more specialized hardware by increasing the traffic load to
        #    the maximum
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Trigger a resize of the VNF resources to use more specialized hardware by increasing the traffic load'
                 ' to the maximum')
        self.traffic.config_traffic_load('MAX_TRAFFIC_LOAD')

        # --------------------------------------------------------------------------------------------------------------
        # 6. Validate VNF has resized
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating VNF has resized')
        # The scale out duration will include:
        # - the time it takes the VNF CPU load to increase (caused by the max traffic load)
        # - the time after which the scaling alarm is triggered
        # - the time it takes the VNF to scale out
        self.time_record.START('scale_out_vnf')
        elapsed_time = 0
        while elapsed_time < constants.SCALE_INTERVAL:
            vnf_info = self.mano.vnf_query(filter={'vnf_instance_id': self.vnf_instance_id})
            if len(vnf_info.instantiated_vnf_info.vnfc_resource_info) == \
                            self.tc_input['scaling']['default_instances'] + self.tc_input['scaling']['increment']:
                break
            else:
                time.sleep(constants.POLL_INTERVAL)
                elapsed_time += constants.POLL_INTERVAL
            if elapsed_time == constants.SCALE_INTERVAL:
                LOG.error('TC_VNFC_SCALE_OUT_005_2 execution failed')
                LOG.debug('VNF has not resized')
                self.tc_result['overall_status'] = constants.TEST_FAILED
                self.tc_result['error_info'] = 'VNF has not resized'
                self.tc_result['scaling_out']['status'] = 'Fail'
                return False

        self.time_record.END('scale_out_vnf')

        self.tc_result['scaling_out']['level'] = self.tc_input['scaling']['default_instances'] + \
                                                 self.tc_input['scaling']['increment']

        self.tc_result['events']['scale_out_vnf']['duration'] = self.time_record.duration('scale_out_vnf')

        self.tc_result['resources']['After scale out'] = self.mano.get_allocated_vresources(self.vnf_instance_id)

        self.tc_result['scaling_out']['status'] = 'Success'

        # --------------------------------------------------------------------------------------------------------------
        # 7. Validate increased capacity without traffic loss
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating increased capacity without traffic loss')
        # Because the VNF scaled out, we need to reconfigure traffic so that it passes through all VNFCs.

        # Stop the max traffic load.
        if not self.traffic.stop():
            LOG.error('TC_VNFC_SCALE_OUT_005_2 execution failed')
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
            LOG.error('TC_VNFC_SCALE_OUT_005_2 execution failed')
            LOG.debug('Traffic could not be started')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Max traffic could not be started'
            return False

        if not self.traffic.does_traffic_flow(delay_time=5):
            LOG.error('TC_VNFC_SCALE_OUT_005_2 execution failed')
            LOG.debug('Traffic is not flowing')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Max traffic did not flow'
            return False

        if self.traffic.any_traffic_loss():
            LOG.error('TC_VNFC_SCALE_OUT_005_2 execution failed')
            LOG.debug('Traffic is flowing with packet loss')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Max traffic flew with packet loss'
            return False

        self.tc_result['scaling_out']['traffic_after'] = 'MAX_TRAFFIC_LOAD'
        self.tc_result['scaling_in']['traffic_before'] = 'MAX_TRAFFIC_LOAD'

        # --------------------------------------------------------------------------------------------------------------
        # 8. Validate that MANO has allocated more specialized hardware resources and added new VNFCs
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validate that MANO has allocated more specialized hardware resources and added new VNFCs')
        if not self.mano.validate_allocated_vresources(self.tc_input['vnfd_id'], self.vnf_instance_id):
            LOG.error('TC_VNFC_SCALE_OUT_005_2 execution failed')
            LOG.debug('Could not validate allocated vResources')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Could not validate allocated vResources'
            return False

        # --------------------------------------------------------------------------------------------------------------
        # 9. Trigger a resize of the VNF resources to use less specialized hardware by decreasing the traffic load to
        #    the minimum
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Trigger a resize of the VNF resources to use less specialized hardware by decreasing the traffic load'
                 ' to the minimum')
        self.traffic.config_traffic_load('LOW_TRAFFIC_LOAD')

        # --------------------------------------------------------------------------------------------------------------
        # 10. Validate VNF has resized and has decreased its capacity and removed VNFCs
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating VNF has resized and has decreased its capacity and removed VNFCs')
        # The scale in duration will include:
        # - the time it takes the VNF CPU load to decrease (caused by the low traffic load)
        # - the time after which the scaling alarm is triggered
        # - the time it takes the VNF to scale in
        self.time_record.START('scale_in_vnf')
        elapsed_time = 0
        while elapsed_time < constants.SCALE_INTERVAL:
            vnf_info = self.mano.vnf_query(filter={'vnf_instance_id': self.vnf_instance_id})
            if len(vnf_info.instantiated_vnf_info.vnfc_resource_info) == self.tc_input['scaling']['default_instances']:
                break
            else:
                time.sleep(constants.POLL_INTERVAL)
                elapsed_time += constants.POLL_INTERVAL
            if elapsed_time == constants.SCALE_INTERVAL:
                LOG.error('TC_VNFC_SCALE_OUT_005_2 execution failed')
                LOG.debug('VNF has not decreased the VNFCs')
                self.tc_result['overall_status'] = constants.TEST_FAILED
                self.tc_result['error_info'] = 'VNF has not decreased the VNFCs'
                self.tc_result['scaling_in']['status'] = 'Fail'
                return False

        self.time_record.END('scale_in_vnf')

        self.tc_result['scaling_in']['level'] = self.tc_input['scaling']['default_instances']

        self.tc_result['events']['scale_in_vnf']['duration'] = self.time_record.duration('scale_in_vnf')

        self.tc_result['resources']['After scale in'] = self.mano.get_allocated_vresources(self.vnf_instance_id)

        self.tc_result['scaling_in']['status'] = 'Success'

        # --------------------------------------------------------------------------------------------------------------
        # 11. Validate that MANO has allocated less specialized hardware resources and the previous specialized hardware
        #     resources have been freed up
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validate that MANO has allocated less specialized hardware resources and the previous specialized '
                 'hardware resources have been freed up')
        if not self.mano.validate_allocated_vresources(self.tc_input['vnfd_id'], self.vnf_instance_id):
            LOG.error('TC_VNFC_SCALE_OUT_005_2 execution failed')
            LOG.debug('Could not validate allocated vResources')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Could not validate allocated vResources'
            return False

        # --------------------------------------------------------------------------------------------------------------
        # 12. Determine the service disruption during the resizing
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Determining the service disruption during the resizing')
        self.tc_result['events']['service_disruption']['duration'] = self.traffic.calculate_service_disruption_length()

        # --------------------------------------------------------------------------------------------------------------
        # 13. Validate traffic flows through without issues
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating traffic flows through without issues')

        # Stop the low traffic load.
        if not self.traffic.stop():
            LOG.error('TC_VNFC_SCALE_OUT_005_2 execution failed')
            LOG.debug('Traffic could not be stopped')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Low traffic could not be stopped'
            return False

        # Configure stream destination MAC address(es).
        vnf_info = self.mano.vnf_query(filter={'vnf_instance_id': self.vnf_instance_id})
        dest_mac_addr_list = ''
        for ext_cp_info in vnf_info.instantiated_vnf_info.ext_cp_info:
            if ext_cp_info.cpd_id == self.tc_input['traffic_params']['traffic_config']['left_cp_name']:
                dest_mac_addr_list += ext_cp_info.address[0] + ' '

        self.traffic.config_traffic_stream(dest_mac_addr_list)
        self.traffic.clear_counters()

        # Start the low traffic load.
        if not self.traffic.start(return_when_emission_starts=True):
            LOG.error('TC_VNFC_SCALE_OUT_005_2 execution failed')
            LOG.debug('Traffic could not be started')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Low traffic could not be started'
            return False

        # Checking the traffic flow.
        if not self.traffic.does_traffic_flow(delay_time=5):
            LOG.error('TC_VNFC_SCALE_OUT_005_2 execution failed')
            LOG.debug('Traffic is not flowing')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Low traffic did not flow'
            return False

        if self.traffic.any_traffic_loss():
            LOG.error('TC_VNFC_SCALE_OUT_005_2 execution failed')
            LOG.debug('Traffic is flowing with packet loss')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Low traffic flew with packet loss'
            return False

        self.tc_result['scaling_in']['traffic_after'] = 'LOW_TRAFFIC_LOAD'

        LOG.info('TC_VNFC_SCALE_OUT_005_2 execution completed successfully')

        return True
