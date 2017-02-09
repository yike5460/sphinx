"""
Various constants and mappings.
"""
OPERATION_SUCCESS = 'SUCCESS'
OPERATION_FAILED = 'FAILED'
OPERATION_PENDING = 'PENDING'
OPERATION_FINAL_STATES = [OPERATION_SUCCESS, OPERATION_FAILED]

VNF_INSTANTIATED = 'INSTANTIATED'
VNF_NOT_INSTANTIATED = 'NOT_INSTANTIATED'

VNF_STARTED = 'STARTED'
VNF_STOPPED = 'STOPPED'
VNF_FINAL_STATES = [VNF_STARTED, VNF_STOPPED]

OPERATION_STATUS = dict()
OPERATION_STATUS['OPENSTACK_VNF_STATE'] = {'ACTIVE': OPERATION_SUCCESS,
                                           'ERROR': OPERATION_FAILED,
                                           'PENDING_CREATE': OPERATION_PENDING,
                                           'PENDING_DELETE': OPERATION_PENDING,
                                           'PENDING_UPDATE': OPERATION_PENDING}

VNF_INSTANTIATION_STATE = dict()
VNF_INSTANTIATION_STATE['OPENSTACK_VNF_STATE'] = {'ACTIVE': VNF_INSTANTIATED,
                                                  'ERROR': VNF_NOT_INSTANTIATED,
                                                  'PENDING_CREATE': VNF_NOT_INSTANTIATED,
                                                  'PENDING_DELETE': VNF_NOT_INSTANTIATED}

VNF_STATE = dict()
VNF_STATE['OPENSTACK_VNF_STATE'] = {'ACTIVE': VNF_STARTED,
                                    'ERROR': VNF_STOPPED,
                                    'PENDING_CREATE': VNF_STOPPED,
                                    'PENDING_DELETE': VNF_STOPPED}

TEST_FAILED = 'FAILED'
TEST_PASSED = 'PASSED'
