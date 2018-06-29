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
from time import sleep

from api.generic import constants
from test_cases import TestCase, TestRunError
from utils.misc import generate_name

# Instantiate logger
LOG = logging.getLogger(__name__)


class TC_VNF_SCALE_OUT_005__MANO_ONDEMAND__VNF_IND(TestCase):
    """
    TC_VNF_SCALE_OUT_005__MANO_ONDEMAND__VNF_IND Removal of virtualized specialized hardware acceleration for VNF
    scale-in with on-demand scaling event generated by MANO. The stimulus for scaling out consists of value changes of
    one or multiple VNF related indicators on the interface produced by the VNF.

    Sequence:
    1. Instantiate the NS
    2. Validate NS state is INSTANTIATED
    3. Validate VNF instantiation state is INSTANTIATED and VNF state is STARTED
    4. Start the low traffic load
    5. Validate traffic flows through without issues
    6. Trigger a resize of the NS resources to use more specialized hardware by altering a VNF indicator
    7. Validate NS has resized
    8. Validate increased capacity without traffic loss
    9. Validate that MANO has allocated more specialized hardware resources
    10. Trigger a resize of the NS resources to use less specialized hardware by altering a VNF indicator
    11. Validate NS has resized and has decreased its capacity and removed VNFs
    12. Validate that MANO has allocated less specialized hardware resources and the previous specialized hardware
        resources have been freed up
    13. Determine the service disruption during the resizing
    14. Validate traffic flows through without issues
    15. Terminate the NS
    16. Validate that the NS is terminated and that all resources have been released by the VIM
    """

    REQUIRED_APIS = ('mano', 'traffic')
    REQUIRED_ELEMENTS = ('nsd_id', 'scaling_policy_name')
    TESTCASE_EVENTS = ('instantiate_ns', 'scale_out_ns', 'service_disruption', 'scale_in_ns', 'terminate_ns')

    def run(self):
        LOG.info('Starting %s' % self.tc_name)
        # TODO: Check the VNFD to see if hardware acceleration is present. This check will be added after we create an
        # internal representation for the VNFD.

        # Get scaling policy properties
        sp = self.mano.get_nsd_scaling_properties(self.tc_input['nsd_id'], self.tc_input['scaling_policy_name'])

        # --------------------------------------------------------------------------------------------------------------
        # 1. Instantiate the NS
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

        self.register_for_cleanup(index=10, function_reference=self.mano.ns_terminate_and_delete,
                                  ns_instance_id=self.ns_instance_id,
                                  terminate_time=self.tc_input.get('terminate_time'),
                                  additional_param=self.tc_input['mano'].get('termination_params'))
        self.register_for_cleanup(index=20, function_reference=self.mano.wait_for_ns_stable_state,
                                  ns_instance_id=self.ns_instance_id)

        # --------------------------------------------------------------------------------------------------------------
        # 2. Validate NS state is INSTANTIATED
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating NS state is INSTANTIATED')
        ns_info = self.mano.ns_query(filter={'ns_instance_id': self.ns_instance_id})
        if ns_info.ns_state != constants.NS_INSTANTIATED:
            raise TestRunError('Unexpected NS state',
                               err_details='NS state was not "%s" after the NS was instantiated'
                                           % constants.NS_INSTANTIATED)

        # --------------------------------------------------------------------------------------------------------------
        # 3. Validate VNF instantiation state is INSTANTIATED and VNF state is STARTED
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
        # 4. Start the low traffic load
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Starting the low traffic load')
        self.traffic.configure(traffic_load='LOW_TRAFFIC_LOAD',
                               traffic_config=self.tc_input['traffic']['traffic_config'])

        self.register_for_cleanup(index=30, function_reference=self.traffic.destroy)

        # Configure stream destination address(es)
        dest_addr_list = self.mano.get_vnf_ingress_cp_addr_list(
                                                          vnf_info,
                                                          self.tc_input['traffic']['traffic_config']['ingress_cp_name'])
        self.traffic.reconfig_traffic_dest(dest_addr_list)

        self.traffic.start(return_when_emission_starts=True)

        self.register_for_cleanup(index=40, function_reference=self.traffic.stop)

        # --------------------------------------------------------------------------------------------------------------
        # 5. Validate traffic flows through without issues
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating traffic flows through without issues')
        if not self.traffic.does_traffic_flow(delay_time=constants.TRAFFIC_DELAY_TIME):
            raise TestRunError('Traffic is not flowing', err_details='Low traffic did not flow')

        if self.traffic.any_traffic_loss(tolerance=constants.TRAFFIC_TOLERANCE):
            raise TestRunError('Traffic is flowing with packet loss', err_details='Low traffic flew with packet loss')

        if not self.mano.validate_vnf_allocated_vresources(self.vnf_instance_id,
                                                           self.tc_input['mano'].get('query_params')):
            raise TestRunError('Allocated vResources could not be validated')

        self.tc_result['scaling_out']['traffic_before'] = 'LOW_TRAFFIC_LOAD'

        # --------------------------------------------------------------------------------------------------------------
        # 6. Trigger a resize of the NS resources to use more specialized hardware by altering a VNF indicator
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Triggering a resize of the NS resources to use more specialized hardware by altering a VNF indicator')

        # The scale out is triggered by a VNF related indicator value change.
        # The VNF exposed interface Ve-Vnfm-Vnf will enable the MANO to trigger a scale out based on VNF Indicator
        # value changes. VNF related indicators are declared in the VNFD.
        # There are 2 ways for MANO to obtain VNF Indicator information:
        # - by GetIndicatorValue operation on the Ve-Vnfm-Vnf interface
        # - by subscribing for notifications related to VNF Indicator value changes with the VNF.
        # The two operations involved are Subscribe and Notify

        # TODO: Insert here code to:
        # 1. alter the VNF related indicators so that MANO can trigger an NS scale out
        # 2. check that MANO has subscribed to VNF
        # 3. subscribe to VNF and check the notifications
        # For now we use only traffic load to trigger the scale out (we will increase the traffic load to the maximum).
        self.traffic.config_traffic_load('MAX_TRAFFIC_LOAD')

        # --------------------------------------------------------------------------------------------------------------
        # 7. Validate NS has resized
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating NS has resized')
        # The scale out duration will include:
        # - the time it takes the VNF CPU load to increase (caused by the max traffic load)
        # - the time after which the scaling alarm is triggered
        # - the time it takes the NS to scale out
        self.time_record.START('scale_out_ns')
        elapsed_time = 0
        while elapsed_time < constants.NS_SCALE_TIMEOUT:
            ns_info = self.mano.ns_query(filter={'ns_instance_id': self.ns_instance_id})
            if len(ns_info.vnf_info_id) == sp['default_instances'] + sp['increment']:
                break
            else:
                sleep(constants.POLL_INTERVAL)
                elapsed_time += constants.POLL_INTERVAL
            if elapsed_time == constants.NS_SCALE_TIMEOUT:
                self.tc_result['scaling_out']['status'] = 'Fail'
                raise TestRunError('VNFs not added after traffic load was increased to the maximum')

        self.time_record.END('scale_out_ns')

        self.tc_result['events']['scale_out_ns']['duration'] = self.time_record.duration('scale_out_ns')

        self.tc_result['resources']['After scale out'] = {}
        for vnf_instance_id in ns_info.vnf_info_id:
            self.tc_result['resources']['After scale out'].update(
                self.mano.get_allocated_vresources(vnf_instance_id, self.tc_input['mano'].get('query_params')))

        self.tc_result['scaling_out']['level'] = sp['default_instances'] + sp['increment']

        self.tc_result['scaling_out']['status'] = 'Success'

        # --------------------------------------------------------------------------------------------------------------
        # 8. Validate increased capacity without traffic loss
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating increased capacity without traffic loss')
        # Because the NS scaled out, we need to reconfigure traffic so that it passes through all VNFs.

        # Stop the max traffic load.
        self.traffic.stop()

        # Configure stream destination address(es).
        dest_addr_list = ''
        for vnf_instance_id in ns_info.vnf_info_id:
            vnf_info = self.mano.vnf_query(query_filter={'vnf_instance_id': vnf_instance_id,
                                                         'additional_param': self.tc_input['mano'].get('query_params')})
            for ext_cp_info in vnf_info.instantiated_vnf_info.ext_cp_info:
                if ext_cp_info.cpd_id == self.tc_input['traffic']['traffic_config']['ingress_cp_name']:
                    dest_addr_list += ext_cp_info.address[0] + ' '

        self.traffic.reconfig_traffic_dest(dest_addr_list)
        self.traffic.clear_counters()

        # Start the max traffic load.
        self.traffic.start(return_when_emission_starts=True)

        if not self.traffic.does_traffic_flow(delay_time=constants.TRAFFIC_DELAY_TIME):
            raise TestRunError('Traffic is not flowing', err_details='Max traffic did not flow')

        if self.traffic.any_traffic_loss(tolerance=constants.TRAFFIC_TOLERANCE):
            raise TestRunError('Traffic is flowing with packet loss', err_details='Max traffic flew with packet loss')

        self.tc_result['scaling_out']['traffic_after'] = 'MAX_TRAFFIC_LOAD'
        self.tc_result['scaling_in']['traffic_before'] = 'MAX_TRAFFIC_LOAD'

        # --------------------------------------------------------------------------------------------------------------
        # 9. Validate that MANO has allocated more specialized hardware resources
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validate that MANO has allocated more specialized hardware resources')
        for vnf_instance_id in ns_info.vnf_info_id:
            if not self.mano.validate_vnf_allocated_vresources(vnf_instance_id,
                                                               self.tc_input['mano'].get('query_params')):
                raise TestRunError('Allocated vResources could not be validated',
                                   err_details='Allocated vResources could not be validated for VNF with ID %s'
                                               % vnf_instance_id)

        # --------------------------------------------------------------------------------------------------------------
        # 10. Trigger a resize of the NS resources to use less specialized hardware by altering a VNF indicator
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Triggering a resize of the NS resources to use less specialized hardware by altering a VNF indicator')

        # The scale in is triggered by a VNF related indicator value change.
        # The VNF exposed interface Ve-Vnfm-Vnf will enable the MANO to trigger a scale out based on VNF Indicator
        # value changes. VNF related indicators are declared in the VNFD.
        # There are 2 ways for MANO to obtain VNF Indicator information:
        # - by GetIndicatorValue operation on the Ve-Vnfm-Vnf interface
        # - by subscribing for notifications related to VNF Indicator value changes with the VNF.
        # The two operations involved are Subscribe and Notify.

        # TODO: Insert here code to:
        # 1. alter the VNF related indicators so that MANO can trigger an NS scale in
        # 2. check that MANO has subscribed to VNF
        # 3. subscribe to VNF and check the notifications
        # For now we use only traffic load to trigger the scale out (we will decrease the traffic load to the minimum).
        self.traffic.config_traffic_load('LOW_TRAFFIC_LOAD')

        # --------------------------------------------------------------------------------------------------------------
        # 11. Validate NS has resized and has decreased its capacity and removed VNFs
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating NS has resized and has decreased its capacity and removed VNFs')
        # The scale in duration will include:
        # - the time it takes the VNF CPU load to decrease (caused by the low traffic load)
        # - the time after which the scaling alarm is triggered
        # - the time it takes the NS to scale in
        self.time_record.START('scale_in_ns')
        elapsed_time = 0
        while elapsed_time < constants.NS_SCALE_TIMEOUT:
            ns_info = self.mano.ns_query(filter={'ns_instance_id': self.ns_instance_id})
            if len(ns_info.vnf_info_id) == sp['default_instances']:
                break
            else:
                sleep(constants.POLL_INTERVAL)
                elapsed_time += constants.POLL_INTERVAL
            if elapsed_time == constants.NS_SCALE_TIMEOUT:
                self.tc_result['scaling_in']['status'] = 'Fail'
                raise TestRunError('NS did not scale in')

        self.time_record.END('scale_in_ns')

        self.tc_result['events']['scale_in_ns']['duration'] = self.time_record.duration('scale_in_ns')

        self.vnf_instance_id = ns_info.vnf_info_id[0]
        self.tc_result['resources']['After scale in'] = self.mano.get_allocated_vresources(
                                                                              self.vnf_instance_id,
                                                                              self.tc_input['mano'].get('query_params'))

        self.tc_result['scaling_in']['level'] = sp['default_instances']

        self.tc_result['scaling_in']['status'] = 'Success'

        # --------------------------------------------------------------------------------------------------------------
        # 12. Validate that MANO has allocated less specialized hardware resources and the previous specialized hardware
        #     resources have been freed up
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validate that MANO has allocated less specialized hardware resources and the previous specialized '
                 'hardware resources have been freed up')
        if not self.mano.validate_vnf_allocated_vresources(self.vnf_instance_id,
                                                           self.tc_input['mano'].get('query_params')):
            raise TestRunError('Allocated vResources could not be validated')

        # --------------------------------------------------------------------------------------------------------------
        # 13. Determine the service disruption during the resizing
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Determining the service disruption during the resizing')
        self.tc_result['events']['service_disruption']['duration'] = self.traffic.calculate_service_disruption_length()

        # --------------------------------------------------------------------------------------------------------------
        # 14. Validate traffic flows through without issues
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating traffic flows through without issues')

        # Stop the low traffic load.
        self.traffic.stop()

        # Configure stream destination address(es).
        dest_addr_list = ''
        vnf_info = self.mano.vnf_query(query_filter={'vnf_instance_id': self.vnf_instance_id,
                                                     'additional_param': self.tc_input['mano'].get('query_params')})
        for ext_cp_info in vnf_info.instantiated_vnf_info.ext_cp_info:
            if ext_cp_info.cpd_id == self.tc_input['traffic']['traffic_config']['ingress_cp_name']:
                dest_addr_list += ext_cp_info.address[0] + ' '

        self.traffic.reconfig_traffic_dest(dest_addr_list)
        self.traffic.clear_counters()

        # Start the low traffic load.
        self.traffic.start(return_when_emission_starts=True)

        # Checking the traffic flow.
        if not self.traffic.does_traffic_flow(delay_time=constants.TRAFFIC_DELAY_TIME):
            raise TestRunError('Traffic is not flowing', err_details='Low traffic did not flow')

        if self.traffic.any_traffic_loss(tolerance=constants.TRAFFIC_TOLERANCE):
            raise TestRunError('Traffic is flowing with packet loss', err_details='Low traffic flew with packet loss')

        self.tc_result['scaling_in']['traffic_after'] = 'LOW_TRAFFIC_LOAD'

        # --------------------------------------------------------------------------------------------------------------
        # 15. Terminate the NS
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

        self.unregister_from_cleanup(index=20)
        self.unregister_from_cleanup(index=10)

        self.register_for_cleanup(index=10, function_reference=self.mano.ns_delete_id,
                                  ns_instance_id=self.ns_instance_id)

        # --------------------------------------------------------------------------------------------------------------
        # 16. Validate that the NS is terminated and that all resources have been released by the VIM
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
