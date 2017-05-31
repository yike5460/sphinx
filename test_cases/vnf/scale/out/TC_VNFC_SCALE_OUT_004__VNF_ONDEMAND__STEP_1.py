import logging

from api.generic import constants
from api.generic.mano import Mano
from api.generic.traffic import Traffic
from api.generic.vim import Vim
from api.structures.objects import VnfLifecycleChangeNotification
from test_cases import TestCase
from utils.misc import generate_name

# Instantiate logger
LOG = logging.getLogger(__name__)


class TC_VNFC_SCALE_OUT_004__VNF_ONDEMAND__STEP_1(TestCase):
    """
    TC_VNFC_SCALE_OUT_004__VNF_ONDEMAND__STEP_1 Max vResource VNFC limit reached before max VNFD limit for 
    scale-out with on-demand scaling event generated by the VNF. 
    Scaling step is set to max_instances.

    Sequence:
    1. Ensure NFVI has vResources so that the VNF can be scaled out only desired_scale_out_steps times
    2. Instantiate the VNF
    3. Validate VNF instantiation state is INSTANTIATED and VNF state is STARTED
    4. Start the low traffic load
    5. Validate the provided functionality and all traffic goes through
    6. Subscribe for VNF Lifecycle change notifications
    7. Trigger a resize of the VNF resources to the maximum increasing the traffic load to the maximum
    8. Verify that the scale out was triggered by the VNF
    9. Validate VNF scale out operation was performed desired_scale_out_steps times
    10. Validate VNF has resized to the max (limited by NFVI)
    11. Determine if and length of service disruption
    12. Validate traffic goes through
    """

    def setup(self):
        LOG.info('Starting setup for TC_VNFC_SCALE_OUT_004__VNF_ONDEMAND__STEP_1')

        # Create objects needed by the test.
        self.mano = Mano(vendor=self.tc_input['mano_params']['type'], **self.tc_input['mano_params']['client_config'])
        self.vim = Vim(vendor=self.tc_input['vim_params']['type'], **self.tc_input['vim_params']['client_config'])
        self.traffic = Traffic(self.tc_input['traffic_params']['type'],
                               **self.tc_input['traffic_params']['client_config'])
        self.register_for_cleanup(self.traffic.destroy)

        # Initialize test case result.
        self.tc_result['overall_status'] = constants.TEST_PASSED
        self.tc_result['error_info'] = 'No errors'
        self.tc_result['events']['instantiate_vnf'] = dict()
        self.tc_result['events']['scale_out_vnf'] = dict()
        self.tc_result['events']['service_disruption'] = dict()

        LOG.info('Finished setup for TC_VNFC_SCALE_OUT_004__VNF_ONDEMAND__STEP_1')

        return True

    def run(self):
        LOG.info('Starting TC_VNFC_SCALE_OUT_004__VNF_ONDEMAND__STEP_1')

        # --------------------------------------------------------------------------------------------------------------
        # 1. Ensure NFVI has vResources so that the VNF can be scaled out only desired_scale_out_steps times
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Ensuring NFVI has vResources so that the VNF can be scaled out only desired_scale_out_steps times')
        # Reserving only compute resources is enough for limiting the NFVI resources
        reservation_id = self.mano.limit_compute_resources_for_vnf_scaling(
                                                                          self.tc_input['vnfd_id'],
                                                                          self.tc_input['scaling_policy_name'],
                                                                          self.tc_input['desired_scale_out_steps'],
                                                                          self.vim)
        if reservation_id is None:
            LOG.error('TC_VNFC_SCALE_OUT_004__VNF_ONDEMAND__STEP_1 execution failed')
            LOG.debug('Compute resources could not be limited')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Compute resources could not be limited'
            return False

        self.register_for_cleanup(self.vim.terminate_compute_resource_reservation, reservation_id)

        # --------------------------------------------------------------------------------------------------------------
        # 2. Instantiate the VNF
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Instantiating the VNF')
        self.time_record.START('instantiate_vnf')
        self.vnf_instance_id = self.mano.vnf_create_and_instantiate(
                                                 vnfd_id=self.tc_input['vnfd_id'], flavour_id=None,
                                                 vnf_instance_name=generate_name(self.tc_input['vnf']['instance_name']),
                                                 vnf_instance_description=None)
        if self.vnf_instance_id is None:
            LOG.error('TC_VNFC_SCALE_OUT_004__VNF_ONDEMAND__STEP_1 execution failed')
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
            LOG.error('TC_VNFC_SCALE_OUT_004__VNF_ONDEMAND__STEP_1 execution failed')
            LOG.debug('Unexpected VNF instantiation state')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'VNF instantiation state was not "%s" after the VNF was instantiated' \
                                           % constants.VNF_INSTANTIATED
            return False

        LOG.info('Validating VNF state is STARTED')
        if vnf_info.instantiated_vnf_info.vnf_state != constants.VNF_STARTED:
            LOG.error('TC_VNFC_SCALE_OUT_004__VNF_ONDEMAND__STEP_1 execution failed')
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
            LOG.error('TC_VNFC_SCALE_OUT_004__VNF_ONDEMAND__STEP_1 execution failed')
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
            LOG.error('TC_VNFC_SCALE_OUT_004__VNF_ONDEMAND__STEP_1 execution failed')
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
            LOG.error('TC_VNFC_SCALE_OUT_004__VNF_ONDEMAND__STEP_1 execution failed')
            LOG.debug('Traffic is not flowing')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Low traffic did not flow'
            return False

        if self.traffic.any_traffic_loss():
            LOG.error('TC_VNFC_SCALE_OUT_004__VNF_ONDEMAND__STEP_1 execution failed')
            LOG.debug('Traffic is flowing with packet loss')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Low traffic flew with packet loss'
            return False

        self.tc_result['scaling_out']['traffic_before'] = 'LOW_TRAFFIC_LOAD'

        if not self.mano.validate_allocated_vresources(self.tc_input['vnfd_id'], self.vnf_instance_id):
            LOG.error('TC_VNFC_SCALE_OUT_004__VNF_ONDEMAND__STEP_1 execution failed')
            LOG.debug('Could not validate allocated vResources')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Could not validate allocated vResources'
            return False

        # --------------------------------------------------------------------------------------------------------------
        # 6. Subscribe for VNF Lifecycle change notifications
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Subscribing for VNF lifecycle change notifications')
        subscription_id = self.mano.vnf_lifecycle_change_notification_subscribe(
                                                          notification_filter={'vnf_instance_id': self.vnf_instance_id})

        # --------------------------------------------------------------------------------------------------------------
        # 7. Trigger a resize of the VNF resources to the maximum increasing the traffic load to the maximum
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Trigger a resize of the VNF resources to the maximum by increasing the traffic load to the maximum')
        self.traffic.config_traffic_load('MAX_TRAFFIC_LOAD')

        # --------------------------------------------------------------------------------------------------------------
        # 8. Verify that the scale out was triggered by the VNF
        # --------------------------------------------------------------------------------------------------------------

        # TODO: Insert code here to verify that the scale out was triggered by the EM

        # --------------------------------------------------------------------------------------------------------------
        # 9. Validate VNF scale out operation was performed desired_scale_out_steps times
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating VNF scale out operation was performed desired_scale_out_steps times')
        notification_queue = self.mano.get_notification_queue(subscription_id)

        self.time_record.START('scale_out_vnf')
        # We are scaling the VNF (desired_scale_out_steps + 1) times and check at the next step that the VNF scaled out
        # only desired_scale_out_steps times
        for scale_out_level in range(self.tc_input['desired_scale_out_steps'] + 1):
            notification_info = self.mano.search_in_notification_queue(
                                                                      notification_queue=notification_queue,
                                                                      notification_type=VnfLifecycleChangeNotification,
                                                                      notification_pattern={'status': 'STARTED',
                                                                                            'operation': 'VNF_SCALE.*'},
                                                                      timeout=constants.SCALE_INTERVAL)
            if notification_info is None:
                LOG.error('TC_VNFC_SCALE_OUT_004__VNF_ONDEMAND__STEP_1 execution failed')
                LOG.debug('Could not validate that scale out finished')
                self.tc_result['overall_status'] = constants.TEST_FAILED
                self.tc_result['error_info'] = 'Could not validate that scale out finished'
                return False
            notification_info = self.mano.search_in_notification_queue(
                                                                      notification_queue=notification_queue,
                                                                      notification_type=VnfLifecycleChangeNotification,
                                                                      notification_pattern={'status': 'SUCCESS|FAILED',
                                                                                            'operation': 'VNF_SCALE.*'},
                                                                      timeout=constants.SCALE_INTERVAL)
            if notification_info is None:
                LOG.error('TC_VNFC_SCALE_OUT_004__VNF_ONDEMAND__STEP_1 execution failed')
                LOG.debug('Could not validate that scale out finished')
                self.tc_result['overall_status'] = constants.TEST_FAILED
                self.tc_result['error_info'] = 'Could not validate that scale out finished'
                return False
        self.time_record.END('scale_out_vnf')

        self.tc_result['events']['scale_out_vnf']['duration'] = self.time_record.duration('scale_out_vnf')

        self.tc_result['resources']['After scale out'] = self.mano.get_allocated_vresources(self.vnf_instance_id)

        self.tc_result['scaling_out']['status'] = 'Success'

        # --------------------------------------------------------------------------------------------------------------
        # 10. Validate VNF has resized to the max (limited by NFVI)
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating VNF has resized to the max (limited by NFVI)')
        vnf_info = self.mano.vnf_query(filter={'vnf_instance_id': self.vnf_instance_id})
        if len(vnf_info.instantiated_vnf_info.vnfc_resource_info) != self.tc_input['scaling']['default_instances'] + \
                                                                     self.tc_input['scaling']['increment'] * \
                                                                     self.tc_input['desired_scale_out_steps']:
            LOG.error('TC_VNFC_SCALE_OUT_004__VNF_ONDEMAND__STEP_1 execution failed')
            LOG.debug('VNF scaled out')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'VNF scaled out'
            return False
        self.tc_result['scaling_out']['level'] = self.tc_input['scaling']['default_instances'] + \
                                                 self.tc_input['desired_scale_out_steps']

        # --------------------------------------------------------------------------------------------------------------
        # 11. Determine if and length of service disruption
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Determining if and length of service disruption')
        self.tc_result['events']['service_disruption']['duration'] = self.traffic.calculate_service_disruption_length()

        # --------------------------------------------------------------------------------------------------------------
        # 12. Validate traffic goes through
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating traffic goes through')
        # Since the VNF scaled out only desired_scale_out_steps, we are not checking the traffic loss because we do not
        # expect all traffic to go through.
        # Decreasing the traffic load to normal would not be appropriate as it could trigger a scale in.
        if not self.traffic.does_traffic_flow(delay_time=5):
            LOG.error('TC_VNFC_SCALE_OUT_004__VNF_ONDEMAND__STEP_1 execution failed')
            LOG.debug('Traffic is not flowing')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Max traffic did not flow'
            return False

        self.tc_result['scaling_out']['traffic_after'] = 'MAX_TRAFFIC_LOAD'

        LOG.info('TC_VNFC_SCALE_OUT_004__VNF_ONDEMAND__STEP_1 execution completed successfully')

        return True
