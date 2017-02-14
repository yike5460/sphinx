import logging
import yaml

from api.generic import constants
from test_cases import TestCase
from api.generic.vnfm import Vnfm

# Instantiate logger
LOG = logging.getLogger(__name__)


class TC_VNF_STATE_INST_001(TestCase):
    """
    TC_VNF_STATE_INST_001 VNF Instantiation without Element Management with configuration file without traffic

    Sequence:
    1. Instantiate VNF without load (--> time stamp)
    2. Validate VNFM reports the instantiation state INSTANTIATED (--> time stamp when correct state reached)
    3. Update VNF (--> time stamp)
    4. Validate VNFM reports the instantiation state INSTANTIATED (--> time stamp when correct state reached)
    5. Validate the right vResources have been allocated
    6. Calculate the instantiation time
    """

    def setup(self):
        LOG.info('Starting setup for TC_VNF_STATE_INST_001')

        # Create objects needed by the test.
        self.vnfm = Vnfm(vendor=self.tc_input['vnfm_params']['type'], **self.tc_input['vnfm_params']['client_config'])

        # Initialize test case result.
        self.tc_result['overall_status'] = constants.TEST_PASSED
        self.tc_result['error_info'] = 'No errors'
        self.tc_result['resource_list'] = {}

        # Store the VNF config.
        with open(self.tc_input['vnf']['config'], 'r') as vnf_config_file:
            self.vnf_config = yaml.load(vnf_config_file.read())

        LOG.info('Finished setup for TC_VNF_STATE_INST_001')

        return True

    def run(self):
        LOG.info('Starting TC_VNF_STATE_INST_001')

        # --------------------------------------------------------------------------------------------------------------
        # 1. Instantiate VNF without load (--> time stamp)
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Instantiating VNF')
        self.time_record.START('instantiate_vnf')
        self.vnf_instance_id = self.vnfm.vnf_create_and_instantiate(
                                                                vnfd_id=self.tc_input['vnfd_id'], flavour_id=None,
                                                                vnf_instance_name=self.tc_input['vnf']['instance_name'],
                                                                vnf_instance_description=None)
        if self.vnf_instance_id is None:
            LOG.error('TC_VNF_STATE_INST_001 execution failed')
            LOG.debug('Unexpected VNF instantiation ID')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'VNF instantiation operation failed'
            return False

        self.register_for_cleanup(self.vnfm.vnf_terminate_and_delete, vnf_instance_id=self.vnf_instance_id,
                                  termination_type='graceful')

        # --------------------------------------------------------------------------------------------------------------
        # 2. Validate VNFM reports the instantiation state INSTANTIATED (--> time stamp when correct state reached)
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating VNF instantiation state is INSTANTIATED')
        vnf_info = self.vnfm.vnf_query(filter={'vnf_instance_id': self.vnf_instance_id})
        if vnf_info.instantiation_state != constants.VNF_INSTANTIATED:
            LOG.error('TC_VNF_STATE_INST_001 execution failed')
            LOG.debug('Unexpected VNF instantiation state')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'VNF instantiation state was not "%s" after the VNF was instantiated' % \
                                           constants.VNF_INSTANTIATED
            return False

        self.time_record.END('instantiate_vnf')

        # --------------------------------------------------------------------------------------------------------------
        # 3. Update VNF (--> time stamp)
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Updating VNF')
        self.time_record.START('update_vnf')
        if self.vnfm.modify_vnf_configuration_sync(self.vnf_instance_id, self.vnf_config,
                                                   cooldown=120) != constants.OPERATION_SUCCESS:
            LOG.error('TC_VNF_STATE_INST_001 execution failed')
            LOG.debug('Could not update VNF')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Could not update VNF'
            return False

        # --------------------------------------------------------------------------------------------------------------
        # 4. Validate VNFM reports the instantiation state INSTANTIATED (--> time stamp when correct state reached)
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating VNF instantiation state is INSTANTIATED')
        vnf_info = self.vnfm.vnf_query(filter={'vnf_instance_id': self.vnf_instance_id})
        if vnf_info.instantiation_state != constants.VNF_INSTANTIATED:
            LOG.error('TC_VNF_STATE_INST_001 execution failed')
            LOG.debug('Unexpected VNF instantiation state')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'VNF instantiation state was not "%s" after the VNF was instantiated' % \
                                           constants.VNF_INSTANTIATED
            return False

        self.time_record.END('update_vnf')

        # --------------------------------------------------------------------------------------------------------------
        # 5. Validate the right vResources have been allocated
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Validating the right vResources have been allocated')
        if not self.vnfm.validate_allocated_vresources(self.tc_input['vnfd_id'], self.vnf_instance_id):
            LOG.error('TC_VNF_COMPLEX_002 execution failed')
            LOG.debug('Could not validate allocated vResources')
            self.tc_result['overall_status'] = constants.TEST_FAILED
            self.tc_result['error_info'] = 'Could not validate allocated vResources'
            return False

        # --------------------------------------------------------------------------------------------------------------
        # 6. Calculate the instantiation time
        # --------------------------------------------------------------------------------------------------------------
        LOG.info('Calculating the time to stop a max scaled VNF under load')
        self.tc_result['durations']['instantiate_vnf'] = self.time_record.duration('instantiate_vnf')

        LOG.info('TC_VNF_STATE_INST_001 execution completed successfully')

        return True