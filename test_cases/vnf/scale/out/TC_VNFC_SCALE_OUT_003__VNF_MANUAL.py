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
from test_cases import TestCase, TestRunError
from utils.misc import generate_name

# Instantiate logger
LOG = logging.getLogger(__name__)


class TC_VNFC_SCALE_OUT_003__VNF_MANUAL(TestCase):
    """
    TC_VNFC_SCALE_OUT_003__VNF_MANUAL Scale-in VNFC instance with manual scaling event generated by VNF

    Sequence:
    1. Instantiate the VNF
    2. Validate VNF instantiation state is INSTANTIATED and VNF state is STARTED
    3. Start the low traffic load
    4. Validate the provided functionality and all traffic goes through
    5. Trigger a resize of the VNF resources to the next level by instructing the VNF to instruct the MANO to scale out
       the VNF
    6. Validate VNF has resized to the next level
    7. Determine if and length of service disruption
    8. Start the normal traffic load
    9. Validate increased capacity without traffic loss
    10. Trigger the downsize of the VNF by instructing the VNF to instruct the MANO to scale in the VNF
    11. Validate VNF has released the resources and decreased the VNFCs
    12. Validate traffic drop occurred
    13. Reduce traffic load to level that the downsized VNF should process
    14. Validate traffic flows through without issues
    15. Terminate the VNF
    16. Validate that the VNF is terminated and that all resources have been released by the VIM
    """

    REQUIRED_APIS = ('mano', 'vnf', 'traffic')
    REQUIRED_ELEMENTS = ('vnfd_id', 'scaling_policy_name')
    TESTCASE_EVENTS = ('instantiate_vnf', 'scale_out_vnf', 'service_disruption', 'scale_in_vnf', 'terminate_vnf')

    def run(self):
        LOG.info('Starting %s' % self.tc_name)

        # Get scaling policy properties
        sp = self.mano.get_vnfd_scaling_properties(self.tc_input['vnfd_id'], self.tc_input['scaling_policy_name'])

        # --------------------------------------------------------------------------------------------------------------
        # 1. Instantiate the VNF
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Instantiating the VNF')
        self.time_record.START('instantiate_vnf')
        self.vnf_instance_id = self.mano.vnf_create_and_instantiate(
                                                 vnfd_id=self.tc_input['vnfd_id'],
                                                 flavour_id=self.tc_input.get('flavour_id'),
                                                 vnf_instance_name=generate_name(self.tc_name),
                                                 vnf_instance_description=self.tc_input.get('vnf_instance_description'),
                                                 instantiation_level_id=self.tc_input.get('instantiation_level_id'),
                                                 ext_virtual_link=self.tc_input.get('ext_virtual_link'),
                                                 ext_managed_virtual_link=self.tc_input.get('ext_managed_virtual_link'),
                                                 localization_language=self.tc_input.get('localization_language'),
                                                 additional_param=self.tc_input['mano'].get('instantiation_params'))

        self.time_record.END('instantiate_vnf')

        self.tc_result['events']['instantiate_vnf']['duration'] = self.time_record.duration('instantiate_vnf')

        self.register_for_cleanup(index=10, function_reference=self.mano.vnf_terminate_and_delete,
                                  vnf_instance_id=self.vnf_instance_id, termination_type='graceful',
                                  graceful_termination_timeout=self.tc_input.get('graceful_termination_timeout'),
                                  additional_param=self.tc_input['mano'].get('termination_params'))
        self.register_for_cleanup(index=20, function_reference=self.mano.wait_for_vnf_stable_state,
                                  vnf_instance_id=self.vnf_instance_id)

        # --------------------------------------------------------------------------------------------------------------
        # 2. Validate VNF instantiation state is INSTANTIATED and VNF state is STARTED
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating VNF instantiation state is INSTANTIATED')
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
        # 3. Start the low traffic load
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
        # 4. Validate the provided functionality and all traffic goes through
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
        # 5. Trigger a resize of the VNF resources to the next level by instructing the VNF to instruct the MANO to
        #    scale out the VNF
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Triggering a resize of the VNF resources to the next level by instructing the VNF to instruct the '
                 'MANO to scale out the VNF')
        self.time_record.START('scale_out_vnf')
        if self.vnf.scale_sync(self.vnf_instance_id, scale_type='out', aspect_id=sp['targets'],
                               additional_param={'scaling_policy_name': self.tc_input['scaling_policy_name']}) \
                != constants.OPERATION_SUCCESS:
            self.tc_result['scaling_out']['status'] = 'Fail'
            raise TestRunError('VNF could not instruct the MANO to scale out the VNF')

        self.time_record.END('scale_out_vnf')

        self.tc_result['events']['scale_out_vnf']['duration'] = self.time_record.duration('scale_out_vnf')

        # --------------------------------------------------------------------------------------------------------------
        # 6. Validate VNF has resized to the next level
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating VNF has resized to the next level')
        vnf_info = self.mano.vnf_query(query_filter={'vnf_instance_id': self.vnf_instance_id,
                                                     'additional_param': self.tc_input['mano'].get('query_params')})
        if len(vnf_info.instantiated_vnf_info.vnfc_resource_info) != sp['default_instances'] + sp['increment']:
            raise TestRunError('VNF did not scale out to the next level')

        self.tc_result['resources']['After scale out'] = self.mano.get_allocated_vresources(
                                                                              self.vnf_instance_id,
                                                                              self.tc_input['mano'].get('query_params'))

        self.tc_result['scaling_out']['status'] = 'Success'

        self.tc_result['scaling_out']['level'] = sp['default_instances'] + sp['increment']

        # --------------------------------------------------------------------------------------------------------------
        # 7. Determine if and length of service disruption
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Determining if and length of service disruption')
        self.tc_result['events']['service_disruption']['duration'] = self.traffic.calculate_service_disruption_length()

        # --------------------------------------------------------------------------------------------------------------
        # 8. Start the normal traffic load
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Starting the normal traffic load')

        # Stop the low traffic load.
        self.traffic.stop()

        # Configure stream destination address(es).
        dest_addr_list = self.mano.get_vnf_ingress_cp_addr_list(
                                                          vnf_info,
                                                          self.tc_input['traffic']['traffic_config']['ingress_cp_name'])
        self.traffic.reconfig_traffic_dest(dest_addr_list)

        self.traffic.config_traffic_load('NORMAL_TRAFFIC_LOAD')

        # Start the normal traffic load.
        self.traffic.start(return_when_emission_starts=True)

        # --------------------------------------------------------------------------------------------------------------
        # 9. Validate increased capacity without traffic loss
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating increased capacity without traffic loss')
        if not self.traffic.does_traffic_flow(delay_time=constants.TRAFFIC_DELAY_TIME):
            raise TestRunError('Traffic is not flowing', err_details='Normal traffic did not flow')

        if self.traffic.any_traffic_loss(tolerance=constants.TRAFFIC_TOLERANCE):
            raise TestRunError('Traffic is flowing with packet loss',
                               err_details='Normal traffic flew with packet loss')

        self.tc_result['scaling_out']['traffic_after'] = 'NORMAL_TRAFFIC_LOAD'
        self.tc_result['scaling_in']['traffic_before'] = 'NORMAL_TRAFFIC_LOAD'

        # --------------------------------------------------------------------------------------------------------------
        # 10. Trigger the downsize of the VNF by instructing the VNF to instruct the MANO to scale in the VNF
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Triggering the downsize of the VNF by instructing the VNF to instruct the MANO to scale in the VNF')
        self.time_record.START('scale_in_vnf')
        if self.vnf.scale_sync(self.vnf_instance_id, scale_type='in', aspect_id=sp['targets'],
                               additional_param={'scaling_policy_name': self.tc_input['scaling_policy_name']}) \
                != constants.OPERATION_SUCCESS:
            self.tc_result['scaling_in']['status'] = 'Fail'
            raise TestRunError('VNF could not instruct the MANO to scale in the VNF')

        self.time_record.END('scale_in_vnf')

        self.tc_result['events']['scale_in_vnf']['duration'] = self.time_record.duration('scale_in_vnf')

        # --------------------------------------------------------------------------------------------------------------
        # 11. Validate VNF has released the resources and decreased the VNFCs
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating VNF has released the resources and decreased the VNFCs')
        vnf_info = self.mano.vnf_query(query_filter={'vnf_instance_id': self.vnf_instance_id,
                                                     'additional_param': self.tc_input['mano'].get('query_params')})
        if len(vnf_info.instantiated_vnf_info.vnfc_resource_info) != sp['min_instances']:
            raise TestRunError('VNF did not scale in')

        self.tc_result['resources']['After scale in'] = self.mano.get_allocated_vresources(
                                                                              self.vnf_instance_id,
                                                                              self.tc_input['mano'].get('query_params'))

        self.tc_result['scaling_in']['level'] = sp['min_instances']

        self.tc_result['scaling_in']['status'] = 'Success'

        # --------------------------------------------------------------------------------------------------------------
        # 12. Validate traffic drop occurred
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating traffic drop occurred')
        if not self.traffic.any_traffic_loss():
            raise TestRunError('Max traffic flew without packet loss')

        # --------------------------------------------------------------------------------------------------------------
        # 13. Reduce traffic load to level that the downsized VNF should process
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Reducing traffic load to level that the downsized VNF should process')

        # Stop the normal traffic load.
        self.traffic.stop()

        # Configure stream destination address(es)
        dest_addr_list = self.mano.get_vnf_ingress_cp_addr_list(
                                                          vnf_info,
                                                          self.tc_input['traffic']['traffic_config']['ingress_cp_name'])
        self.traffic.reconfig_traffic_dest(dest_addr_list)

        self.traffic.config_traffic_load('LOW_TRAFFIC_LOAD')

        # Start the low traffic load.
        self.traffic.start(return_when_emission_starts=True)

        # --------------------------------------------------------------------------------------------------------------
        # 14. Validate traffic flows through without issues
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating traffic flows through without issues')
        if not self.traffic.does_traffic_flow(delay_time=constants.TRAFFIC_DELAY_TIME):
            raise TestRunError('Traffic is not flowing', err_details='Low traffic did not flow')

        if self.traffic.any_traffic_loss(tolerance=constants.TRAFFIC_TOLERANCE):
            raise TestRunError('Traffic is flowing with packet loss', err_details='Low traffic flew with packet loss')

        self.tc_result['scaling_in']['traffic_after'] = 'LOW_TRAFFIC_LOAD'

        # --------------------------------------------------------------------------------------------------------------
        # 15. Terminate the VNF
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Terminating the VNF')
        self.time_record.START('terminate_vnf')
        if self.mano.vnf_terminate_sync(self.vnf_instance_id, termination_type='graceful',
                                        graceful_termination_timeout=self.tc_input.get('graceful_termination_timeout'),
                                        additional_param=self.tc_input['mano'].get('termination_params')) != \
                constants.OPERATION_SUCCESS:
            raise TestRunError('Unexpected status for terminating VNF operation',
                               err_details='VNF terminate operation failed')

        self.time_record.END('terminate_vnf')

        self.tc_result['events']['terminate_vnf']['duration'] = self.time_record.duration('terminate_vnf')

        self.unregister_from_cleanup(index=20)
        self.unregister_from_cleanup(index=10)

        self.register_for_cleanup(index=10, function_reference=self.mano.vnf_delete_id,
                                  vnf_instance_id=self.vnf_instance_id)

        # --------------------------------------------------------------------------------------------------------------
        # 16. Validate that the VNF is terminated and all resources have been released by the VIM
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating that the VNF is terminated')
        vnf_info_final = self.mano.vnf_query(query_filter={'vnf_instance_id': self.vnf_instance_id,
                                                           'additional_param': self.tc_input['mano'].get(
                                                               'query_params')})
        if vnf_info_final.instantiation_state != constants.VNF_NOT_INSTANTIATED:
            raise TestRunError('Unexpected VNF instantiation state',
                               err_details='VNF instantiation state was not "%s" after the VNF was terminated'
                                           % constants.VNF_NOT_INSTANTIATED)

        LOG.info('Validating that all resources have been released by the VIM')
        if not self.mano.validate_vnf_released_vresources(vnf_info_initial=vnf_info):
            raise TestRunError('Allocated resources have not been released by the VIM')

        LOG.info('%s execution completed successfully' % self.tc_name)
