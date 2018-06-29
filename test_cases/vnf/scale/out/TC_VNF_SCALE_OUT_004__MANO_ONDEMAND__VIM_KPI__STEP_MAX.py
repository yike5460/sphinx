#
# Copyright (c) 2018 by Spirent Communications Plc.
# All Rights Reserved.
#
# This software is confidential and proprietary to Spirent Communications Inc.
# No part of this software may be reproduced, transmitted, disclosed or used
# in violation of the Software License Agreement without the expressed
# written consent of Spirent Communications Inc.
#
#


import logging

from api.generic import constants
from api.structures.objects import VnfLifecycleChangeNotification
from test_cases import TestCase, TestRunError
from utils.misc import generate_name

# Instantiate logger
LOG = logging.getLogger(__name__)


class TC_VNF_SCALE_OUT_004__MANO_ONDEMAND__VIM_KPI__STEP_MAX(TestCase):
    """
    TC_VNF_SCALE_OUT_004__MANO_ONDEMAND__VIM_KPI__STEP_MAX Max vResource VNF limit reached before max NSD limit for
    scale-out with manual scaling event generated by MANO and scaling step set to max_instances. The stimulus for
    scaling out is a VIM key performance indicator threshold crossing.

    Sequence:
    1. Ensure NFVI has not enough vResources for the NS to be scaled out
    2. Instantiate the NS
    3. Validate NS state is INSTANTIATED
    4. Validate VNF instantiation state is INSTANTIATED and VNF state is STARTED
    5. Start the low traffic load
    6. Validate the provided functionality and all traffic goes through
    7. Subscribe for VNF Lifecycle change notifications
    8. Trigger a resize of the NS resources to the maximum by altering a VIM KPI
    9. Validate that the scale out started and the operation finished
    10. Validate NS has not resized
    11. Determine if and length of service disruption
    12. Start the low traffic load
    13. Validate all traffic goes through
    14. Terminate the NS
    15. Validate that the NS is terminated and that all resources have been released by the VIM
    """

    REQUIRED_APIS = ('mano', 'vim', 'traffic')
    REQUIRED_ELEMENTS = ('nsd_id', 'scaling_policy_name')
    TESTCASE_EVENTS = ('instantiate_ns', 'scale_out_ns', 'service_disruption', 'terminate_ns')

    def run(self):
        LOG.info('Starting %s' % self.tc_name)

        # Get scaling policy properties
        sp = self.mano.get_nsd_scaling_properties(self.tc_input['nsd_id'], self.tc_input['scaling_policy_name'])

        # --------------------------------------------------------------------------------------------------------------
        # 1. Ensure NFVI has not enough vResources for the NS to be scaled out
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Ensure NFVI has not enough vResources for the NS to be scaled out')
        # Reserving only compute resources is enough for limiting the NFVI resources
        reservation_id = self.mano.limit_compute_resources_for_ns_scaling(
                                                               nsd_id=self.tc_input['nsd_id'],
                                                               scaling_policy_name=self.tc_input['scaling_policy_name'],
                                                               desired_scale_out_steps=0, generic_vim_object=self.vim)
        if reservation_id is None:
            raise TestRunError('Compute resources could not be limited')

        self.register_for_cleanup(index=10, function_reference=self.vim.terminate_compute_resource_reservation,
                                  reservation_id=reservation_id)

        # --------------------------------------------------------------------------------------------------------------
        # 2. Instantiate the NS
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Instantiating the NS')
        self.time_record.START('instantiate_ns')
        self.ns_instance_id = self.mano.ns_create_and_instantiate(
               nsd_id=self.tc_input['nsd_id'], ns_name=generate_name(self.tc_name),
               ns_description=self.tc_input.get('ns_description'), flavour_id=self.tc_input.get('flavour_id'),
               sap_data=self.tc_input['mano'].get('sap_data'), pnf_info=self.tc_input.get('pnf_info'),
               vnf_instance_data=self.tc_input.get('vnf_instance_data'),
               nested_ns_instance_data=self.tc_input.get('nested_ns_instance_data'),
               location_constraints=self.tc_input.get('location_constraints'),
               additional_param_for_ns=self.tc_input['mano'].get('instantiation_params_for_ns'),
               additional_param_for_vnf=self.tc_input['mano'].get('instantiation_params_for_vnf'),
               start_time=self.tc_input.get('start_time'),
               ns_instantiation_level_id=self.tc_input.get('ns_instantiation_level_id'),
               additional_affinity_or_anti_affinity_rule=self.tc_input.get('additional_affinity_or_anti_affinity_rule'))

        self.time_record.END('instantiate_ns')

        self.tc_result['events']['instantiate_ns']['duration'] = self.time_record.duration('instantiate_ns')

        self.register_for_cleanup(index=20, function_reference=self.mano.ns_terminate_and_delete,
                                  ns_instance_id=self.ns_instance_id,
                                  terminate_time=self.tc_input.get('terminate_time'),
                                  additional_param=self.tc_input['mano'].get('termination_params'))
        self.register_for_cleanup(index=30, function_reference=self.mano.wait_for_ns_stable_state,
                                  ns_instance_id=self.ns_instance_id)

        # --------------------------------------------------------------------------------------------------------------
        # 3. Validate NS state is INSTANTIATED
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating NS state is INSTANTIATED')
        ns_info = self.mano.ns_query(filter={'ns_instance_id': self.ns_instance_id})
        if ns_info.ns_state != constants.NS_INSTANTIATED:
            raise TestRunError('Unexpected NS state',
                               err_details='NS state was not "%s" after the NS was instantiated'
                                           % constants.NS_INSTANTIATED)

        # --------------------------------------------------------------------------------------------------------------
        # 4. Validate VNF instantiation state is INSTANTIATED and VNF state is STARTED
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating VNF instantiation state is INSTANTIATED')

        # Get the instance ID of the VNF inside the NS
        self.vnf_instance_id = ns_info.vnf_info_id[0]

        vnf_info = self.mano.vnf_query(query_filter={'vnf_instance_id': self.vnf_instance_id,
                                                     'additional_param': self.tc_input['mano'].get('query_params')})
        if vnf_info.instantiation_state != constants.VNF_INSTANTIATED:
            raise TestRunError('Unexpected VNF instantiation state',
                               err_details='VNF instantiation state was not "%s" after the VNF was instantiated'
                                           % constants.VNF_INSTANTIATED)

        LOG.info('Validating VNF state is STARTED')
        if vnf_info.instantiated_vnf_info.vnf_state != constants.VNF_STARTED:
            raise TestRunError('Unexpected VNF state',
                               err_details='VNF state was not "%s" after the VNF was instantiated'
                                           % constants.VNF_STARTED)

        self.tc_result['resources']['Initial'] = self.mano.get_allocated_vresources(
                                                                              self.vnf_instance_id,
                                                                              self.tc_input['mano'].get('query_params'))

        # --------------------------------------------------------------------------------------------------------------
        # 5. Start the low traffic load
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Starting the low traffic load')
        self.traffic.configure(traffic_load='LOW_TRAFFIC_LOAD',
                               traffic_config=self.tc_input['traffic']['traffic_config'])

        self.register_for_cleanup(index=40, function_reference=self.traffic.destroy)

        # Configure stream destination address(es)
        dest_addr_list = self.mano.get_vnf_ingress_cp_addr_list(
                                                          vnf_info,
                                                          self.tc_input['traffic']['traffic_config']['ingress_cp_name'])
        self.traffic.reconfig_traffic_dest(dest_addr_list)

        self.traffic.start(return_when_emission_starts=True)

        self.register_for_cleanup(index=50, function_reference=self.traffic.stop)

        # --------------------------------------------------------------------------------------------------------------
        # 6 Validate the provided functionality and all traffic goes through
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating the provided functionality and all traffic goes through')
        if not self.traffic.does_traffic_flow(delay_time=constants.TRAFFIC_DELAY_TIME):
            raise TestRunError('Traffic is not flowing', err_details='Low traffic did not flow')

        if self.traffic.any_traffic_loss(tolerance=constants.TRAFFIC_TOLERANCE):
            raise TestRunError('Traffic is flowing with packet loss', err_details='Low traffic flew with packet loss')

        self.tc_result['scaling_out']['traffic_before'] = 'LOW_TRAFFIC_LOAD'

        if not self.mano.validate_vnf_allocated_vresources(self.vnf_instance_id,
                                                           self.tc_input['mano'].get('query_params')):
            raise TestRunError('Allocated vResources could not be validated')

        # --------------------------------------------------------------------------------------------------------------
        # 7. Subscribe for VNF Lifecycle change notifications
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Subscribing for VNF lifecycle change notifications')
        subscription_id = self.mano.vnf_lifecycle_change_notification_subscribe(
                                                                       filter={'vnf_instance_id': self.vnf_instance_id})

        # --------------------------------------------------------------------------------------------------------------
        # 8. Trigger a resize of the NS resources to the maximum by altering a VIM KPI
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Triggering a resize of the NS resources to the maximum by altering a VIM KPI')

        # The scale out is triggered by a VIM KPI threshold crossing.
        # The Virtualised Resources Performance Management interface Or-Vi will enable the MANO to trigger a scale
        # out based on a VIM KPI.
        # There are 2 ways for MANO to obtain KPI information:
        # - by polling the VIM periodically on the Or-Vi interface (by means of a PM job)
        # - by subscribing for notifications related to performance information with the VIM. The MANO can define
        #   thresholds that generate notifications from the VIM when they are crossed.

        # TODO: Insert here code to:
        # 1. alter a VIM KPI so that MANO can trigger an NS scale out
        # 2. check that MANO has subscribed to VIM
        # 3. subscribe to VIM and check the notifications
        # For now we use only traffic load to trigger the scale out (we will increase the traffic load to the maximum).
        self.traffic.config_traffic_load('MAX_TRAFFIC_LOAD')

        # --------------------------------------------------------------------------------------------------------------
        # 9. Validate that the scaling out started and the operation finished
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating that the scale out started')
        notification_info = self.mano.wait_for_notification(subscription_id,
                                                            notification_type=VnfLifecycleChangeNotification,
                                                            notification_pattern={'status': 'STARTED',
                                                                                  'operation': 'NS_SCALE.*'},
                                                            timeout=120)
        if notification_info is None:
            raise TestRunError('Could not validate that NS scale out started')

        self.time_record.START('scale_out_ns')

        LOG.info('Validating that the scale out finished')
        notification_info = self.mano.wait_for_notification(subscription_id,
                                                            notification_type=VnfLifecycleChangeNotification,
                                                            notification_pattern={'status': 'SUCCESS|FAILED',
                                                                                  'operation': 'NS_SCALE.*'},
                                                            timeout=constants.NS_SCALE_TIMEOUT)
        if notification_info is None:
            raise TestRunError('Could not validate that NS scale out finished')

        self.time_record.END('scale_out_ns')

        self.tc_result['events']['scale_out_ns']['duration'] = self.time_record.duration('scale_out_ns')

        # --------------------------------------------------------------------------------------------------------------
        # 10. Validate NS has not resized
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating NS has not resized')
        ns_info = self.mano.ns_query(filter={'ns_instance_id': self.ns_instance_id})
        if len(ns_info.vnf_info_id) != sp['default_instances']:
            raise TestRunError('NS did not scale out to the max NFVI limit')

        self.tc_result['resources']['After scale out'] = {}
        for vnf_instance_id in ns_info.vnf_info_id:
            self.tc_result['resources']['After scale out'].update(
                self.mano.get_allocated_vresources(vnf_instance_id, self.tc_input['mano'].get('query_params')))

        self.tc_result['scaling_out']['level'] = sp['default_instances']

        self.tc_result['scaling_out']['status'] = notification_info.status

        # --------------------------------------------------------------------------------------------------------------
        # 11. Determine is and length of service disruption
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
        if not self.traffic.does_traffic_flow(delay_time=constants.TRAFFIC_DELAY_TIME):
            raise TestRunError('Traffic is not flowing', err_details='Low traffic did not flow')

        if self.traffic.any_traffic_loss(tolerance=constants.TRAFFIC_TOLERANCE):
            raise TestRunError('Traffic is flowing with packet loss', err_details='Low traffic flew with packet loss')

        self.tc_result['scaling_out']['traffic_after'] = 'LOW_TRAFFIC_LOAD'

        # --------------------------------------------------------------------------------------------------------------
        # 14. Terminate the NS
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Terminating the NS')
        self.time_record.START('terminate_ns')
        if self.mano.ns_terminate_sync(ns_instance_id=self.ns_instance_id,
                                       terminate_time=self.tc_input.get('terminate_time'),
                                       additional_param=self.tc_input['mano'].get('termination_params')) != \
                constants.OPERATION_SUCCESS:
            raise TestRunError('Unexpected status for NS termination operation',
                               err_details='NS termination operation failed')

        self.time_record.END('terminate_ns')

        self.tc_result['events']['terminate_ns']['duration'] = self.time_record.duration('terminate_ns')

        self.unregister_from_cleanup(index=30)
        self.unregister_from_cleanup(index=20)

        self.register_for_cleanup(index=20, function_reference=self.mano.ns_delete_id,
                                  ns_instance_id=self.ns_instance_id)

        # --------------------------------------------------------------------------------------------------------------
        # 15. Validate that the NS is terminated and that all resources have been released by the VIM
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating that the NS is terminated')
        ns_info_final = self.mano.ns_query(filter={'ns_instance_id': self.ns_instance_id,
                                                   'additional_param': self.tc_input['mano'].get('query_params')})
        if ns_info_final.ns_state != constants.NS_NOT_INSTANTIATED:
            raise TestRunError('Unexpected NS instantiation state',
                               err_details='NS instantiation state was not "%s" after the NS was terminated'
                                           % constants.NS_NOT_INSTANTIATED)

        LOG.info('Verifying that all the VNF instance(s) have been terminated')
        for vnf_info in ns_info.vnf_info:
            vnf_instance_id = vnf_info.vnf_instance_id
            vnf_info = self.mano.vnf_query(query_filter={'vnf_instance_id': vnf_instance_id,
                                                         'additional_param': self.tc_input['mano'].get('query_params')})
            if vnf_info.instantiation_state != constants.VNF_NOT_INSTANTIATED:
                raise TestRunError('VNF instance %s was not terminated correctly. Expected state was %s but got %s'
                                   % (vnf_instance_id, constants.VNF_NOT_INSTANTIATED, vnf_info.instantiation_state))

        LOG.info('Validating that all resources have been released by the VIM')
        if not self.mano.validate_ns_released_vresources(ns_info):
            raise TestRunError('Allocated resources have not been released by the VIM')

        LOG.info('%s execution completed successfully' % self.tc_name)
