# Copyright 2015 GoDaddy.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
#  implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import oslo_log.log as logging

import neutron.api.extensions as extensions
import neutron.api.v2.attributes as attributes
import neutron.api.v2.base as base
import neutron.common.constants as constants
from neutron.i18n import _
import neutron.services.network_ip_usage.plugin as plugin

LOG = logging.getLogger(__name__)

RESOURCE_NAME = "network_ip_usage"
RESOURCE_PLURAL = "%ss" % RESOURCE_NAME
COLLECTION_NAME = RESOURCE_PLURAL.replace('_', '-')
EXT_ALIAS = RESOURCE_NAME.replace('_', '-')

RESOURCE_ATTRIBUTE_MAP = {
    RESOURCE_PLURAL: {
        'name': {'allow_post': False, 'allow_put': False,
                 'is_visible': True},
        'id': {'allow_post': False, 'allow_put': False,
               'is_visible': True},
        'total_ips': {'allow_post': False, 'allow_put': False,
                      'is_visible': True},
        'used_ips': {'allow_post': False, 'allow_put': False,
                     'is_visible': True},
        'subnet_ip_allocations': {'allow_post': False, 'allow_put': False,
                                  'is_visible': True},
        'ip_version': {'allow_post': False, 'allow_put': False,
                       'convert_to': attributes.convert_to_int,
                       'validate': {'type:values': [constants.IP_VERSION_4,
                                                    constants.IP_VERSION_6]},
                       'is_visible': True},
        'network_id': {'allow_post': False, 'allow_put': False,
                       'validate': {'type:uuid': None},
                       'is_visible': True}},
        'network_name': {'allow_post': True, 'allow_put': True, 'default': '',
                         'validate': {'type:string': attributes.NAME_MAX_LEN},
                         'is_visible': True},
}


class Network_ip_usage(extensions.ExtensionDescriptor):
    """Extension class supporting network ip usage information."""

    @classmethod
    def get_name(cls):
        return _("Network IP Usage")

    @classmethod
    def get_alias(cls):
        return EXT_ALIAS

    @classmethod
    def get_description(cls):
        return _("Provides IP usage data for each network and subnet.")

    @classmethod
    def get_updated(cls):
        return "2015-09-24T00:00:00-00:00"

    @classmethod
    def get_resources(cls):
        """Returns Extended Resource for service type management."""
        plural = {RESOURCE_PLURAL: RESOURCE_NAME}
        attributes.PLURALS.update(dict(plural))
        resource_attributes = RESOURCE_ATTRIBUTE_MAP[RESOURCE_PLURAL]
        controller = base.create_resource(
            RESOURCE_PLURAL,
            RESOURCE_NAME,
            plugin.IpUsagePlugin.get_instance(),
            resource_attributes)
        return [extensions.ResourceExtension(COLLECTION_NAME,
                                             controller,
                                             attr_map=resource_attributes)]

    def get_extended_resources(self, version):
        if version == "2.0":
            return RESOURCE_ATTRIBUTE_MAP
        else:
            return {}
