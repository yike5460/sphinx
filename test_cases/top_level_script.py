#!/usr/bin/env python

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


from datetime import datetime
import logging

from utils.logging_module import configure_logger
from api.structures.objects import ScalingAspect, VduCpd
from test_cases.vnf.state.inst.TC_VNF_STATE_INST_001 import TC_VNF_STATE_INST_001
from test_cases.vnf.state.inst.TC_VNF_STATE_INST_002 import TC_VNF_STATE_INST_002
from test_cases.vnf.state.term.TC_VNF_STATE_TERM_002 import TC_VNF_STATE_TERM_002
from test_cases.vnf.scale.out.TC_VNFC_SCALE_OUT_001__MANO_ONDEMAND__EM_IND import \
    TC_VNFC_SCALE_OUT_001__MANO_ONDEMAND__EM_IND
from test_cases.vnf.scale.out.TC_VNFC_SCALE_OUT_001__MANO_MANUAL import TC_VNFC_SCALE_OUT_001__MANO_MANUAL
from test_cases.vnf.scale.out.TC_VNFC_SCALE_OUT_002__MANO_MANUAL import TC_VNFC_SCALE_OUT_002__MANO_MANUAL
from test_cases.vnf.scale.out.TC_VNFC_SCALE_OUT_003__MANO_MANUAL import TC_VNFC_SCALE_OUT_003__MANO_MANUAL
from test_cases.vnf.scale.out.TC_VNFC_SCALE_OUT_004__MANO_MANUAL__STEP_1 import \
    TC_VNFC_SCALE_OUT_004__MANO_MANUAL__STEP_1
from test_cases.vnf.scale.out.TC_VNFC_SCALE_OUT_004__MANO_MANUAL__STEP_MAX import \
    TC_VNFC_SCALE_OUT_004__MANO_MANUAL__STEP_MAX
from test_cases.vnf.scale.out.TC_VNFC_SCALE_OUT_004__MANO_ONDEMAND__EM_IND__STEP_1 import \
    TC_VNFC_SCALE_OUT_004__MANO_ONDEMAND__EM_IND__STEP_1
from test_cases.vnf.scale.out.TC_VNFC_SCALE_OUT_005__MANO_MANUAL import TC_VNFC_SCALE_OUT_005__MANO_MANUAL
from test_cases.vnf.state.start.TC_VNF_STATE_START_001 import TC_VNF_STATE_START_001
from test_cases.vnf.state.start.TC_VNF_STATE_START_002 import TC_VNF_STATE_START_002
from test_cases.vnf.state.start.TC_VNF_STATE_START_003 import TC_VNF_STATE_START_003
from test_cases.vnf.state.stop.TC_VNF_STATE_STOP_001 import TC_VNF_STATE_STOP_001
from test_cases.vnf.state.stop.TC_VNF_STATE_STOP_002 import TC_VNF_STATE_STOP_002
from test_cases.vnf.state.stop.TC_VNF_STATE_STOP_003 import TC_VNF_STATE_STOP_003
from test_cases.vnf.state.term.TC_VNF_STATE_TERM_001 import TC_VNF_STATE_TERM_001
from test_cases.vnf.state.term.TC_VNF_STATE_TERM_003 import TC_VNF_STATE_TERM_003
from test_cases.vnf.state.term.TC_VNF_STATE_TERM_004 import TC_VNF_STATE_TERM_004
from test_cases.vnf.state.term.TC_VNF_STATE_TERM_005 import TC_VNF_STATE_TERM_005
from test_cases.vnf.complex.TC_VNF_COMPLEX_002 import TC_VNF_COMPLEX_002
from test_cases.vnf.complex.TC_VNF_COMPLEX_003 import TC_VNF_COMPLEX_003
from test_cases.vnf.state.inst.TC_VNF_STATE_INST_003 import TC_VNF_STATE_INST_003
from test_cases.vnf.state.inst.TC_VNF_STATE_INST_004 import TC_VNF_STATE_INST_004
from test_cases.vnf.state.inst.TC_VNF_STATE_INST_005 import TC_VNF_STATE_INST_005
from test_cases.vnf.state.inst.TC_VNF_STATE_INST_006 import TC_VNF_STATE_INST_006
from test_cases.vnf.state.inst.TC_VNF_STATE_INST_007 import TC_VNF_STATE_INST_007_001, TC_VNF_STATE_INST_007_002, \
    TC_VNF_STATE_INST_007_003, TC_VNF_STATE_INST_007_004, TC_VNF_STATE_INST_007_005, TC_VNF_STATE_INST_007_006, \
    TC_VNF_STATE_INST_007_007, TC_VNF_STATE_INST_007_008

