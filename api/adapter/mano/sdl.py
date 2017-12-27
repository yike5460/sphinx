import json
import logging
import requests
import time

from api.adapter import construct_adapter
from api.adapter.mano import ManoAdapterError
from api.generic import constants
from api.structures.objects import ResourceHandle, InstantiatedVnfInfo, NsInfo, VnfInfo, VnfcResourceInfo
from utils.logging_module import log_entry_exit

# Instantiate logger
LOG = logging.getLogger(__name__)


class SdlManoAdapterError(ManoAdapterError):
    """
    A problem occurred in the VNF LifeCycle Validation SDL MANO adapter API.
    """
    pass


class SdlManoAdapter(object):
    def __init__(self, endpoint_url, backend_url, tenant_id, username, password):
        self.endpoint_url = endpoint_url
        self.backend_url = backend_url

        self.token = self.get_token(username, password)
        self.cookiejar = self.get_cookies(username, password)

        # TODO: tenant_id may need to be moved in instantiation_params
        self.tenant_id = tenant_id

        self.ns_update_json_mapping = dict()
        self.ns_nsd_mapping = dict()

    @log_entry_exit(LOG)
    def get_token(self, username, password):
        response = requests.post(url=self.backend_url + '/token', data={
            'user': username,
            'passwd': password})

        assert response.status_code == 200
        token = response.json()['token']

        return token

    @log_entry_exit(LOG)
    def get_cookies(self, username, password):
        response = requests.post(url=self.backend_url + '/token', data={
            'user': username,
            'passwd': password})

        assert response.status_code == 200
        return response.cookies

    @log_entry_exit(LOG)
    def get_nsd_id_from_name(self, nsd_name):
        # TODO: treat invalid nsd_name
        response = requests.get(self.backend_url + '/nst/', cookies=self.cookiejar, headers={'Token': self.token})
        assert response.status_code == 200

        nsd_list = response.json()['data']
        for nsd_dict in nsd_list:
            if nsd_dict['name'] == nsd_name:
                return nsd_dict['uuid']

    @log_entry_exit(LOG)
    def get_nsd(self, nsd_id):
        # TODO: treat invalid nsd_id
        response = requests.get(self.backend_url + '/nst/details', params={'uuid': nsd_id}, cookies=self.cookiejar,
                                headers={'Token': self.token})

        assert response.status_code == 200
        raw_nsd = response.json()['data']

        response = requests.post(self.backend_url + '/nst/export', json=raw_nsd, cookies=self.cookiejar,
                                headers={'Token': self.token})
        assert response.status_code == 200
        converted_nsd = response.json()['data']

        return converted_nsd

    @log_entry_exit(LOG)
    def ns_create_id(self, nsd_id, ns_name, ns_description):
        # Assuming user will most likely used nsd_name as input
        real_nsd_id = self.get_nsd_id_from_name(nsd_id)
        nsd_dict = self.get_nsd(real_nsd_id)

        nsd_dict['is_enabled'] = False
        nsd_dict['name'] = ns_name
        nsd_dict['description'] = ns_description

        response = requests.post(url=self.endpoint_url + '/nfv_network_service', params={'tenant_id': self.tenant_id},
                                 json=nsd_dict)

        assert response.status_code == 200
        ns_instance_id = response.json()['nfvns_uuid']

        self.ns_update_json_mapping[ns_instance_id] = nsd_dict
        self.ns_nsd_mapping[ns_instance_id] = real_nsd_id

        return ns_instance_id

    @log_entry_exit(LOG)
    def ns_instantiate(self, ns_instance_id, flavour_id, sap_data=None, pnf_info=None, vnf_instance_data=None,
                       nested_ns_instance_data=None, location_constraints=None, additional_param_for_ns=None,
                       additional_param_for_vnf=None, start_time=None, ns_instantiation_level_id=None,
                       additional_affinity_or_anti_affinity_rule=None):

        ns_update_dict = self.ns_update_json_mapping[ns_instance_id]
        ns_update_dict['is_enabled'] = True

        # TODO: expose via params
        ns_update_dict['default_location_constraints'] = dict()
        ns_update_dict['default_location_constraints']['virp_type'] = 'OPENSTACK'

        response = requests.put(url=self.endpoint_url + '/nfv_network_service/%s' % ns_instance_id, json=ns_update_dict)
        assert response.status_code == 200

        return 'ns_instantiate', ns_instance_id

    @log_entry_exit(LOG)
    def get_operation_status(self, lifecycle_operation_occurrence_id):
        operation_type, resource_id = lifecycle_operation_occurrence_id

        if operation_type == 'ns_instantiate':
            response = requests.get(url=self.endpoint_url + '/nfv_network_service/%s' % resource_id)
            ns_instance_state = response.json()['state']

            if ns_instance_state == 'running':
                return constants.OPERATION_SUCCESS
            elif ns_instance_state == 'failed':
                return constants.OPERATION_FAILED
            else:
                return constants.OPERATION_PENDING

        if operation_type == 'ns_terminate':
            response = requests.get(url=self.endpoint_url + '/nfv_network_service/%s' % resource_id)
            ns_instance_state = response.json()['state']

            if ns_instance_state == 'disabled':
                return constants.OPERATION_SUCCESS
            elif ns_instance_state == 'failed':
                return constants.OPERATION_FAILED
            else:
                return constants.OPERATION_PENDING

    @log_entry_exit(LOG)
    def ns_query(self, filter, attribute_selector=None):
        ns_instance_id = filter['ns_instance_id']
        ns_info = NsInfo()
        ns_info.ns_instance_id = str(ns_instance_id)

        response = requests.get(url=self.endpoint_url + '/nfv_network_service/%s' % ns_instance_id)
        ns_instance_dict = response.json()

        ns_info.ns_name = str(ns_instance_dict['name'])
        ns_info.description = str(ns_instance_dict['description'])
        ns_info.nsd_id = str(self.ns_nsd_mapping[ns_info.ns_instance_id])

        if ns_instance_dict['state'] == 'running':
            ns_info.ns_state = constants.NS_INSTANTIATED
        else:
            ns_info.ns_state = constants.NS_NOT_INSTANTIATED

        ns_info.vnf_info = list()
        for service_desc in ns_instance_dict['service_desc_list']:
            vnf_instance_id = service_desc['instance_id']
            if vnf_instance_id != '':
                vnf_info = self.vnf_query(filter={'vnf_instance_id': vnf_instance_id})
                ns_info.vnf_info.append(vnf_info)

        return ns_info

    @log_entry_exit(LOG)
    def vnf_query(self, filter, attribute_selector=None):
        vnf_instance_id = filter['vnf_instance_id']
        vnf_info = VnfInfo()
        vnf_info.vnf_instance_id = vnf_instance_id.encode()

        response = requests.get(url=self.endpoint_url + '/nfv/vnf/vnf-instance/%s' % vnf_instance_id)
        vnf_instance_dict = response.json()

        if response.status_code == 404:
            vnf_info.instantiation_state = constants.VNF_NOT_INSTANTIATED
            return vnf_info

        vnf_info.vnf_instance_name = str(vnf_instance_dict['vnf-instance']['inst_name'])
        vnf_info.vnf_product_name = str(vnf_instance_dict['vnf-instance']['inst_name'])

        # TODO: add logic for all states
        vnf_info.instantiation_state = constants.VNF_INSTANTIATED
        vnf_info.vnfd_id = str(vnf_instance_dict['vnf-instance']['vnf_id'])

        vnf_info.instantiated_vnf_info = InstantiatedVnfInfo()
        if vnf_instance_dict['vnf-instance']['state']['oper_state'] == 'ACTIVE':
            vnf_info.instantiated_vnf_info.vnf_state = constants.VNF_STARTED
        else:
            vnf_info.instantiated_vnf_info.vnf_state = constants.VNF_STOPPED

        vnf_info.instantiated_vnf_info.vnfc_resource_info = list()
        for vnfc_id, vnfc_details in vnf_instance_dict['vnf-instance']['vnfc_instance_list'].items():
            vnfc_resource_info = VnfcResourceInfo()
            vnfc_resource_info.vnfc_instance_id = str(vnfc_details['vnfc_id'])
            vnfc_resource_info.vdu_id = str(vnfc_details['vi_resources']['vdu_id'])

            vnfc_resource_info.compute_resource = ResourceHandle()
            vnfc_resource_info.compute_resource.vim_id = str(vnfc_details['vi_resources']['vi_descriptor']['virp_id'])
            vnfc_resource_info.compute_resource.resource_id = str(vnfc_details['vi_resources']['vi_descriptor']
                                                                  ['vi_resources']['mgmt_objects']['OPENSTACK_SERVER'])
            vnf_info.instantiated_vnf_info.vnfc_resource_info.append(vnfc_resource_info)

        return vnf_info

    @log_entry_exit(LOG)
    def get_vim_helper(self, vim_id):
        response = requests.get(url=self.endpoint_url + '/nfv/vi/virp/%s' % vim_id)
        assert response.status_code == 200

        generic_vim = response.json()
        generic_vim_type = generic_vim['virp']['vi_plugin_id']
        generic_vim_location = generic_vim['virp']['location']

        if generic_vim_type == 'OPENSTACK':
            vim_params = self.get_openstack_vim_params(location=generic_vim_location)
            vim_vendor='openstack'
        else:
            raise SdlManoAdapterError('Unsupported VIM type: %s' % generic_vim_type)

        return construct_adapter(vendor=vim_vendor, module_type='vim', **vim_params)

    @log_entry_exit(LOG)
    def get_openstack_vim_params(self, location):
        response = requests.get(url=self.endpoint_url + '/nfv/vi/openstack')
        assert response.status_code == 200

        openstack_vim_list = response.json()['openstack']
        for openstack_vim in openstack_vim_list:
            auth_url = openstack_vim['auth_url']
            username = openstack_vim['username']
            password = openstack_vim['password']
            project_name = openstack_vim['project_name']

            if location == '%s/%s@%s' % (auth_url, username, project_name):

                # TODO: temporary workaround for DNAT
                auth_url = 'http://10.2.16.50:35357'

                return {
                    'auth_url': auth_url,
                    'username': username,
                    'password': password,
                    'project_name': project_name
                }


    @log_entry_exit(LOG)
    def ns_terminate(self, ns_instance_id, terminate_time=None):
        ns_update_dict = self.ns_update_json_mapping[ns_instance_id]
        ns_update_dict['is_enabled'] = False

        response = requests.put(url=self.endpoint_url + '/nfv_network_service/%s' % ns_instance_id, json=ns_update_dict)
        assert response.status_code == 200

        return 'ns_terminate', ns_instance_id

    @log_entry_exit(LOG)
    def ns_delete_id(self, ns_instance_id):
        response = requests.delete(url=self.endpoint_url + '/nfv_network_service/%s' % ns_instance_id)
        assert response.status_code == 200

        self.ns_nsd_mapping.pop(ns_instance_id)

    @log_entry_exit(LOG)
    def wait_for_ns_stable_state(self, ns_instance_id, max_wait_time, poll_interval):
        stable_states = ['running', 'failed', 'disabled']
        elapsed_time = 0

        while elapsed_time < max_wait_time:
            try:
                response = requests.get(url=self.endpoint_url + '/nfv_network_service/%s' % ns_instance_id)
                assert response.status_code == 200
                ns_instance_dict = response.json()
                ns_status = ns_instance_dict['state']
            except Exception as e:
                raise SdlManoAdapterError(e.message)
            LOG.debug('Got NS status %s for NS with ID %s' % (ns_status, ns_instance_id))
            if ns_status in stable_states:
                return True
            else:
                LOG.debug('Expected NS status to be one of %s, got %s' % (stable_states, ns_status))
                LOG.debug('Sleeping %s seconds' % poll_interval)
                time.sleep(poll_interval)
                elapsed_time += poll_interval
                LOG.debug('Elapsed time %s seconds out of %s' % (elapsed_time, max_wait_time))

        LOG.debug('NS with ID %s did not reach a stable state after %s' % (ns_instance_id, max_wait_time))
        return False

    @log_entry_exit(LOG)
    def verify_vnf_sw_images(self, vnf_info):
        vnfd_id = vnf_info.vnfd_id
        vnfd = self.get_vnfd(vnfd_id)

        # TODO: optimize by creating a VDU - image mapping by passing through the VNFD a single time

        for vnfc_resource_info in vnf_info.instantiated_vnf_info.vnfc_resource_info:
            # Get list of possible image names from the VNFD for the VDU ID of the current VNFC
            vdu_id = vnfc_resource_info.vdu_id
            sw_object_list = []
            for vi_resource in vnfd['vnf']['vdu_list'][vdu_id]['vi_resources'].values():
                for storage_list in vi_resource['storage_list'].values():
                    sw_object_list += storage_list['sw_objects']

            vim_id = vnfc_resource_info.compute_resource.vim_id
            vim = self.get_vim_helper(vim_id)
            resource_id = vnfc_resource_info.compute_resource.resource_id
            virtual_compute = vim.query_virtualised_compute_resource(filter={'compute_id': resource_id})
            image_id = virtual_compute.vc_image_id
            image_details = vim.query_image(image_id)
            image_name_vim = image_details.name

            if image_name_vim not in sw_object_list:
                LOG.debug('Unexpected image for VNFC %s, VDU type %s' % (resource_id, vdu_id))
                LOG.debug('Expected images: %s; actual image name: %s' % (sw_object_list, image_name_vim))
                return False

        return True

    @log_entry_exit(LOG)
    def get_vnfd(self, vnfd):
        response = requests.get(url=self.endpoint_url + '/nfv/vnf/vnf/%s' % vnfd)
        assert response.status_code == 200

        return response.json()

    @log_entry_exit(LOG)
    def validate_ns_allocated_vresources(self, ns_instance_id, additional_param=None):
        ns_info = self.ns_query(filter={'ns_instance_id': ns_instance_id})
        for vnf_info in ns_info.vnf_info:
            if not self.validate_vnf_allocated_vresources(vnf_info):
                return False
        return True

    @log_entry_exit(LOG)
    def validate_vnf_allocated_vresources(self, vnf_info):
        validation_result = True

        vnfd_id = vnf_info.vnfd_id
        vnfd = self.get_vnfd(vnfd_id)

        for vnfc_resource_info in vnf_info.instantiated_vnf_info.vnfc_resource_info:
            vdu_id = vnfc_resource_info.vdu_id

            # Get possible values for vResources
            expected_cpu_count_list = []
            for vi_resource in vnfd['vnf']['vdu_list'][vdu_id]['vi_resources'].values():
                for cpu_list in vi_resource['cpu_list'].values():
                    expected_cpu_count_list.append(cpu_list['amount'])

            expected_memory_size_list = []
            for vi_resource in vnfd['vnf']['vdu_list'][vdu_id]['vi_resources'].values():
                for memory_list in vi_resource['memory_list'].values():
                    expected_memory_size_list.append(memory_list['amount'])

            LOG.debug('Not checking vStorage size, because it is not stated in the VNFD')

            expected_nic_count_list = []
            for vi_resource in vnfd['vnf']['vdu_list'][vdu_id]['vi_resources'].values():
                expected_nic_count_list.append(len(vi_resource['intf_list']))

            # Get VIM adapter object
            vim = self.get_vim_helper(vnfc_resource_info.compute_resource.vim_id)

            resource_id = vnfc_resource_info.compute_resource.resource_id
            virtual_compute = vim.query_virtualised_compute_resource(filter={'compute_id': resource_id})
            actual_cpu_count = virtual_compute.virtual_cpu.num_virtual_cpu
            actual_memory_size = virtual_compute.virtual_memory.virtual_mem_size
            actual_nic_count = len(virtual_compute.virtual_network_interface)

            if actual_cpu_count not in expected_cpu_count_list:
                LOG.debug('Unexpected CPU count for VDU %s: %s. Expected values: %s' % (
                    vdu_id, actual_cpu_count, expected_cpu_count_list))
                validation_result = False

            if actual_memory_size not in expected_memory_size_list:
                LOG.debug('Unexpected memory size for VDU %s: %s. Expected values: %s' % (
                    vdu_id, actual_memory_size, expected_memory_size_list))

                # TODO: Clarify memory size in VNFD. Until then, do not set validation_result
                # validation_result = False

            if actual_nic_count not in expected_nic_count_list:
                LOG.debug('Unexpected memory size for VDU %s: %s. Expected values: %s' % (
                    vdu_id, actual_nic_count, expected_nic_count_list))
                validation_result = False

        return validation_result

    @log_entry_exit(LOG)
    def verify_vnf_nsd_mapping(self, ns_instance_id, additional_param=None):
        validation_result = True

        ns_info = self.ns_query(filter={'ns_instance_id': ns_instance_id, 'additional_param': additional_param})
        nsd_id = ns_info.nsd_id
        nsd = self.get_nsd(nsd_id)

        service_name_type_mapping = dict()
        for service_desc in nsd['service_desc_list']:
            service_name_type_mapping[service_desc['name']] = service_desc['service_type']

        for vnf_info in ns_info.vnf_info:
            # Get the VNF product name
            vnf_name = vnf_info.vnf_product_name
            vnfd_id = vnf_info.vnfd_id
            vnfd = self.get_vnfd(vnfd_id)

            vnfd_service_type = vnfd['vnf']['service_type']
            nsd_service_type = service_name_type_mapping[vnf_name]

            if vnfd_service_type != nsd_service_type:
                LOG.debug('Unexpected VNFD %s, having service type %s for VNF %s. Expecting a VNFD with service type %s'
                          % (vnfd_id, vnfd_service_type, vnf_name, nsd_service_type))
                validation_result = False

        return validation_result
