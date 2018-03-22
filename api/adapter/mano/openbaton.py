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
import time

import requests

from requests.auth import HTTPBasicAuth
from api.adapter import construct_adapter
from api.adapter.mano import ManoAdapterError
from api.generic import constants
from api.structures.objects import ResourceHandle, InstantiatedVnfInfo, NsInfo, VnfInfo, VnfExtCpInfo, VnfcResourceInfo
from utils.logging_module import log_entry_exit
import json

# Instantiate logger
LOG = logging.getLogger(__name__)


class OpenbatonManoAdapterError(ManoAdapterError):
    """
    A problem occurred in the VNF LifeCycle Validation Openbaton MANO adapter API.
    """
    pass


class OpenbatonManoAdapterUnauthorized(Exception):
    """
    Openbaton access token not valid.
    """
    pass


class OpenbatonManoAdapter(object):
    def __init__(self, api_url, username, password, project):
        self.api_url = api_url
        self.username = username
        self.password = password
        self.project = project
        self.session = requests.Session()
        self.token = self.get_token(username, password)
        self.session.headers = {
            'Content-Type': 'application/json',
            'project-id': self.project,
            'Authorization': self.token
        }
        self.vnf_to_ns_mapping = dict()

    @log_entry_exit(LOG)
    def get_token(self, username, password):
        http_headers = {
            "Accept": "application/json",
        }
        body = (('username', username), ('password', password), ('grant_type', 'password'))
        try:
            response = requests.post(url=self.api_url + '/oauth/token',
                                     auth=HTTPBasicAuth('openbatonOSClient', 'secret'),
                                     data=body, headers=http_headers, verify=False)
            assert response.status_code == 200
        except Exception as e:
            LOG.debug(e)
            raise OpenbatonManoAdapterError('Unable to fetch Authorization token from %s' %
                                            self.api_url + '/oauth/token')
        token = str('Bearer ' + response.json()['access_token'])
        return token

    @log_entry_exit(LOG)
    def do_request(self, url, method, **kwargs):
        # Perform the request once. If we get a 401 back then it might be because the auth token expired, so try to
        # re-authenticate and try again. If it still fails, bail.
        try:
            kwargs.setdefault('data', {})
            kwargs.setdefault('verify', False)
            resp, body = self._do_request(self.api_url + url, method, **kwargs)
        except OpenbatonManoAdapterUnauthorized:
            self.token = self.get_token(self.username, self.password)
            self.session.headers['Authorization'] = self.token
            resp, body = self._do_request(self.api_url + url, method, **kwargs)
        return resp, body

    @log_entry_exit(LOG)
    def _do_request(self, url, method, **kwargs):
        data = kwargs.pop('data', {})
        verify = kwargs.pop('verify', False)
        try:
            resp = self.session.request(url=url, method=method, data=data, verify=verify)
            body = json.loads(resp.text)
        except ValueError:
            body = {}
        except Exception as e:
            LOG.exception(e)
            raise OpenbatonManoAdapterError('Unable to run request on %s, method %s. Reason: %s' % (url, method, e))
        if resp.status_code == 401:
            raise OpenbatonManoAdapterUnauthorized("Access token %s is invalid" % self.token)
        return resp, body

    @log_entry_exit(LOG)
    def ns_create_id(self, nsd_id, ns_name, ns_description):
        url = '/api/v1/ns-records/%s' % nsd_id
        try:
            resp, body = self.do_request(url=url, method='post')
            assert resp.status_code == 201
            ns_instance_id = str(body.get('id', ''))
        except Exception as e:
            LOG.exception(e)
            raise OpenbatonManoAdapterError('Unable to instantantiate NS for NSD ID %s. Reason: %s. '
                                            % (nsd_id, e.message))
        return ns_instance_id

    @log_entry_exit(LOG)
    def ns_instantiate(self, ns_instance_id, flavour_id, sap_data=None, pnf_info=None, vnf_instance_data=None,
                       nested_ns_instance_data=None, location_constraints=None, additional_param_for_ns=None,
                       additional_param_for_vnf=None, start_time=None, ns_instantiation_level_id=None,
                       additional_affinity_or_anti_affinity_rule=None):
        LOG.debug('"NS Instantiate" operation is not implemented in Openbaton!')
        LOG.debug('Instead of "Lifecycle Operation Occurrence Id", will just return the "NS Instance Id"')
        return 'ns_instantiate', ns_instance_id

    @log_entry_exit(LOG)
    def get_operation_status(self, lifecycle_operation_occurrence_id):
        """
        This function does not have a direct mapping in Openbaton so it will just return the status of the
        specified resource type with given ID.
        """
        LOG.debug('"Lifecycle Operation Occurrence Id" is not implemented in Openbaton!')
        LOG.debug('Will return the state of the resource with given Id')

        if lifecycle_operation_occurrence_id is None:
            raise OpenbatonManoAdapterError('Lifecycle Operation Occurrence ID is absent')
        else:
            operation_type, resource_id = lifecycle_operation_occurrence_id

        if operation_type == 'ns_instantiate':
            url = '/api/v1/ns-records/%s' % resource_id
            try:
                resp, ns_config = self.do_request(url=url, method='get')
                ns_status = str(ns_config.get('status', ''))
            except Exception as e:
                LOG.exception(e)
                raise OpenbatonManoAdapterError('Unable to retrieve status for NS ID %s. Reason: %s' %
                                                (resource_id, e.message))
            if ns_status == 'ACTIVE':
                for vnfr in ns_config.get('vnfr', []):
                    self.vnf_to_ns_mapping[str(vnfr.get('id', ''))] = resource_id
                return constants.OPERATION_SUCCESS
            elif ns_status == 'ERROR':
                return constants.OPERATION_FAILED
            else:
                return constants.OPERATION_PENDING

        if operation_type == 'ns_terminate':
            url = '/api/v1/ns-records/%s' % resource_id
            try:
                resp, ns_config = self.do_request(url=url, method='get')
                if resp.status_code == 404:
                    self.vnf_to_ns_mapping = {k:v for k, v in self.vnf_to_ns_mapping.items() if v != resource_id}
                    return constants.OPERATION_SUCCESS
                assert resp.status_code == 200
                ns_status = str(ns_config.get('status', ''))
            except Exception as e:
                LOG.exception(e)
                raise OpenbatonManoAdapterError('Unable to get status for NS %s' % resource_id)

            if ns_status == 'ERROR':
                return constants.OPERATION_FAILED
            else:
                return constants.OPERATION_PENDING

    @log_entry_exit(LOG)
    def ns_query(self, filter, attribute_selector=None):
        ns_instance_id = filter['ns_instance_id']
        ns_info = NsInfo()
        ns_info.ns_instance_id = ns_instance_id
        try:
            url = '/api/v1/ns-records/%s' % ns_instance_id
            resp, ns_config = self.do_request(url=url, method='get')
            if resp.status_code == 404:
                # ns-instance-id not found, so assuming NOT_INSTANTIATED
                ns_info.ns_state = constants.NS_NOT_INSTANTIATED
                return ns_info
            assert resp.status_code == 200
        except Exception as e:
            LOG.exception(e)
            raise OpenbatonManoAdapterError('Unable to retrieve status for NS ID %s. Reason: %s' %
                                            (ns_instance_id, e.message))
        ns_info.nsd_id = str(ns_config.get('descriptor_reference', ''))
        if ns_config.get('status') == 'ACTIVE':
            ns_info.ns_state = constants.NS_INSTANTIATED
        else:
            ns_info.ns_state = constants.NS_NOT_INSTANTIATED
        ns_info.vnf_info = list()
        for constituent_vnfr in ns_config.get('vnfr', []):
            vnf_info = VnfInfo()
            vnf_info.vnf_instance_id = str(constituent_vnfr.get('id', ''))
            if constituent_vnfr.get('status', '') not in ['ACTIVE', 'INACTIVE']:
                vnf_info.instantiation_state = constants.VNF_NOT_INSTANTIATED
                ns_info.vnf_info.append(vnf_info)
                continue
            vnf_info.instantiation_state = constants.VNF_INSTANTIATED
            vnf_info.vnfd_id = str(constituent_vnfr.get('descriptor_reference', ''))
            vnf_info.vnf_instance_name = str(constituent_vnfr.get('name', ''))
            vnf_info.vnf_product_name = str(constituent_vnfr.get('type', ''))
            vnf_info.instantiated_vnf_info = InstantiatedVnfInfo()
            vnf_info.instantiated_vnf_info.vnf_state = \
                constants.VNF_STATE['OPENBATON_DEPLOYMENT_STATE'][constituent_vnfr.get('status')]
            vnf_info.instantiated_vnf_info.vnfc_resource_info = list()
            vnf_info.instantiated_vnf_info.ext_cp_info = list()
            for vdu in constituent_vnfr.get('vdu', []):
                for vnfc_instance in vdu.get('vnfc_instance', []):
                    vnfc_resource_info = VnfcResourceInfo()
                    vnfc_resource_info.vnfc_instance_id = str(vnfc_instance.get('id', ''))
                    vnfc_resource_info.vdu_id = str(vdu.get('parent_vdu', ''))
                    vnfc_resource_info.compute_resource = ResourceHandle()
                    vnfc_resource_info.compute_resource.vim_id = str(vnfc_instance.get('vim_id', ''))
                    vnfc_resource_info.compute_resource.resource_id = str(vnfc_instance.get('vc_id', ''))
                    vnf_info.instantiated_vnf_info.vnfc_resource_info.append(vnfc_resource_info)
                    for ext_cp in vnfc_instance.get('vnfComponent', {}).get('connection_point', []):
                        vnf_ext_cp_info = VnfExtCpInfo()
                        port_name = 'VNFD-' + str(ext_cp.get('id', ''))
                        vnf_ext_cp_info.cp_instance_id, vnf_ext_cp_info.address = self.get_cp_info(
                            port_name=port_name, vim_id=str(vnfc_instance.get('vim_id', '')))
                        virtual_link_reference = str(ext_cp.get('virtual_link_reference', ''))
                        # TODO Replace this with the ID of the virtual-link from VNFD
                        vnf_ext_cp_info.cpd_id = virtual_link_reference
                        vnf_info.instantiated_vnf_info.ext_cp_info.append(vnf_ext_cp_info)
            ns_info.vnf_info.append(vnf_info)
        return ns_info

    @log_entry_exit(LOG)
    def vnf_query(self, filter, attribute_selector=None):
        vnf_instance_id = filter['vnf_instance_id']
        vnf_info = VnfInfo()
        vnf_info.vnf_instance_id = vnf_instance_id
        ns_instance_id = self.vnf_to_ns_mapping.get(vnf_instance_id, '')
        try:
            url = '/api/v1/ns-records/%s/vnfrecords/%s' % (ns_instance_id, vnf_instance_id)
            resp, vnf_config = self.do_request(url=url, method='get')
            if resp.status_code == 400:
                # vnf-instance-id not found, so assuming NOT_INSTANTIATED
                vnf_info.instantiation_state = constants.VNF_NOT_INSTANTIATED
                return vnf_info
        except Exception as e:
            LOG.exception(e)
            raise OpenbatonManoAdapterError('Unable to retrieve status for VNF with ID %s. Reason: %s' %
                                            (vnf_instance_id, e.message))
        vnf_info.vnf_instance_id = str(vnf_config.get('id', ''))
        if vnf_config.get('status', '') not in ['ACTIVE', 'INACTIVE']:
            vnf_info.instantiation_state = constants.VNF_NOT_INSTANTIATED
            return vnf_info
        vnf_info.instantiation_state = constants.VNF_INSTANTIATED
        vnf_info.vnfd_id = str(vnf_config.get('descriptor_reference', ''))
        vnf_info.vnf_instance_name = str(vnf_config.get('name', ''))
        vnf_info.vnf_product_name = str(vnf_config.get('type', ''))
        vnf_info.instantiated_vnf_info = InstantiatedVnfInfo()
        vnf_info.instantiated_vnf_info.vnf_state = \
            constants.VNF_STATE['OPENBATON_DEPLOYMENT_STATE'][vnf_config.get('status')]
        vnf_info.instantiated_vnf_info.vnfc_resource_info = list()
        vnf_info.instantiated_vnf_info.ext_cp_info = list()
        for vdu in vnf_config.get('vdu', []):
            for vnfc_instance in vdu.get('vnfc_instance', []):
                vnfc_resource_info = VnfcResourceInfo()
                vnfc_resource_info.vnfc_instance_id = str(vnfc_instance.get('id', ''))
                vnfc_resource_info.vdu_id = str(vdu.get('id', ''))
                vnfc_resource_info.compute_resource = ResourceHandle()
                vnfc_resource_info.compute_resource.vim_id = str(vnfc_instance.get('vim_id', ''))
                vnfc_resource_info.compute_resource.resource_id = str(vnfc_instance.get('vc_id', ''))
                vnf_info.instantiated_vnf_info.vnfc_resource_info.append(vnfc_resource_info)
                for ext_cp in vnfc_instance.get('vnfComponent', {}).get('connection_point', []):
                    vnf_ext_cp_info = VnfExtCpInfo()
                    port_name = 'VNFD-' + str(ext_cp.get('id', ''))
                    vnf_ext_cp_info.cp_instance_id, vnf_ext_cp_info.address = self.get_cp_info(
                        port_name=port_name, vim_id=str(vnfc_instance.get('vim_id', '')))
                    virtual_link_reference = str(ext_cp.get('virtual_link_reference', ''))
                    # TODO Replace this with the ID of the virtual-link from VNFD
                    vnf_ext_cp_info.cpd_id = virtual_link_reference
                    vnf_info.instantiated_vnf_info.ext_cp_info.append(vnf_ext_cp_info)
        return vnf_info

    @log_entry_exit(LOG)
    def get_vim_helper(self, vim_id):
        url = '/api/v1/datacenters/%s' % vim_id
        try:
            resp, vim_config = self.do_request(url=url, method='get')
            assert resp.status_code == 200
        except Exception as e:
            LOG.exception(e)
            raise OpenbatonManoAdapterError('Unable to retrieve config for VIM with ID %s. Reason: %s' %
                                            (vim_id, e.message))
        if vim_config.get('type', '') == 'openstack':
            vim_vendor = 'openstack'
            vim_params = {
                'auth_url': vim_config.get('authUrl', ''),
                'username': vim_config.get('username', ''),
                # 'password': vim_config.get('password'),
                'password': 'admin',
                'project_domain_name': 'default',
                'project_name': 'admin',
                'user_domain_name': 'default'
            }
        else:
            raise OpenbatonManoAdapterError('Unsupported VIM type: %s' % vim_config.get('type', ''))

        return construct_adapter(vendor=vim_vendor, module_type='vim', **vim_params)

    @log_entry_exit(LOG)
    def ns_terminate(self, ns_instance_id, terminate_time=None, additional_param=None):
        url = '/api/v1/ns-records/%s' % ns_instance_id
        try:
            resp, ns_term = self.do_request(url=url, method='delete')
            assert resp.status_code == 204
        except Exception as e:
            LOG.exception(e)
            raise OpenbatonManoAdapterError('Unable to terminate NS instance ID %s. Reason: %s' %
                                            (ns_instance_id, e.message))

        return 'ns_terminate', ns_instance_id

    @log_entry_exit(LOG)
    def ns_delete_id(self, ns_instance_id):
        LOG.debug('"NS Delete ID" operation is not implemented in Openbaton!')

    @log_entry_exit(LOG)
    def wait_for_ns_stable_state(self, ns_instance_id, max_wait_time, poll_interval):
        if ns_instance_id is None:
            raise OpenbatonManoAdapterError('NS instance ID is absent')
        stable_states = ['ACTIVE', 'INACTIVE', 'ERROR', 'NOTFOUND']
        elapsed_time = 0

        while elapsed_time < max_wait_time:
            url = '/api/v1/ns-records/%s' % ns_instance_id
            try:
                resp, ns_config = self.do_request(url=url, method='get')
                ns_status = ns_config.get('status', 'NOTFOUND')
                if ns_status in stable_states:
                    return True
                else:
                    LOG.debug('Expected NS status to be one of %s, got %s' % (stable_states, ns_status))
                    LOG.debug('Sleeping %s seconds' % poll_interval)
                    time.sleep(poll_interval)
                    elapsed_time += poll_interval
                    LOG.debug('Elapsed time %s seconds out of %s' % (elapsed_time, max_wait_time))
            except Exception as e:
                LOG.debug('Could not retrieve status for NS with ID %s' %  ns_instance_id)
                raise OpenbatonManoAdapterError(e.message)
        LOG.debug('NS with ID %s did not reach a stable state after %s' % (ns_instance_id, max_wait_time))
        return False

    @log_entry_exit(LOG)
    def get_vnfd(self, vnfd_id):
        url = '/api/v1/vnf-descriptors/%s' % vnfd_id
        try:
            resp, vnfd = self.do_request(url=url, method='get')
            assert resp.status_code == 200
        except Exception as e:
            LOG.exception(e)
            raise OpenbatonManoAdapterError('Unable to retrieve config for VNFD with ID %s. Reason: %s' %
                                            (vnfd_id, e.message))
        return vnfd

    @log_entry_exit(LOG)
    def verify_vnf_sw_images(self, vnf_info, additional_param=None):
        vnfd_id = vnf_info.vnfd_id
        vnfd = self.get_vnfd(vnfd_id)

        expected_vdu_images = {}
        for vdu in vnfd.get('vdu', []):
            expected_vdu_images[vdu.get('id', '')] = vdu.get('vm_image', '')

        for vnfc_resource_info in vnf_info.instantiated_vnf_info.vnfc_resource_info:
            vdu_id = vnfc_resource_info.vdu_id

            vim_id = vnfc_resource_info.compute_resource.vim_id
            vim = self.get_vim_helper(vim_id)
            resource_id = vnfc_resource_info.compute_resource.resource_id
            virtual_compute = vim.query_virtualised_compute_resource(filter={'compute_id': resource_id})
            image_id = virtual_compute.vc_image_id
            image_details = vim.query_image(image_id)
            image_name_vim = image_details.name

            image_name_vnfd = expected_vdu_images[vdu_id]
            if image_name_vim not in image_name_vnfd:
                LOG.debug('Unexpected image for VNFC %s, VDU type %s' % (resource_id, vdu_id))
                LOG.debug('Expected image name: %s; actual image name: %s' % (image_name_vnfd, image_name_vim))
                return False

        return True

    # TODO This function is already in api.mano.generic in the master branch. To be deleted before merge in master.
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

        expected_vdu_flavours = {}
        for vdu in vnfd.get('vdu', []):
            vdu_id = str(vdu.get('id', ''))
            expected_vdu_flavours[vdu_id] = list()
            if vdu.get('computation_requirement') is not None:
                vdu_flavour = str(vdu.get('computation_requirement', ''))
                expected_vdu_flavours[vdu_id].append(vdu_flavour)
            else:
                for flavour in vnfd.get('deployment_flavour', []):
                    vdu_flavour = str(flavour.get('flavour_key', ''))
                    expected_vdu_flavours[vdu_id].append(vdu_flavour)

        for vnfc_resource_info in vnf_info.instantiated_vnf_info.vnfc_resource_info:
            vdu_id = vnfc_resource_info.vdu_id

            # Get VIM adapter object
            vim = self.get_vim_helper(vnfc_resource_info.compute_resource.vim_id)

            server_id = vnfc_resource_info.compute_resource.resource_id
            server_details = vim.server_get(server_id)
            server_flavour_id = server_details['flavor_id']
            flavour_details = vim.flavor_get(server_flavour_id)
            flavour_name_nova = str(flavour_details['name'])
            if flavour_name_nova not in expected_vdu_flavours.get(vdu_id, []):
                validation_result = False

        return validation_result

    @log_entry_exit(LOG)
    def verify_vnf_nsd_mapping(self, ns_instance_id, additional_param=None):
        ns_info = self.ns_query(filter={'ns_instance_id': ns_instance_id, 'additional_param': additional_param})
        nsd_id = ns_info.nsd_id
        nsd = self.get_nsd(nsd_id)
        expected_vnf_vnfd_mapping = dict()
        for vnfd in nsd.get('vnfd', []):
            vnf_product_name = str(vnfd.get('type', ''))
            expected_vnf_vnfd_mapping[vnf_product_name] = str(vnfd.get('id', ''))

        for vnf_info in ns_info.vnf_info:
            vnf_product_name = vnf_info.vnf_product_name
            if vnf_info.vnfd_id != expected_vnf_vnfd_mapping[vnf_product_name]:
                return False

        return True

    @log_entry_exit(LOG)
    def get_nsd(self, nsd_id):
        url = '/api/v1/ns-descriptors/%s' % nsd_id
        try:
            resp, nsd = self.do_request(url=url, method='get')
            assert resp.status_code == 200
        except Exception as e:
            LOG.exception(e)
            raise OpenbatonManoAdapterError('Unable to retrieve config for NSD with ID %s. Reason: %s' %
                                            (nsd_id, e.message))
        return nsd

    @log_entry_exit(LOG)
    def get_vnf_mgmt_addr_list(self, vnf_instance_id, additional_param=None):
        ns_instance_id = self.vnf_to_ns_mapping.get(vnf_instance_id)
        url = '/api/v1/ns-records/%s/vnfrecords/%s' % (ns_instance_id, vnf_instance_id)
        try:
            resp, vnf_config = self.do_request(url=url, method='get')
            assert resp.status_code == 200
        except Exception as e:
            LOG.exception(e)
            raise OpenbatonManoAdapterError('Unable to retrieve config for VNF with ID %s. Reason: %s' %
                                            (vnf_instance_id, e.message))
        mgmt_addr_list = [str(addr) for addr in vnf_config.get('vnf_address', [])]

        return mgmt_addr_list

    @log_entry_exit(LOG)
    def get_cp_info(self, port_name, vim_id):
        vim = self.get_vim_helper(vim_id)
        port_dict = vim.port_list(name=port_name)
        for port in port_dict:
            port_info = port.get('ports', [])
            if len(port_info) == 0:
                LOG.debug('Could not find port with name %s in VIM' % port_name)
                raise OpenbatonManoAdapterError('Could not find port with name %s in VIM' % port_name)
            port_id = str(port_info[0].get('id'))
            mac_address = [str(port_info[0].get('mac_address'))]
        return port_id, mac_address

