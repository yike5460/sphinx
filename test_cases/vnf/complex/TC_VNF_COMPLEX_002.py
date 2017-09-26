import logging

from api.generic import constants
from api.generic.mano import Mano
from api.generic.traffic import Traffic
from test_cases import TestCase, TestRunError
from utils.misc import generate_name

# Instantiate logger
LOG = logging.getLogger(__name__)


class TC_VNF_COMPLEX_002(TestCase):
    """
    TC_VNF_COMPLEX_002 Stop a max scale-up/scaled-out VNF instance in state STARTED under max traffic load

    Sequence:
    1. Instantiate the VNF
    2. Validate VNF instantiation state is INSTANTIATED and VNF state is STARTED
    3. Start the low traffic load
    4. Validate that traffic flows through without issues
    5. Trigger a resize of the VNF resources to reach the maximum by instructing the MANO to scale out the VNF
    6. Validate VNF has resized to the max and has max capacity
    7. Start the max traffic load
    8. Validate all traffic flows through and has reached max capacity
    9. Stop the VNF
    10. Validate VNF instantiation state is INSTANTIATED and VNF state is STOPPED
    11. Validate no traffic flows through
    """

    required_elements = ('mano', 'traffic', 'vnfd_id', 'scaling_policy_name')

    def setup(self):
        LOG.info('Starting setup for TC_VNF_COMPLEX_002')

        # Create objects needed by the test.
        self.mano = Mano(vendor=self.tc_input['mano']['type'], **self.tc_input['mano']['client_config'])
        self.traffic = Traffic(self.tc_input['traffic']['type'], **self.tc_input['traffic']['client_config'])
        self.register_for_cleanup(self.traffic.destroy)

        # Initialize test case result.
        self.tc_result['events']['instantiate_vnf'] = dict()
        self.tc_result['events']['scale_out_vnf'] = dict()
        self.tc_result['events']['service_disruption'] = dict()
        self.tc_result['events']['stop_vnf'] = dict()
        self.tc_result['events']['traffic_deactivation'] = dict()

        LOG.info('Finished setup for TC_VNF_COMPLEX_002')

    def run(self):
        LOG.info('Starting TC_VNF_COMPLEX_002')

        # Get scaling policy properties
        sp = self.mano.get_vnfd_scaling_properties(self.tc_input['vnfd_id'], self.tc_input['scaling_policy_name'])

        # --------------------------------------------------------------------------------------------------------------
        # 1. Instantiate the VNF
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Instantiating the VNF')
        self.time_record.START('instantiate_vnf')
        self.vnf_instance_id = self.mano.vnf_create_and_instantiate(
                                                 vnfd_id=self.tc_input['vnfd_id'], flavour_id=None,
                                                 vnf_instance_name=generate_name(self.tc_input['vnf']['instance_name']),
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
                               traffic_config=self.tc_input['traffic']['traffic_config'])

        # Configure stream destination address(es)
        dest_addr_list = ''
        for ext_cp_info in vnf_info.instantiated_vnf_info.ext_cp_info:
            if ext_cp_info.cpd_id == self.tc_input['traffic']['traffic_config']['ingress_cp_name']:
                dest_addr_list += ext_cp_info.address[0] + ' '
        self.traffic.config_traffic_stream(dest_addr_list)

        self.traffic.start(return_when_emission_starts=True)

        self.register_for_cleanup(self.traffic.stop)

        # --------------------------------------------------------------------------------------------------------------
        # 4. Validate that traffic flows through without issues
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating that traffic flows through without issues')
        if not self.traffic.does_traffic_flow(delay_time=5):
            raise TestRunError('Traffic is not flowing', err_details='Low traffic did not flow')

        if self.traffic.any_traffic_loss(tolerance=constants.traffic_tolerance):
            raise TestRunError('Traffic is flowing with packet loss', err_details='Low traffic flew with packet loss')

        self.tc_result['scaling_out']['traffic_before'] = 'LOW_TRAFFIC_LOAD'

        if not self.mano.validate_allocated_vresources(self.tc_input['vnfd_id'], self.vnf_instance_id):
            raise TestRunError('Allocated vResources could not be validated')

        # --------------------------------------------------------------------------------------------------------------
        # 5. Trigger a resize of the VNF resources to reach the maximum by instructing the MANO to scale out the VNF
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Triggering a resize of the VNF resources to reach the maximum by instructing the MANO to scale out '
                 'the VNF')
        self.time_record.START('scale_out_vnf')
        if self.mano.vnf_scale_sync(self.vnf_instance_id, scale_type='out', aspect_id=sp['targets'],
                                    additional_param={'scaling_policy_name': self.tc_input['scaling_policy_name']}) \
                != constants.OPERATION_SUCCESS:
            self.tc_result['scaling_out']['status'] = 'Fail'
            raise TestRunError('MANO could not scale out the VNF')

        self.time_record.END('scale_out_vnf')

        self.tc_result['events']['scale_out_vnf']['duration'] = self.time_record.duration('scale_out_vnf')

        # --------------------------------------------------------------------------------------------------------------
        # 6. Validate VNF has resized to the max and has max capacity
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating VNF has resized to the max and has max capacity')
        vnf_info = self.mano.vnf_query(filter={'vnf_instance_id': self.vnf_instance_id})
        if len(vnf_info.instantiated_vnf_info.vnfc_resource_info) != sp['max_instances']:
            raise TestRunError('VNF did not scale out to the max')

        self.tc_result['resources']['After scale out'] = self.mano.get_allocated_vresources(self.vnf_instance_id)

        self.tc_result['scaling_out']['level'] = sp['max_instances']

        self.tc_result['scaling_out']['status'] = 'Success'

        self.tc_result['events']['service_disruption']['duration'] = self.traffic.calculate_service_disruption_length()

        # --------------------------------------------------------------------------------------------------------------
        # 7. Start the max traffic load
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Starting the max traffic load')

        # Stop the low traffic load.
        self.traffic.stop()

        # Configure stream destination address(es).
        dest_addr_list = ''
        for ext_cp_info in vnf_info.instantiated_vnf_info.ext_cp_info:
            if ext_cp_info.cpd_id == self.tc_input['traffic']['traffic_config']['ingress_cp_name']:
                dest_addr_list += ext_cp_info.address[0] + ' '

        self.traffic.config_traffic_stream(dest_addr_list)
        self.traffic.config_traffic_load('MAX_TRAFFIC_LOAD')

        # Start the max traffic load.
        self.traffic.start(return_when_emission_starts=True)

        # --------------------------------------------------------------------------------------------------------------
        # 8. Validate all traffic flows through and has reached max capacity
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating all traffic flows through and has reached max capacity')
        if not self.traffic.does_traffic_flow(delay_time=5):
            raise TestRunError('Traffic is not flowing', err_details='Max traffic did not flow')

        if self.traffic.any_traffic_loss(tolerance=constants.traffic_tolerance):
            raise TestRunError('Traffic is flowing with packet loss', err_details='Max traffic flew with packet loss')

        self.tc_result['scaling_out']['traffic_after'] = 'MAX_TRAFFIC_LOAD'

        # --------------------------------------------------------------------------------------------------------------
        # 9. Stop the VNF
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Stopping the VNF')
        # Clearing counters so traffic deactivation time is accurate
        self.traffic.clear_counters()
        self.time_record.START('stop_vnf')
        if self.mano.vnf_operate_sync(self.vnf_instance_id, change_state_to='stop') != constants.OPERATION_SUCCESS:
            raise TestRunError('MANO could not stop the VNF')
        self.time_record.END('stop_vnf')

        self.tc_result['events']['stop_vnf']['duration'] = self.time_record.duration('stop_vnf')

        self.tc_result['events']['traffic_deactivation']['duration'] = self.traffic.calculate_deactivation_time()

        # --------------------------------------------------------------------------------------------------------------
        # 10. Validate VNF instantiation state is INSTANTIATED and VNF state is STOPPED
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating VNF instantiation state is INSTANTIATED')
        vnf_info = self.mano.vnf_query(filter={'vnf_instance_id': self.vnf_instance_id})
        if vnf_info.instantiation_state != constants.VNF_INSTANTIATED:
            raise TestRunError('Unexpected VNF instantiation state',
                               err_details='VNF instantiation state was not "%s" after the VNF was stopped'
                                           % constants.VNF_INSTANTIATED)

        LOG.info('Validating VNF state is STOPPED')
        if vnf_info.instantiated_vnf_info.vnf_state != constants.VNF_STOPPED:
            raise TestRunError('Unexpected VNF state',
                               err_details='VNF state was not "%s" after the VNF was stopped' % constants.VNF_STOPPED)

        # --------------------------------------------------------------------------------------------------------------
        # 11. Validate no traffic flows through
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating no traffic flows through')
        if self.traffic.does_traffic_flow(delay_time=5):
            raise TestRunError('Traffic is still flowing', err_details='Traffic still flew after VNF was stopped')

        LOG.info('TC_VNF_COMPLEX_002 execution completed successfully')
