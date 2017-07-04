import logging
import time

from api.generic import constants
from api.generic.mano import Mano
from api.generic.traffic import Traffic
from test_cases import TestCase, TestRunError
from utils.misc import generate_name

# Instantiate logger
LOG = logging.getLogger(__name__)


class TC_VNF_SCALE_OUT_003__MANO_ONDEMAND__VIM_KPI(TestCase):
    """
    TC_VNF_SCALE_OUT_003__MANO_ONDEMAND__VIM_KPI Scale-in VNF instance with on-demand scaling event generated by MANO.
    The stimulus for scaling in is a VIM key performance indicator threshold crossing.

    Sequence:
    1. Instantiate the NS
    2. Validate NS state is INSTANTIATED
    3. Validate VNF instantiation state is INSTANTIATED and VNF state is STARTED
    4. Start the low traffic load
    5. Validate the provided functionality and all traffic goes through
    6. Trigger a resize of the NS resources to the next level by altering a VIM KPI
    7. Validate NS has resized to the next level
    8. Determine if and length of service disruption
    9. Validate increased capacity without traffic loss
    10. Trigger the downsize of the NS by altering a a VIM KPI
    11. Validate NS has released the resources and decreased the VNFs
    12. Validate traffic drop occurred
    13. Validate traffic flows through without issues
    """

    def setup(self):
        LOG.info('Starting setup for TC_VNF_SCALE_OUT_003__MANO_ONDEMAND__VIM_KPI')

        # Create objects needed by the test.
        self.mano = Mano(vendor=self.tc_input['mano_params']['type'], **self.tc_input['mano_params']['client_config'])
        self.traffic = Traffic(self.tc_input['traffic_params']['type'],
                               **self.tc_input['traffic_params']['client_config'])
        self.register_for_cleanup(self.traffic.destroy)

        # Initialize test case result.
        self.tc_result['events']['instantiate_ns'] = dict()
        self.tc_result['events']['scale_out_ns'] = dict()
        self.tc_result['events']['service_disruption'] = dict()
        self.tc_result['events']['scale_in_ns'] = dict()

        LOG.info('Finished setup for TC_VNF_SCALE_OUT_003__MANO_ONDEMAND__VIM_KPI')

    def run(self):
        LOG.info('Starting TC_VNF_SCALE_OUT_003__MANO_ONDEMAND__VIM_KPI')

        # --------------------------------------------------------------------------------------------------------------
        # 1. Instantiate the NS
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Instantiating the NS')
        self.time_record.START('instantiate_ns')
        self.ns_instance_id = self.mano.ns_create_and_instantiate(nsd_id=self.tc_input['nsd_id'],
                                                                  ns_name=generate_name(self.tc_input['ns']['name']),
                                                                  ns_description=None, flavour_id=None)
        if self.ns_instance_id is None:
            raise TestRunError('Unexpected NS instantiation ID', err_details='NS instantiation operation failed')

        self.time_record.END('instantiate_ns')

        self.tc_result['events']['instantiate_ns']['duration'] = self.time_record.duration('instantiate_ns')

        self.register_for_cleanup(self.mano.ns_terminate_and_delete, ns_instance_id=self.ns_instance_id)

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

        if self.traffic.any_traffic_loss():
            raise TestRunError('Traffic is flowing with packet loss', err_details='Low traffic flew with packet loss')

        self.tc_result['scaling_out']['traffic_before'] = 'LOW_TRAFFIC_LOAD'

        if not self.mano.validate_allocated_vresources(self.tc_input['vnfd_id'], self.vnf_instance_id):
            raise TestRunError('Allocated vResources could not be validated')

        # --------------------------------------------------------------------------------------------------------------
        # 6. Trigger a resize of the NS resources to the next level by altering a VIM KPI
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Triggering a resize of the NS resources to the next level by altering a VIM KPI')

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
        # 7. Validate NS has resized to the next level
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating NS has resized to the next level')
        # The scale out duration will include:
        # - the time it takes the VNF CPU load to increase (caused by the max traffic load)
        # - the time after which the scaling alarm is triggered
        # - the time it takes the NS to scale out
        self.time_record.START('scale_out_ns')
        elapsed_time = 0
        while elapsed_time < constants.SCALE_INTERVAL:
            ns_info = self.mano.ns_query(filter={'ns_instance_id': self.ns_instance_id})
            if len(ns_info.vnf_info_id) == self.tc_input['scaling']['default_instances'] + \
                    self.tc_input['scaling']['increment']:
                break
            else:
                time.sleep(constants.POLL_INTERVAL)
                elapsed_time += constants.POLL_INTERVAL
            if elapsed_time == constants.SCALE_INTERVAL:
                self.tc_result['scaling_out']['status'] = 'Fail'
                raise TestRunError('VNFs not added after traffic load was increased to the maximum')

        self.time_record.END('scale_out_ns')

        self.tc_result['scaling_out']['level'] = self.tc_input['scaling']['default_instances'] + \
                                                 self.tc_input['scaling']['increment']

        self.tc_result['events']['scale_out_ns']['duration'] = self.time_record.duration('scale_out_ns')

        self.tc_result['resources']['After scale out'] = dict()
        for vnf_instance_id in ns_info.vnf_info_id:
            self.tc_result['resources']['After scale out'].update(self.mano.get_allocated_vresources(vnf_instance_id))

        self.tc_result['scaling_out']['status'] = 'Success'

        # --------------------------------------------------------------------------------------------------------------
        # 8. Determine if and length of service disruption
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Determining if and length of service disruption')
        self.tc_result['events']['service_disruption']['duration'] = self.traffic.calculate_service_disruption_length()

        # --------------------------------------------------------------------------------------------------------------
        # 9. Validate increased capacity without traffic loss
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating increased capacity without traffic loss')
        # Because the NS scaled out, we need to reconfigure traffic so that it passes through all VNFs.

        # Stop the max traffic load.
        self.traffic.stop()

        # Configure stream destination MAC address(es).
        dest_mac_addr_list = ''
        for vnf_instance_id in ns_info.vnf_info_id:
            vnf_info = self.mano.vnf_query(filter={'vnf_instance_id': vnf_instance_id})
            for ext_cp_info in vnf_info.instantiated_vnf_info.ext_cp_info:
                if ext_cp_info.cpd_id == self.tc_input['traffic_params']['traffic_config']['left_cp_name']:
                    dest_mac_addr_list += ext_cp_info.address[0] + ' '

        self.traffic.config_traffic_stream(dest_mac_addr_list)
        self.traffic.clear_counters()

        # Start the max traffic load.
        self.traffic.start(return_when_emission_starts=True)

        if not self.traffic.does_traffic_flow(delay_time=5):
            raise TestRunError('Traffic is not flowing', err_details='Max traffic did not flow')

        if self.traffic.any_traffic_loss():
            raise TestRunError('Traffic is flowing with packet loss', err_details='Max traffic flew with packet loss')

        self.tc_result['scaling_out']['traffic_after'] = 'MAX_TRAFFIC_LOAD'
        self.tc_result['scaling_in']['traffic_before'] = 'MAX_TRAFFIC_LOAD'

        # --------------------------------------------------------------------------------------------------------------
        # 10. Trigger the downsize of the VNF by altering a VIM KPI
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Triggering the downsize of the VNF by altering a VIM KPI')

        # The scale in is triggered by a VIM KPI threshold crossing.
        # The Virtualised Resources Performance Management interface Or-Vi will enable the MANO to trigger a scale
        # in based on a VIM KPI.
        # There are 2 ways for MANO to obtain KPI information:
        # - by polling the VIM periodically on the Or-Vi interface (by means of a PM job)
        # - by subscribing for notifications related to performance information with the VIM. The MANO can define
        #   thresholds that generate notifications from the VIM when they are crossed.

        # TODO: Insert here code to:
        # 1. alter a VIM KPI so that MANO can trigger an NS scale in
        # 2. check that MANO has subscribed to VIM
        # 3. subscribe to VIM and check the notifications
        # For now we use only traffic load to trigger the scale in (we will decrease the traffic load to the minimum).
        self.traffic.config_traffic_load('LOW_TRAFFIC_LOAD')

        # --------------------------------------------------------------------------------------------------------------
        # 11. Validate NS has released the resources and decreased the VNFs
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating NS has released the resources and decreased the VNFs')
        # The scale in duration will include:
        # - the time it takes the VNF CPU load to decrease (caused by the low traffic load)
        # - the time after which the scaling alarm is triggered
        # - the time it takes the NS to scale in
        self.time_record.START('scale_in_ns')
        elapsed_time = 0
        while elapsed_time < constants.SCALE_INTERVAL:
            ns_info = self.mano.ns_query(filter={'ns_instance_id': self.ns_instance_id})
            if len(ns_info.vnf_info_id) == self.tc_input['scaling']['default_instances']:
                break
            else:
                time.sleep(constants.POLL_INTERVAL)
                elapsed_time += constants.POLL_INTERVAL
            if elapsed_time == constants.SCALE_INTERVAL:
                self.tc_result['scaling_in']['status'] = 'Fail'
                raise TestRunError('NS did not scale in')

        self.time_record.END('scale_in_ns')

        self.tc_result['scaling_in']['level'] = self.tc_input['scaling']['default_instances']

        self.tc_result['events']['scale_in_ns']['duration'] = self.time_record.duration('scale_in_ns')

        self.vnf_instance_id = ns_info.vnf_info_id[0]
        self.tc_result['resources']['After scale in'] = self.mano.get_allocated_vresources(self.vnf_instance_id)

        self.tc_result['scaling_in']['status'] = 'Success'

        # --------------------------------------------------------------------------------------------------------------
        # 12. Validate traffic drop occurred
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating traffic drop occurred')
        if not self.traffic.any_traffic_loss():
            raise TestRunError('Max traffic flew without packet loss')

        # --------------------------------------------------------------------------------------------------------------
        # 13. Validate traffic flows through without issues
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating traffic flows through without issues')
        # Because the NS scaled in, we need to reconfigure traffic so that it passes through the new VNF.

        # Stop the low traffic load.
        self.traffic.stop()

        # Configure stream destination MAC address(es).
        dest_mac_addr_list = ''
        vnf_info = self.mano.vnf_query(filter={'vnf_instance_id': self.vnf_instance_id})
        for ext_cp_info in vnf_info.instantiated_vnf_info.ext_cp_info:
            if ext_cp_info.cpd_id == self.tc_input['traffic_params']['traffic_config']['left_cp_name']:
                dest_mac_addr_list += ext_cp_info.address[0] + ' '

        self.traffic.config_traffic_stream(dest_mac_addr_list)
        self.traffic.clear_counters()

        # Start the low traffic load.
        self.traffic.start(return_when_emission_starts=True)

        if not self.traffic.does_traffic_flow(delay_time=5):
            raise TestRunError('Traffic is not flowing', err_details='Low traffic did not flow')

        if self.traffic.any_traffic_loss():
            raise TestRunError('Traffic is flowing with packet loss', err_details='Low traffic flew with packet loss')

        self.tc_result['scaling_in']['traffic_after'] = 'LOW_TRAFFIC_LOAD'

        LOG.info('TC_VNF_SCALE_OUT_003__MANO_ONDEMAND__VIM_KPI execution completed successfully')
