import logging
import time

from api.generic import constants
from api.generic.mano import Mano
from api.generic.traffic import Traffic
from api.generic.vim import Vim
from api.structures.objects import ScaleNsData, ScaleNsByStepsData
from test_cases import TestCase, TestRunError
from utils.misc import generate_name

# Instantiate logger
LOG = logging.getLogger(__name__)


class TC_VNF_SCALE_OUT_004__MANO_MANUAL__STEP_1(TestCase):
    """
    TC_VNF_SCALE_OUT_004__MANO_MANUAL__STEP_1 Max vResource VNF limit reached before max NSD limit for scale-out with
    manual scaling event generated by MANO and scaling step set to 1

    Sequence:
    1. Ensure NFVI has vResources so that the VNF can be scaled out only desired_scale_out_steps times
    2. Instantiate the NS
    3. Validate NS state is INSTANTIATED
    4. Validate VNF instantiation state is INSTANTIATED and VNF state is STARTED
    5. Start the low traffic load
    6. Validate the provided functionality and all traffic goes through
    7. Trigger a resize of the NS resources to the maximum by instructing the MANO to scale out the NS
    8. Validate NS has resized to the max (limited by NFVI)
    9. Determine the length of service disruption
    10. Start the normal traffic load
    11. Validate all traffic goes through
    """

    required_elements = ('mano_params', 'vim_params', 'traffic_params')

    def setup(self):
        LOG.info('Starting setup for TC_VNF_SCALE_OUT_004__MANO_MANUAL__STEP_1')

        # Create objects needed by the test.
        self.mano = Mano(vendor=self.tc_input['mano_params']['type'], **self.tc_input['mano_params']['client_config'])
        self.vim = Vim(vendor=self.tc_input['vim_params']['type'], **self.tc_input['vim_params']['client_config'])
        self.traffic = Traffic(self.tc_input['traffic_params']['type'],
                               **self.tc_input['traffic_params']['client_config'])
        self.register_for_cleanup(self.traffic.destroy)

        # Initialize test case result.
        self.tc_result['events']['instantiate_ns'] = dict()
        self.tc_result['events']['scale_out_ns'] = dict()
        self.tc_result['events']['service_disruption'] = dict()

        LOG.info('Finished setup for TC_VNF_SCALE_OUT_004__MANO_MANUAL__STEP_1')

    def run(self):
        LOG.info('Starting TC_VNF_SCALE_OUT_004__MANO_MANUAL__STEP_1')

        # --------------------------------------------------------------------------------------------------------------
        # 1. Ensure NFVI has vResources so that the NS can be scaled out only desired_scale_out_steps times
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Ensure NFVI has vResources so that the NS can be scaled out only desired_scale_out_steps times')
        # Reserving only compute resources is enough for limiting the NFVI resources
        reservation_id = self.mano.limit_compute_resources_for_ns_scaling(self.tc_input['nsd_id'],
                                                                          self.tc_input['scaling_policy_name'],
                                                                          self.tc_input['desired_scale_out_steps'],
                                                                          self.vim)
        if reservation_id is None:
            raise TestRunError('Compute resources could not be limited')

        self.register_for_cleanup(self.vim.terminate_compute_resource_reservation, reservation_id)

        # --------------------------------------------------------------------------------------------------------------
        # 2. Instantiate the NS
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
        # 5. Start the low traffic load
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
        # 6. Validate the provided functionality and all traffic goes through
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
        # 7. Trigger a resize of the NS resources to the maximum by instructing the MANO to scale out the NS
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Triggering a resize of the NS resources to the maximum by instructing the MANO to scale out the NS')

        # Build the ScaleNsData information element
        scale_ns_data = ScaleNsData()
        scale_ns_data.scale_ns_by_steps_data = ScaleNsByStepsData()
        scale_ns_data.scale_ns_by_steps_data.scaling_direction = 'scale_out'
        scale_ns_data.scale_ns_by_steps_data.aspect_id = self.tc_input['scaling']['aspect']
        scale_ns_data.scale_ns_by_steps_data.number_of_steps = self.tc_input['scaling']['increment']

        self.time_record.START('scale_out_ns')
        # We are scaling the NS (desired_scale_out_steps + 1) times and check at the next step that the NS scaled out
        # only desired_scale_out_steps times
        for scale_out_step in range(self.tc_input['desired_scale_out_steps'] + 1):
            if self.mano.ns_scale_sync(self.ns_instance_id, scale_type='scale_ns', scale_ns_data=scale_ns_data) \
                    != constants.OPERATION_SUCCESS:
                self.tc_result['scaling_out']['status'] = 'Fail'
                raise TestRunError('MANO could not scale out the NS to the next level')
            time.sleep(self.tc_input['scaling']['cooldown'])

        self.time_record.END('scale_out_ns')

        self.tc_result['events']['scale_out_ns']['duration'] = self.time_record.duration('scale_out_ns')

        self.tc_result['resources']['After scale out'] = dict()
        ns_info = self.mano.ns_query(filter={'ns_instance_id': self.ns_instance_id})
        for vnf_instance_id in ns_info.vnf_info_id:
            self.tc_result['resources']['After scale out'].update(self.mano.get_allocated_vresources(vnf_instance_id))

        self.tc_result['scaling_out']['status'] = 'Success'

        # --------------------------------------------------------------------------------------------------------------
        # 8. Validate NS has resized to the max (limited by NFVI)
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating NS has resized to the max (limited by NFVI)')
        # The NS should have default_instances + desired_scale_out_steps * increment VNFs after scale out
        if len(ns_info.vnf_info_id) != self.tc_input['scaling']['default_instances'] + \
                                       self.tc_input['scaling']['increment'] * self.tc_input['desired_scale_out_steps']:
            raise TestRunError('NS did not scale out to the max NFVI limit')
        self.tc_result['scaling_out']['level'] = self.tc_input['scaling']['default_instances'] + \
                                                 self.tc_input['scaling']['increment'] * \
                                                 self.tc_input['desired_scale_out_steps']

        # --------------------------------------------------------------------------------------------------------------
        # 9. Determine the length of service disruption
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Determining the length of service disruption')
        self.tc_result['events']['service_disruption']['duration'] = self.traffic.calculate_service_disruption_length()

        # --------------------------------------------------------------------------------------------------------------
        # 10. Start the normal traffic load
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Starting the normal traffic load')

        # Stop the low traffic load.
        self.traffic.stop()

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
        self.traffic.start(return_when_emission_starts=True)

        # --------------------------------------------------------------------------------------------------------------
        # 11. Validate all traffic goes through
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating all traffic goes through')
        if not self.traffic.does_traffic_flow(delay_time=5):
            raise TestRunError('Traffic is not flowing', err_details='Normal traffic did not flow')

        if self.traffic.any_traffic_loss():
            raise TestRunError('Traffic is flowing with packet loss',
                               err_details='Normal traffic flew with packet loss')

        self.tc_result['scaling_out']['traffic_after'] = 'NORMAL_TRAFFIC_LOAD'

        LOG.info('TC_VNF_SCALE_OUT_004__MANO_MANUAL__STEP_1 execution completed successfully')
