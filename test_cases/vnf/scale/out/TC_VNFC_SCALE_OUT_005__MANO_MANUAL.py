import logging

from api.generic import constants
from api.generic.mano import Mano
from api.generic.traffic import Traffic
from test_cases import TestCase, TestRunError
from utils.misc import generate_name

# Instantiate logger
LOG = logging.getLogger(__name__)


class TC_VNFC_SCALE_OUT_005__MANO_MANUAL(TestCase):
    """
    TC_VNFC_SCALE_OUT_005__MANO_MANUAL Removal of virtualized specialized hardware acceleration for VNFC scale-in with
    manual scaling event generated by MANO

    Sequence:
    1. Instantiate the VNF
    2. Validate VNF instantiation state is INSTANTIATED and VNF state is STARTED
    3. Start the low traffic load
    4. Validate traffic flows through without issues
    5. Trigger a resize of the VNF resources to use more specialized hardware by instructing the MANO to scale out the
       VNF
    6. Validate VNF has resized
    7. Start the normal traffic load
    8. Validate increased capacity without traffic loss
    9. Validate that MANO has allocated more specialized hardware resources
    10. Start the low traffic load
    11. Trigger a resize of the VNF resources to use less specialized hardware by instructing the MANO to scale in the
        VNF
    12. Validate VNF has resized and has decreased its capacity and removed VNFCs
    13. Validate that MANO has allocated less specialized hardware resources and the previous specialized hardware
        resources have been freed up
    14. Determine the service disruption during the resizing
    15. Validate traffic flows through without issues
    """

    required_elements = ('mano_params', 'traffic_params')

    def setup(self):
        LOG.info('Starting setup for TC_VNFC_SCALE_OUT_005__MANO_MANUAL')

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

        LOG.info('Finished setup for TC_VNFC_SCALE_OUT_005__MANO_MANUAL')

    def run(self):
        LOG.info('Starting TC_VNFC_SCALE_OUT_005__MANO_MANUAL')
        # TODO: Check the VNFD to see if hardware acceleration is present. This check will be added after we create an
        # internal representation for the VNFD.

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
        # 4. Validate traffic flows through without issues
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating traffic flows through without issues')
        if not self.traffic.does_traffic_flow(delay_time=5):
            raise TestRunError('Traffic is not flowing', err_details='Low traffic did not flow')

        if self.traffic.any_traffic_loss(tolerance=constants.traffic_tolerance):
            raise TestRunError('Traffic is flowing with packet loss', err_details='Low traffic flew with packet loss')

        if not self.mano.validate_allocated_vresources(self.tc_input['vnfd_id'], self.vnf_instance_id):
            raise TestRunError('Allocated vResources could not be validated')

        self.tc_result['scaling_out']['traffic_before'] = 'LOW_TRAFFIC_LOAD'

        # --------------------------------------------------------------------------------------------------------------
        # 5. Trigger a resize of the VNF resources to use more specialized hardware by instructing the MANO to scale out
        #    the VNF
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Triggering a resize of the VNF resources to use more specialized hardware by instructing the MANO to '
                 'scale out the VNF')
        self.time_record.START('scale_out_vnf')
        if self.mano.vnf_scale_sync(self.vnf_instance_id, scale_type='out', aspect_id=sp['targets'],
                                    additional_param={'scaling_policy_name': self.tc_input['scaling_policy_name']}) \
                != constants.OPERATION_SUCCESS:
            self.tc_result['scaling_out']['status'] = 'Fail'
            raise TestRunError('MANO could not scale out the VNF')

        self.time_record.END('scale_out_vnf')

        self.tc_result['events']['scale_out_vnf']['duration'] = self.time_record.duration('scale_out_vnf')

        # --------------------------------------------------------------------------------------------------------------
        # 6. Validate VNF has resized
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating VNF has resized')
        vnf_info = self.mano.vnf_query(filter={'vnf_instance_id': self.vnf_instance_id})
        if len(vnf_info.instantiated_vnf_info.vnfc_resource_info) != sp['default_instances'] + sp['increment']:
            raise TestRunError('VNF did not scale out')

        self.tc_result['resources']['After scale out'] = self.mano.get_allocated_vresources(self.vnf_instance_id)

        self.tc_result['scaling_out']['level'] = sp['default_instances'] + sp['increment']

        self.tc_result['scaling_out']['status'] = 'Success'

        # --------------------------------------------------------------------------------------------------------------
        # 7. Start the normal traffic load
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Starting the normal traffic load')

        # Stop the low traffic load.
        self.traffic.stop()

        # Configure stream destination MAC address(es).
        dest_mac_addr_list = ''
        for ext_cp_info in vnf_info.instantiated_vnf_info.ext_cp_info:
            if ext_cp_info.cpd_id == self.tc_input['traffic_params']['traffic_config']['left_cp_name']:
                dest_mac_addr_list += ext_cp_info.address[0] + ' '

        self.traffic.config_traffic_stream(dest_mac_addr_list)
        self.traffic.config_traffic_load('NORMAL_TRAFFIC_LOAD')

        # Start the normal traffic load.
        self.traffic.start(return_when_emission_starts=True)

        # --------------------------------------------------------------------------------------------------------------
        # 8. Validate increased capacity without traffic loss
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating increased capacity without traffic loss')
        if not self.traffic.does_traffic_flow(delay_time=5):
            raise TestRunError('Traffic is not flowing', err_details='Normal traffic did not flow')

        if self.traffic.any_traffic_loss(tolerance=constants.traffic_tolerance):
            raise TestRunError('Traffic is flowing with packet loss',
                               err_details='Normal traffic flew with packet loss')

        self.tc_result['scaling_out']['traffic_after'] = 'NORMAL_TRAFFIC_LOAD'
        self.tc_result['scaling_in']['traffic_before'] = 'NORMAL_TRAFFIC_LOAD'

        # --------------------------------------------------------------------------------------------------------------
        # 9. Validate that MANO has allocated more specialized hardware resources
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validate that MANO has allocated more specialized hardware resources')
        if not self.mano.validate_allocated_vresources(self.tc_input['vnfd_id'], self.vnf_instance_id):
            raise TestRunError('Allocated vResources could not be validated')

        # --------------------------------------------------------------------------------------------------------------
        # 10. Start the low traffic load
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Starting the low traffic load')

        # Stop the normal traffic load.
        self.traffic.stop()

        # Configure the traffic load.
        self.traffic.config_traffic_load('LOW_TRAFFIC_LOAD')

        # Start the low traffic load.
        self.traffic.start(return_when_emission_starts=True)

        # --------------------------------------------------------------------------------------------------------------
        # 11. Trigger a resize of the VNF resources to use less specialized hardware by instructing the MANO to scale in
        # the VNF
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Triggering a resize of the VNF resources to use less specialized hardware by instructing the MANO to '
                 'scale in the VNF')
        self.time_record.START('scale_in_vnf')
        if self.mano.vnf_scale_sync(self.vnf_instance_id, scale_type='in', aspect_id=sp['targets'],
                                    additional_param={'scaling_policy_name': self.tc_input['scaling_policy_name']}) \
                != constants.OPERATION_SUCCESS:
            self.tc_result['scaling_in']['status'] = 'Fail'
            raise TestRunError('MANO could not scale in the VNF')

        self.time_record.END('scale_in_vnf')

        self.tc_result['events']['scale_in_vnf']['duration'] = self.time_record.duration('scale_in_vnf')

        # --------------------------------------------------------------------------------------------------------------
        # 12. Validate VNF has resized and has decreased its capacity and removed VNFCs
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating VNF has resized and has decreased its capacity and removed VNFCs')
        vnf_info = self.mano.vnf_query(filter={'vnf_instance_id': self.vnf_instance_id})
        if len(vnf_info.instantiated_vnf_info.vnfc_resource_info) != sp['min_instances']:
            raise TestRunError('VNF did not scale in')

        self.tc_result['resources']['After scale in'] = self.mano.get_allocated_vresources(self.vnf_instance_id)

        self.tc_result['scaling_in']['level'] = sp['min_instances']

        self.tc_result['scaling_in']['status'] = 'Success'

        # --------------------------------------------------------------------------------------------------------------
        # 13. Validate that MANO has allocated less specialized hardware resources and the previous specialized hardware
        #     resources have been freed up
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validate that MANO has allocated less specialized hardware resources and the previous specialized '
                 'hardware resources have been freed up')
        if not self.mano.validate_allocated_vresources(self.tc_input['vnfd_id'], self.vnf_instance_id):
            raise TestRunError('Allocated vResources could not be validated')

        # --------------------------------------------------------------------------------------------------------------
        # 14. Determine the service disruption during the resizing
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Determining the service disruption during the resizing')
        self.tc_result['events']['service_disruption']['duration'] = self.traffic.calculate_service_disruption_length()

        # --------------------------------------------------------------------------------------------------------------
        # 15. Validate traffic flows through without issues
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating traffic flows through without issues')

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

        # Checking the traffic flow.
        if not self.traffic.does_traffic_flow(delay_time=5):
            raise TestRunError('Traffic is not flowing', err_details='Low traffic did not flow')

        if self.traffic.any_traffic_loss(tolerance=constants.traffic_tolerance):
            raise TestRunError('Traffic is flowing with packet loss', err_details='Low traffic flew with packet loss')

        self.tc_result['scaling_in']['traffic_after'] = 'LOW_TRAFFIC_LOAD'

        LOG.info('TC_VNFC_SCALE_OUT_005__MANO_MANUAL execution completed successfully')
