import importlib

from api import ApiError
from api.adapter.constructors import get_vendor_constructor_mapping


class ApiAdapterError(ApiError):
    """
    A problem occurred in the VNF LifeCycle Validation adapter API.
    """
    pass


def construct_adapter(vendor, module_type, **kwargs):
    """
    This function fetches the adapter constructor for the specified vendor and module type.

    :param vendor:      The name of the vendor of the module. Ex "openstack"
    :param module_type: The module type for which to fetch the constructor. Ex. "vnfm"
    :param kwargs:      Additional key-value pairs.
    :return:            The constructor for the specified vendor and module type.
    """
    vendor_constructor_mapping = get_vendor_constructor_mapping()
    if module_type not in vendor_constructor_mapping:
        raise ApiAdapterError('Unable to find module %s for vendor "%s"' % (module_type, vendor))

    if vendor not in vendor_constructor_mapping[module_type]:
        raise ApiAdapterError('Unable to find constructor for vendor "%s"' % vendor)

    module_name, constructor_name = vendor_constructor_mapping[module_type][vendor].rsplit('.', 1)

    try:
        module = importlib.import_module(module_name)
    except ImportError:
        raise ApiAdapterError('Unable to import module %s' % module_name)

    try:
        constructor = getattr(module, constructor_name)
    except AttributeError:
        raise ApiAdapterError('Unable to find constructor %s in module %s' % (constructor_name, module_name))

    return constructor(**kwargs)