log_file_name = '{:%Y_%m_%d_%H_%M_%S}'.format(datetime.now()) + '.log'

# Getting and configuring the RootLogger.
root_logger = logging.getLogger()
configure_logger(root_logger, file_level='DEBUG', log_filename=log_file_name, console_level='INFO', propagate=True)

print root_logger
# Logger for the current module.
LOG = logging.getLogger(__name__)

if __name__ == '__main__':
    openstack = {
        'mano': {
            'type': 'tacker',
            'client_config': {
                'auth_url': 'http://10.3.228.230:35357/v3',
                'username': 'admin',
                'password': 'admin',
                'identity_api_version': '3',
                'project_name': 'admin',
                'project_domain_name': 'default',
                'user_domain_name': 'default'
            },
            'instantiation_params': {},
            'query_params': {},
            'termination_params': {},
            'operate_params': {}
        },
        'vim': {
            'type': 'openstack',
            'client_config': {
                'auth_url': 'http://10.3.228.202:35357/v3',
                'username': 'admin',
                'password': 'admin',
                'identity_api_version': '3',
                'project_name': 'admin',
                'project_domain_name': 'default',
                'user_domain_name': 'default'
            }
        },
        'em': {
            'type': 'tacker',
            'client_config': {
                'auth_url': 'http://10.3.228.230:35357/v3',
                'username': 'admin',
                'password': 'admin',
                'identity_api_version': '3',
                'project_name': 'admin',
                'project_domain_name': 'default',
                'user_domain_name': 'default'
            }
        },
        'nsd_id': 'c0870bda-e5f3-477c-be22-0d791f8bb828',
        'ns': {
            'name': 'test_ns'
        },
        'flavour_id': None,
        'instantiation_level_id': None,
        # VNFD with IP and MAC
        # 'vnfd_id': 'c849dc0f-c5b2-4164-b883-b630a0d0812b',
        # VNFD with SP
        'vnfd_id': 'a1eff079-d75e-4b9b-84b0-c5a0fcd6fc58',
        # VNFD with max SP
        # 'vnfd_id': 'b40f227f-2f0d-4eb6-ba53-df54bd525529',
        # VNF that requires EM
        # 'vnfd_id': 'b8933098-950f-49b4-961c-a63dc458ba05',
        # VNFD with config
        # 'vnfd_id': '65340c17-52b4-45da-8a48-9bd64cdb9eac',
        # VNFD no mgmt_driver
        # 'vnfd_id': 'c5f1ef7c-397d-4953-9afd-c74e818d68c0',
        # VNFD exceeding vMemory size
        # 'vnfd_id': '8e47b1f1-1a39-447c-bd56-23e705177252',
        # VNFD exceeding vStorage size
        # 'vnfd_id': '6d1e53b9-3373-4143-9db6-1e10af3b827b',
        # VNFD exceeding vCPU count
        # 'vnfd_id': '376bc7b1-1635-4232-be7a-f68c5405d917',
        # VNFD requires SRIOV
        # 'vnfd_id': '80fd7708-4745-4e2b-9241-69efd2238a6d',
        # VNFD with SP & alarm scaling
        # 'vnfd_id': '8e451832-349e-4589-893f-7339f5c05fbb',
        # VNFD with exceeding SP step 1
        # 'vnfd_id': '3f7a41e6-d0d3-4afe-9f14-d7d619a89e6a',
        # VNFD with exceeding SP step max
        # 'vnfd_id': '3404c2de-3a31-434b-bacf-62c913a6322f',
        'vnf': {
            'type': 'ubuntu',
            'instance_name': 'test_vnf',
            'credentials': {
                'mgmt_ip_addr': '172.31.203.111',
                'username': 'cirros',
                'password': 'cubswin:)'
            },
            'config': '/home/mdragomir/Downloads/owrt_forward.yaml'
            # 'config': '/home/mdragomir/Downloads/owrt_empty_config.yaml'
        },
        'traffic': {
            'type': 'stc',
            'client_config': {
                'lab_server_addr': '10.3.228.13',
                'user_name': 'cudroiu',
                'session_name': 'automation'
            },
            'traffic_config': {
                'type': 'VNF_TRANSIENT',
                'left_port_location': '10.3.228.231/1/1',
                'left_traffic_addr': '172.16.1.3',
                'left_traffic_plen': '24',
                'left_traffic_gw': '172.16.1.10',
                'left_traffic_gw_mac': '00:11:22:33:44:55',
                'ingress_cp_name': 'CP2',
                'right_port_location': '10.3.228.232/1/1',
                'right_traffic_addr': '172.16.2.3',
                'right_traffic_plen': '24',
                'right_traffic_gw': '0.0.0.0'
            }
        },
        'scaling_policy_name': 'SP1',
        'scaling': {
            'aspect': 'VDU1',
            'increment': 1,
            'cooldown': 3,
            'min_instances': 1,
            'max_instances': 3,
            'default_instances': 1},
        'desired_scale_out_steps': 2,
        'process_type': 'update',
        'performance': {
            'metric': 'vCPU',
            'collecting_period': 60,
            'reporting_period': 60,
            'reporting_boundary': 60,
            'threshold': {
                'type': 'single_value',
                'value_to_be_crossed': 12,
                'direction_in_which_value_is_crossed': 'above'
            }
        },
        'fault': {
            'injection_command': 'vim_command_to_stop_vnf',
            'recovery_source': 'vnfm'
        }
    }

    LOG.info('Starting top level script')
    # Use VNFD with config
    # LOG.info('Calling test case TC_VNF_STATE_INST_001')
    # TC_VNF_STATE_INST_001(tc_input=openstack).execute()
    # LOG.info('Calling test case TC_VNF_STATE_INST_002')
    # TC_VNF_STATE_INST_002(tc_input=openstack).execute()

    # Use VNF that requires EM, config owrt_forward.yaml
    # LOG.info('Calling test case TC_VNF_STATE_INST_003')
    # TC_VNF_STATE_INST_003(tc_input=openstack).execute()
    # LOG.info('Calling test case TC_VNF_STATE_INST_004')
    # TC_VNF_STATE_INST_004(tc_input=openstack).execute()

    # Use VNF that requires EM, config owrt_empty_config.yaml
    # LOG.info('Calling test case TC_VNF_STATE_INST_005')
    # TC_VNF_STATE_INST_005(tc_input=openstack).execute()

    # Use VNFD no mgmt_driver
    # LOG.info('Calling test case TC_VNF_STATE_INST_006')
    # TC_VNF_STATE_INST_006(tc_input=openstack).execute()

    # Use VNFD that requires unavailable resources
    # LOG.info('Calling test case TC_VNF_STATE_INST_007_001')
    # TC_VNF_STATE_INST_007_001(tc_input=openstack).execute()
    # LOG.info('Calling test case TC_VNF_STATE_INST_007_002')
    # TC_VNF_STATE_INST_007_002(tc_input=openstack).execute()
    # LOG.info('Calling test case TC_VNF_STATE_INST_007_003')
    # TC_VNF_STATE_INST_007_003(tc_input=openstack).execute()
    # LOG.info('Calling test case TC_VNF_STATE_INST_007_004')
    # TC_VNF_STATE_INST_007_004(tc_input=openstack).execute()
    # LOG.info('Calling test case TC_VNF_STATE_INST_007_005')
    # TC_VNF_STATE_INST_007_005(tc_input=openstack).execute()
    # LOG.info('Calling test case TC_VNF_STATE_INST_007_006')
    # TC_VNF_STATE_INST_007_006(tc_input=openstack).execute()
    # LOG.info('Calling test case TC_VNF_STATE_INST_007_007')
    # TC_VNF_STATE_INST_007_007(tc_input=openstack).execute()
    # LOG.info('Calling test case TC_VNF_STATE_INST_007_008')
    # TC_VNF_STATE_INST_007_008(tc_input=openstack).execute()

    # Use VNFD with IP and MAC
    # LOG.info('Calling test case TC_VNF_STATE_TERM_001')
    # TC_VNF_STATE_TERM_001(tc_input=openstack).execute()
    # LOG.info('Calling test case TC_VNF_STATE_TERM_002')
    # TC_VNF_STATE_TERM_002(tc_input=openstack).execute()
    # LOG.info('Calling test case TC_VNF_STATE_TERM_003')
    # TC_VNF_STATE_TERM_003(tc_input=openstack).execute()
    # LOG.info('Calling test case TC_VNF_STATE_TERM_004')
    # TC_VNF_STATE_TERM_004(tc_input=openstack).execute()
    # LOG.info('Calling test case TC_VNF_STATE_TERM_005')
    # TC_VNF_STATE_TERM_005(tc_input=openstack).execute()

    # Use VNFD with IP and MAC
    # LOG.info('Calling test case TC_VNF_STATE_START_001')
    # TC_VNF_STATE_START_001(tc_input=openstack).execute()
    # LOG.info('Calling test case TC_VNF_STATE_START_002')
    # TC_VNF_STATE_START_002(tc_input=openstack).execute()
    # LOG.info('Calling test case TC_VNF_STATE_START_003')
    # TC_VNF_STATE_START_003(tc_input=openstack).execute()

    # Use VNFD with IP and MAC
    # LOG.info('Calling test case TC_VNF_STATE_STOP_001')
    # TC_VNF_STATE_STOP_001(tc_input=openstack).execute()
    # LOG.info('Calling test case TC_VNF_STATE_STOP_002')
    # TC_VNF_STATE_STOP_002(tc_input=openstack).execute()
    # LOG.info('Calling test case TC_VNF_STATE_STOP_003')
    # TC_VNF_STATE_STOP_003(tc_input=openstack).execute()

    # Use VNFD with SP
    # LOG.info('Calling test case TC_VNFC_SCALE_OUT_001__MANO_MANUAL')
    # TC_VNFC_SCALE_OUT_001__MANO_MANUAL(tc_input=openstack).execute()
    # LOG.info('Calling test case TC_VNFC_SCALE_OUT_003__MANO_MANUAL')
    # TC_VNFC_SCALE_OUT_003__MANO_MANUAL(tc_input=openstack).execute()
    # LOG.info('Calling test case TC_VNFC_SCALE_OUT_005__MANO_MANUAL')
    # TC_VNFC_SCALE_OUT_005__MANO_MANUAL(tc_input=openstack).execute()

    # Use VNFD with max SP
    # LOG.info('Calling test case TC_VNFC_SCALE_OUT_002__MANO_MANUAL')
    # TC_VNFC_SCALE_OUT_002__MANO_MANUAL(tc_input=openstack).execute()

    # Use VNFD with exceeding SP step max
    # LOG.info('Calling test case TC_VNFC_SCALE_OUT_004__MANO_MANUAL__STEP_MAX')
    # TC_VNFC_SCALE_OUT_004__MANO_MANUAL__STEP_MAX(tc_input=openstack).execute()

    # Use VNFD with exceeding SP step 1
    # LOG.info('Calling test case TC_VNFC_SCALE_OUT_004__MANO_ONDEMAND__EM_IND__STEP_1')
    # TC_VNFC_SCALE_OUT_004__MANO_ONDEMAND__EM_IND__STEP_1(tc_input=openstack).execute()
    # LOG.info('Calling test case TC_VNFC_SCALE_OUT_004__MANO_MANUAL__STEP_1')
    # TC_VNFC_SCALE_OUT_004__MANO_MANUAL__STEP_1(tc_input=openstack).execute()

    # Use VNFD with max SP
    # LOG.info('Calling test case TC_VNF_COMPLEX_002')
    # TC_VNF_COMPLEX_002(tc_input=openstack).execute()
    # LOG.info('Calling test case TC_VNF_COMPLEX_003')
    # TC_VNF_COMPLEX_003(tc_input=openstack).execute()

    LOG.info('Exiting top level script')
