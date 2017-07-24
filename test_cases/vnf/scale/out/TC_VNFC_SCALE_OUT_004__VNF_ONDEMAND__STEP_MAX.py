import logging

from api.generic import constants
from api.generic.mano import Mano
from api.generic.traffic import Traffic
from api.generic.vim import Vim
from api.structures.objects import VnfLifecycleChangeNotification
from test_cases import TestCase, TestRunError
from utils.misc import generate_name

# Instantiate logger
LOG = logging.getLogger(__name__)


class TC_VNFC_SCALE_OUT_004__VNF_ONDEMAND__STEP_MAX(TestCase):
    """
    TC_VNFC_SCALE_OUT_004__VNF_ONDEMAND__STEP_MAX Max vResource VNFC limit reached before max VNFD limit for
    scale-out with on-demand scaling event generated by MANO and triggered by a VNF Indicator produced by the EM.
    Scaling step is set to max_instances.

    Sequence:
    1. Ensure NFVI has not enough vResources for the VNF to be scaled out
    2. Instantiate the VNF
    3. Validate VNF instantiation state is INSTANTIATED and VNF state is STARTED
    4. Start the low traffic load
    5. Validate the provided functionality and all traffic goes through
    6. Subscribe for VNF Lifecycle change notifications
    7. Trigger a resize of the VNF resources to the maximum by increasing the traffic load to the maximum
    8. Verify that the scale out was triggered by the VNF
    9. Validate that the scaling out has been attempted and the operation finished
    10. Validate that VNF has not resized
    11. Determine if and length of service disruption
    12. Start the low traffic load
    13. Validate all traffic goes through
    """

    required_elements = ('mano_params', 'vim_params', 'traffic_params', 'vnfd_id')

    def setup(self):
        LOG.info('Starting setup for TC_VNFC_SCALE_OUT_004__VNF_ONDEMAND__STEP_MAX')

        # Create objects needed by the test.
        self.mano = Mano(vendor=self.tc_input['mano_params']['type'], **self.tc_input['mano_params']['client_config'])
        self.vim = Vim(vendor=self.tc_input['vim_params']['type'], **self.tc_input['vim_params']['client_config'])
        self.traffic = Traffic(self.tc_input['traffic_params']['type'],
                               **self.tc_input['traffic_params']['client_config'])
        self.register_for_cleanup(self.traffic.destroy)

        # Initialize test case result.
        self.tc_result['events']['instantiate_vnf'] = dict()
        self.tc_result['events']['scale_out_vnf'] = dict()
        self.tc_result['events']['service_disruption'] = dict()

        LOG.info('Finished setup for TC_VNFC_SCALE_OUT_004__VNF_ONDEMAND__STEP_MAX')

    def run(self):
        LOG.info('Starting TC_VNFC_SCALE_OUT_004__VNF_ONDEMAND__STEP_MAX')

        # Get scaling policy properties
        sp = self.mano.get_vnfd_scaling_properties(self.tc_input['vnfd_id'], self.tc_input['scaling_policy_name'])

        # --------------------------------------------------------------------------------------------------------------
        # 1. Ensure NFVI has not enough vResources for the VNF to be scaled out
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Ensure NFVI has not enough vResources for the VNF to be scaled out')
        # Reserving only compute resources is enough for limiting the NFVI resources
        reservation_id = self.mano.limit_compute_resources_for_vnf_scaling(
                             vnfd_id=self.tc_input['vnfd_id'], scaling_policy_name=self.tc_input['scaling_policy_name'],
                             desired_scale_out_steps=0, generic_vim_object=self.vim)
        if reservation_id is None:
            raise TestRunError('Compute resources could not be limited')

        self.register_for_cleanup(self.vim.terminate_compute_resource_reservation, reservation_id)

        # --------------------------------------------------------------------------------------------------------------
        # 2. Instantiate the VNF
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Instantiating the VNF')
        self.time_record.START('instantiate_vnf')
        self.vnf_instance_id = self.mano.vnf_create_and_instantiate(
                                          vnfd_id=self.tc_input['vnfd_id'], flavour_id=None,
                                          vnf_instance_name=generate_name(self.tc_input['vnf_params']['instance_name']),
                                          vnf_instance_description=None)

        self.time_record.END('instantiate_vnf')

        self.tc_result['events']['instantiate_vnf']['duration'] = self.time_record.duration('instantiate_vnf')

        self.register_for_cleanup(self.mano.vnf_terminate_and_delete, vnf_instance_id=self.vnf_instance_id,
                                  termination_type='graceful')
        self.register_for_cleanup(self.mano.wait_for_vnf_stable_state, vnf_instance_id=self.vnf_instance_id)

        # --------------------------------------------------------------------------------------------------------------
        # 3. Validate VNF instantiation state is INSTANTIATED and VNF state is STARTED
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating VNF instantiation state is INSTANTIATED')
        vnf_info = self.mano.vnf_query(filter={'vnf_instance_id': self.vnf_instance_id})
        if vnf_info.instantiation_state != constants.VNF_INSTANTIATED:
            raise TestRunError('Unexpected VNF instantiation state',
                               err_details='VNF instantiation state was not "%s" after the VNF was instantiated'
                                           % constants.VNF_INSTANTIATED)

        LOG.info('Validating VNF state is STARTED')
        if vnf_info.instantiated_vnf_info.vnf_state != constants.VNF_STARTED:
            raise TestRunError('Unexpected VNF state',
                               err_details='VNF state was not "%s" after the VNF was instantiated'
                                           % constants.VNF_STARTED)

        self.tc_result['resources']['Initial'] = self.mano.get_allocated_vresources(self.vnf_instance_id)

        # --------------------------------------------------------------------------------------------------------------
        # 4. Start the low traffic load
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Starting the low traffic load')
        self.traffic.configure(traffic_load='LOW_TRAFFIC_LOAD',
                               traffic_config=self.tc_input['traffic_params']['traffic_config'])

        # Configure stream destination MAC address(es)
        dest_mac_addr_list = ''
        for ext_cp_info in vnf_info.instantiated_vnf_info.ext_cp_info:
            if ext_cp_info.cpd_id == self.tc_input['traffic_params']['traffic_config']['left_cp_name']:
                dest_mac_addr_list += ext_cp_info.address[0] + ' '
        self.traffic.config_traffic_stream(dest_mac_addr_list)

        self.traffic.start(return_when_emission_starts=True)

        self.register_for_cleanup(self.traffic.stop)

        # --------------------------------------------------------------------------------------------------------------
        # 5. Validate the provided functionality and all traffic goes through
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating the provided functionality and all traffic goes through')
        if not self.traffic.does_traffic_flow(delay_time=5):
            raise TestRunError('Traffic is not flowing', err_details='Low traffic did not flow')

        if self.traffic.any_traffic_loss(tolerance=constants.traffic_tolerance):
            raise TestRunError('Traffic is flowing with packet loss', err_details='Low traffic flew with packet loss')

        self.tc_result['scaling_out']['traffic_before'] = 'LOW_TRAFFIC_LOAD'

        if not self.mano.validate_allocated_vresources(self.tc_input['vnfd_id'], self.vnf_instance_id):
            raise TestRunError('Allocated vResources could not be validated')

        # --------------------------------------------------------------------------------------------------------------
        # 6. Subscribe for VNF Lifecycle change notifications
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Subscribing for VNF lifecycle change notifications')
        subscription_id = self.mano.vnf_lifecycle_change_notification_subscribe(
            notification_filter={'vnf_instance_id': self.vnf_instance_id})

        # --------------------------------------------------------------------------------------------------------------
        # 7. Trigger a resize of the VNF resources to the maximum by increasing the traffic load to the maximum
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Trigger a resize of the VNF resources to the maximum by altering the VNF indicator produced by EM')
        self.traffic.config_traffic_load('MAX_TRAFFIC_LOAD')

        # --------------------------------------------------------------------------------------------------------------
        # 8. Verify that the scale out was triggered by the VNF
        # --------------------------------------------------------------------------------------------------------------

        # TODO: Insert code here to verify that the scale out was triggered by the EM

        # --------------------------------------------------------------------------------------------------------------
        # 9. Validate that the scaling out has been attempted and the operation finished
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating that the scaling out has been attempted')
        notification_info = self.mano.wait_for_notification(subscription_id,
                                                            notification_type=VnfLifecycleChangeNotification,
                                                            notification_pattern={'status': 'STARTED',
                                                                                  'operation': 'VNF_SCALE.*'},
                                                            timeout=120)
        if notification_info is None:
            raise TestRunError('Could not validate that VNF scale out has been attempted')

        self.time_record.START('scale_out_vnf')

        LOG.info('Validating that the scaling out finished')
        notification_info = self.mano.wait_for_notification(subscription_id,
                                                            notification_type=VnfLifecycleChangeNotification,
                                                            notification_pattern={'status': 'SUCCESS|FAILED',
                                                                                  'operation': 'VNF_SCALE.*'},
                                                            timeout=constants.SCALE_INTERVAL)
        if notification_info is None:
            raise TestRunError('Could not validate that VNF scale out finished')

        self.time_record.END('scale_out_vnf')

        self.tc_result['events']['scale_out_vnf']['duration'] = self.time_record.duration('scale_out_vnf')

        # --------------------------------------------------------------------------------------------------------------
        # 10. Validate VNF has not resized
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating VNF has not resized')
        vnf_info = self.mano.vnf_query(filter={'vnf_instance_id': self.vnf_instance_id})
        if len(vnf_info.instantiated_vnf_info.vnfc_resource_info) != sp['default_instances']:
            raise TestRunError('VNF scaled out')

        self.tc_result['resources']['After scale out'] = self.mano.get_allocated_vresources(self.vnf_instance_id)

        self.tc_result['scaling_out']['level'] = sp['default_instances']

        self.tc_result['scaling_out']['status'] = notification_info.status

        # --------------------------------------------------------------------------------------------------------------
        # 11. Determine if and length of service disruption
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Determining if and length of service disruption')
        self.tc_result['events']['service_disruption']['duration'] = self.traffic.calculate_service_disruption_length()

        # --------------------------------------------------------------------------------------------------------------
        # 12. Start the low traffic load
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Starting the low traffic load')

        # Stop the max traffic load.
        self.traffic.stop()

        # Configure the traffic load and clear counters.
        self.traffic.config_traffic_load('LOW_TRAFFIC_LOAD')
        self.traffic.clear_counters()

        # Start the low traffic load.
        self.traffic.start(return_when_emission_starts=True)

        # --------------------------------------------------------------------------------------------------------------
        # 13. Validate all traffic goes through
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating all traffic goes through')
        if not self.traffic.does_traffic_flow(delay_time=5):
            raise TestRunError('Traffic is not flowing', err_details='Low traffic did not flow')

        if self.traffic.any_traffic_loss(tolerance=constants.traffic_tolerance):
            raise TestRunError('Traffic is flowing with packet loss', err_details='Low traffic flew with packet loss')

        self.tc_result['scaling_out']['traffic_after'] = 'LOW_TRAFFIC_LOAD'

        LOG.info('TC_VNFC_SCALE_OUT_004__VNF_ONDEMAND__STEP_MAX execution completed successfully')
