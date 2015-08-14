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

import neutron.db.db_base_plugin_v2 as db_base_plugin_v2
import neutron.db.ip_usage_db as usage_db


class IpUsagePlugin(usage_db.IpUsageMixin,
                    db_base_plugin_v2.NeutronDbPluginV2):
    """This plugin exposes IP usage data for networks and subnets."""
    _instance = None

    supported_extension_aliases = ["network-ip-usage"]

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_plugin_description(self):
        return "Provides IP usage data for each network and subnet."

    def get_plugin_type(self):
        return "network-ip-usage"

    def get_network_ip_usages(self, context, filters=None, fields=None):
        """Returns ip usage data for a collection of networks."""
        return self.get_network_ip_allocations(context, filters)

    def get_network_ip_usage(self, context, id, fields=None):
        """Return ip usage data for a specific network id."""
        filters = {'network_id': id}
        result = self.get_network_ip_allocations(context, filters)
        return result[0] if result else []
