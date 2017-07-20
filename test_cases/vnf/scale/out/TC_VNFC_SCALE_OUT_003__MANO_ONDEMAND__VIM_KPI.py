import logging
import time

from api.generic import constants
from api.generic.mano import Mano
from api.generic.traffic import Traffic
from test_cases import TestCase, TestRunError
from utils.misc import generate_name

# Instantiate logger
LOG = logging.getLogger(__name__)


class TC_VNFC_SCALE_OUT_003__MANO_ONDEMAND__VIM_KPI(TestCase):
    """
    TC_VNFC_SCALE_OUT_003__MANO_ONDEMAND__VIM_KPI Scale-in VNFC instance with on-demand scaling event generated by MANO.
    The stimulus for scaling in is a VIM key performance indicator threshold crossing.

    Sequence:
    1. Instantiate the VNF
    2. Validate VNF instantiation state is INSTANTIATED and VNF state is STARTED
    3. Start the low traffic load
    4. Validate the provided functionality and all traffic goes through
    5. Trigger a resize of the VNF resources to the next level by altering the VNF indicators produced by the VNF
    6. Validate VNF has resized to the next level
    7. Determine if and length of service disruption
    8. Validate increased capacity without traffic loss
    9. Trigger the downsize of the VNF by altering the VIM KPI
    10. Validate VNF has released the resources and decreased the VNFCs
    11. Validate traffic drop occurred
    12. Validate traffic flows through without issues
    """

    required_elements = ('mano_params', 'traffic_params')

    def setup(self):
        LOG.info('Starting setup for TC_VNFC_SCALE_OUT_003__MANO_ONDEMAND__VIM_KPI')

        # Create objects needed by the test.
        self.mano = Mano(vendor=self.tc_input['mano_params']['type'], **self.tc_input['mano_params']['client_config'])
        self.traffic = Traffic(self.tc_input['traffic_params']['type'],
                               **self.tc_input['traffic_params']['client_config'])
        self.register_for_cleanup(self.traffic.destroy)

        # Initialize test case result.
        self.tc_result['events']['instantiate_vnf'] = dict()
        self.tc_result['events']['scale_out_vnf'] = dict()
        self.tc_result['events']['service_disruption'] = dict()
        self.tc_result['events']['scale_in_vnf'] = dict()

        LOG.info('Finished setup for TC_VNFC_SCALE_OUT_003__MANO_ONDEMAND__VIM_KPI')

    def run(self):
        LOG.info('Starting TC_VNFC_SCALE_OUT_003__MANO_ONDEMAND__VIM_KPI')

        # Get scaling policy properties
        sp = self.mano.get_vnfd_scaling_properties(self.tc_input['vnfd_id'], self.tc_input['scaling_policy_name'])

        # --------------------------------------------------------------------------------------------------------------
        # 1. Instantiate the VNF
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
        # 2. Validate VNF instantiation state is INSTANTIATED and VNF state is STARTED
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
        # 3. Start the low traffic load
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
        # 4. Validate the provided functionality and all traffic goes through
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
        # 5. Trigger a resize of the VNF resources to the next level by altering the VNF Indicators produced by the VNF
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Triggering a resize of the VNF resources to the next level by increasing the traffic load to the '
                 'maximum')

        # The scale out is triggered by a VIM KPI threshold crossing.
        # The Virtualised Resources Performance Management interface of Or-Vi will enable the MANO to trigger a scale
        # out based on VIM KPIs.
        # There are 2 ways for MANO to obtain KPI information:
        # - by polling the VIM periodically on the Or-Vi interface (by means of PM jobs)
        # - by subscribing for notifications related to performance information with the VIM. The MANO can define
        #   thresholds that generate notifications from the VIM when they are crossed.
        # Insert here code alters the VIM KPI so that MANO can trigger scale out.

        # TODO: Insert here code to:
        # 1. alter the VNF related indicators so that MANO can trigger a VNF scale out.
        # 2. check that MANO has subscribed to VIM
        # 3. subscribe to VIM and check the notifications
        # For now we use only traffic load to trigger scale out.
        self.traffic.config_traffic_load('MAX_TRAFFIC_LOAD')

        # --------------------------------------------------------------------------------------------------------------
        # 6. Validate VNF has resized to the next level
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating VNF has resized to the next level')
        # The scale out duration will include:
        # - the time it takes the VNF CPU load to increase (caused by the max traffic load)
        # - the time after which the scaling alarm is triggered
        # - the time it takes the VNF to scale out
        self.time_record.START('scale_out_vnf')
        elapsed_time = 0
        while elapsed_time < constants.SCALE_INTERVAL:
            vnf_info = self.mano.vnf_query(filter={'vnf_instance_id': self.vnf_instance_id})
            if len(vnf_info.instantiated_vnf_info.vnfc_resource_info) == sp['default_instances'] + sp['increment']:
                break
            else:
                time.sleep(constants.POLL_INTERVAL)
                elapsed_time += constants.POLL_INTERVAL
            if elapsed_time == constants.SCALE_INTERVAL:
                self.tc_result['scaling_out']['status'] = 'Fail'
                raise TestRunError('VNF has not resized to the next level')

        self.time_record.END('scale_out_vnf')

        self.tc_result['events']['scale_out_vnf']['duration'] = self.time_record.duration('scale_out_vnf')

        self.tc_result['resources']['After scale out'] = self.mano.get_allocated_vresources(self.vnf_instance_id)

        self.tc_result['scaling_out']['level'] = sp['default_instances'] + sp['increment']

        self.tc_result['scaling_out']['status'] = 'Success'

        # --------------------------------------------------------------------------------------------------------------
        # 7. Determine if and length of service disruption
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Determining if and length of service disruption')
        self.tc_result['events']['service_disruption']['duration'] = self.traffic.calculate_service_disruption_length()

        # --------------------------------------------------------------------------------------------------------------
        # 8. Validate increased capacity without traffic loss
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating increased capacity without traffic loss')
        # Because the VNF scaled out, we need to reconfigure traffic so that it passes through all VNFCs.

        # Stop the max traffic load.
        self.traffic.stop()

        # Configure stream destination MAC address(es).
        dest_mac_addr_list = ''
        for ext_cp_info in vnf_info.instantiated_vnf_info.ext_cp_info:
            if ext_cp_info.cpd_id == self.tc_input['traffic_params']['traffic_config']['left_cp_name']:
                dest_mac_addr_list += ext_cp_info.address[0] + ' '

        self.traffic.config_traffic_stream(dest_mac_addr_list)
        self.traffic.clear_counters()

        # Start the max traffic load.
        self.traffic.start(return_when_emission_starts=True)

        if not self.traffic.does_traffic_flow(delay_time=5):
            raise TestRunError('Traffic is not flowing', err_details='Max traffic did not flow')

        if self.traffic.any_traffic_loss(tolerance=constants.traffic_tolerance):
            raise TestRunError('Traffic is flowing with packet loss', err_details='Max traffic flew with packet loss')

        self.tc_result['scaling_out']['traffic_after'] = 'MAX_TRAFFIC_LOAD'
        self.tc_result['scaling_in']['traffic_before'] = 'MAX_TRAFFIC_LOAD'

        # --------------------------------------------------------------------------------------------------------------
        # 9. Trigger the downsize of the VNF by altering the VNF indicators produced by the VNF
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Triggering the downsize of the VNF by decreasing the traffic load to the minimum')

        # The scale in is triggered by a VIM KPI threshold crossing.
        # The Virtualised Resources Performance Management interface of Or-Vi will enable the MANO to trigger a scale
        # in based on VIM KPIs.
        # There are 2 ways for MANO to obtain KPI information:
        # - by polling the VIM periodically on the Or-Vi interface (by means of PM jobs)
        # - by subscribing for notifications related to performance information with the VIM. The MANO can define
        #   thresholds that generate notifications from the VIM when they are crossed.
        # Insert here code that alters the VIM KPI so that MANO can trigger scale out.

        # TODO: Insert here code to:
        # 1. alter the VNF related indicators so that MANO can trigger a VNF scale out.
        # 2. check that MANO has subscribed to VIM
        # 3. subscribe to VIM and check the notifications
        # For now we use only traffic load to trigger scale in.
        self.traffic.config_traffic_load('LOW_TRAFFIC_LOAD')

        # --------------------------------------------------------------------------------------------------------------
        # 10. Validate VNF has released the resources and decreased the VNFCs
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating VNF has released the resources and decreased the VNFCs')
        # The scale in duration will include:
        # - the time it takes the VNF CPU load to decrease (caused by the low traffic load)
        # - the time after which the scaling alarm is triggered
        # - the time it takes the VNF to scale in
        self.time_record.START('scale_in_vnf')
        elapsed_time = 0
        while elapsed_time < constants.SCALE_INTERVAL:
            vnf_info = self.mano.vnf_query(filter={'vnf_instance_id': self.vnf_instance_id})
            if len(vnf_info.instantiated_vnf_info.vnfc_resource_info) == sp['default_instances']:
                break
            else:
                time.sleep(constants.POLL_INTERVAL)
                elapsed_time += constants.POLL_INTERVAL
            if elapsed_time == constants.SCALE_INTERVAL:
                self.tc_result['scaling_in']['status'] = 'Fail'
                raise TestRunError('VNF has not decreased the VNFCs')

        self.time_record.END('scale_in_vnf')

        self.tc_result['events']['scale_in_vnf']['duration'] = self.time_record.duration('scale_in_vnf')

        self.tc_result['resources']['After scale in'] = self.mano.get_allocated_vresources(self.vnf_instance_id)

        self.tc_result['scaling_in']['level'] = sp['default_instances']

        self.tc_result['scaling_in']['status'] = 'Success'

        # --------------------------------------------------------------------------------------------------------------
        # 11. Validate traffic drop occurred
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating traffic drop occurred')
        if not self.traffic.any_traffic_loss():
            raise TestRunError('Max traffic flew without packet loss')

        # --------------------------------------------------------------------------------------------------------------
        # 12. Validate traffic flows through without issues
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating traffic flows through without issues')
        # Because the VNF scaled in, we need to reconfigure traffic so that it passes through the new VNFCs.

        # Stop the low traffic load.
        self.traffic.stop()

        # Configure stream destination MAC address(es).
        dest_mac_addr_list = ''
        for ext_cp_info in vnf_info.instantiated_vnf_info.ext_cp_info:
            if ext_cp_info.cpd_id == self.tc_input['traffic_params']['traffic_config']['left_cp_name']:
                dest_mac_addr_list += ext_cp_info.address[0] + ' '

        self.traffic.config_traffic_stream(dest_mac_addr_list)
        self.traffic.clear_counters()

        # Start the low traffic load.
        self.traffic.start(return_when_emission_starts=True)

        if not self.traffic.does_traffic_flow(delay_time=5):
            raise TestRunError('Traffic is not flowing', err_details='Low traffic did not flow')

        if self.traffic.any_traffic_loss(tolerance=constants.traffic_tolerance):
            raise TestRunError('Traffic is flowing with packet loss', err_details='Low traffic flew with packet loss')

        self.tc_result['scaling_in']['traffic_after'] = 'LOW_TRAFFIC_LOAD'

        LOG.info('TC_VNFC_SCALE_OUT_003__MANO_ONDEMAND__VIM_KPI execution completed successfully')
