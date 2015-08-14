# Copyright 2015 GoDaddy.
#
# Licensed under the Apache License, Version 2.0 (the "License");
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

import neutron.api.extensions as api_ext
import neutron.common.config as config
import neutron.common.constants as constants
import neutron.extensions
import neutron.services.network_ip_usage.plugin as plugin
import neutron.tests.unit.db.test_db_base_plugin_v2 as test_db_base_plugin_v2

API_RESOURCE = 'network-ip-usages'
USAGE_KEY = 'network_ip_usage'
USAGES_KEY = '%ss' % USAGE_KEY
EXTENSIONS_PATH = ':'.join(neutron.extensions.__path__)
PLUGIN_NAME = '%s.%s' % (plugin.IpUsagePlugin.__module__,
                         plugin.IpUsagePlugin.__name__)


class TestNetworkIPUsageAPI(test_db_base_plugin_v2.NeutronDbPluginV2TestCase):
    def setUp(self):
        svc_plugins = {'plugin_name': PLUGIN_NAME}
        super(TestNetworkIPUsageAPI, self).setUp(service_plugins=svc_plugins)
        self.plugin = plugin.IpUsagePlugin()
        ext_mgr = api_ext.PluginAwareExtensionManager(
            EXTENSIONS_PATH,
            {"network-ip-usage": self.plugin}
        )
        app = config.load_paste_app('extensions_test_app')
        self.ext_api = api_ext.ExtensionMiddleware(app, ext_mgr=ext_mgr)

    def _validate_usage(self, network, usage, expected_used_ips,
                        expected_total_ips=253):
        self.assertEqual(network['name'], usage['name'])
        self.assertEqual(network['id'], usage['id'])
        self.assertEqual(expected_used_ips, usage['used_ips'])
        self.assertEqual(expected_total_ips, usage['total_ips'])

    def _validate_from_usages(self, usages, wrapped_network, expected_used_ips,
                              expected_total_ips=253):
        network = wrapped_network['network']
        usage = self._find_usage(usages, network['id'])
        self.assertIsNotNone(usage)
        self._validate_usage(network, usage,
                             expected_used_ips=expected_used_ips,
                             expected_total_ips=expected_total_ips)

    @staticmethod
    def _find_usage(usages, net_id):
        for usage in usages:
            if net_id == usage['id']:
                return usage
        return None

    def test_usages_basic(self):
        with self.network() as net:
            with self.subnet(network=net):
                network = net['network']
                # Get ALL
                request = self.new_list_request(API_RESOURCE)
                response = self.deserialize(self.fmt,
                                            request.get_response(self.ext_api))
                self.assertIn(USAGES_KEY, response)
                self.assertEqual(1, len(response[USAGES_KEY]))
                self._validate_from_usages(response[USAGES_KEY], net, 0)

                # Get single via id
                request = self.new_show_request(API_RESOURCE, network['id'])
                response = self.deserialize(
                    self.fmt, request.get_response(self.ext_api))
                self.assertIn(USAGE_KEY, response)
                usage = response[USAGE_KEY]
                self._validate_usage(network, usage, 0)

    def test_usages_multi_nets_subnets(self):
        with self.network(name='net1') as n1,\
                self.network(name='net2') as n2,\
                self.network(name='net3') as n3:
            # n1 should have 2 subnets, n2 should have none, n3 has 1
            with self.subnet(network=n1) as subnet1_1, \
                    self.subnet(cidr='40.0.0.0/24', network=n3) as subnet3_1:
                # Consume 3 ports n1, none n2, 2 ports on n3
                with self.port(subnet=subnet1_1),\
                        self.port(subnet=subnet1_1),\
                        self.port(subnet=subnet1_1),\
                        self.port(subnet=subnet3_1),\
                        self.port(subnet=subnet3_1):

                    # Get ALL
                    request = self.new_list_request(API_RESOURCE)
                    response = self.deserialize(
                        self.fmt, request.get_response(self.ext_api))

                    self.assertIn(USAGES_KEY, response)
                    self.assertEqual(3, len(response[USAGES_KEY]))

                    data = response[USAGES_KEY]
                    self._validate_from_usages(data, n1, 3, 253)
                    self._validate_from_usages(data, n2, 0, 0)
                    self._validate_from_usages(data, n3, 2, 253)

                    # Get single via network id
                    network = n1['network']
                    request = self.new_show_request(API_RESOURCE,
                                                    network['id'])
                    response = self.deserialize(
                        self.fmt, request.get_response(self.ext_api))
                    self.assertIn(USAGE_KEY, response)
                    self._validate_usage(network, response[USAGE_KEY], 3, 253)

    def test_usages_multi_nets_subnets_sums(self):
        with self.network(name='net1') as n1:
            # n1 has 2 subnets
            with self.subnet(network=n1) as subnet1_1, \
                    self.subnet(cidr='40.0.0.0/24', network=n1) as subnet1_2:
                # Consume 3 ports n1: 1 on subnet 1 and 2 on subnet 2
                with self.port(subnet=subnet1_1),\
                        self.port(subnet=subnet1_2),\
                        self.port(subnet=subnet1_2):
                    # Get ALL
                    request = self.new_list_request(API_RESOURCE)
                    response = self.deserialize(
                        self.fmt, request.get_response(self.ext_api))

                    self.assertIn(USAGES_KEY, response)
                    self.assertEqual(1, len(response[USAGES_KEY]))
                    self._validate_from_usages(response[USAGES_KEY], n1, 3,
                                               506)

                    # Get single via network id
                    network = n1['network']
                    request = self.new_show_request(API_RESOURCE,
                                                    network['id'])
                    response = self.deserialize(
                        self.fmt, request.get_response(self.ext_api))
                    self.assertIn(USAGE_KEY, response)
                    self._validate_usage(network, response[USAGE_KEY], 3, 506)

    def test_usages_port_consumed_v4(self):
        with self.network() as net:
            with self.subnet(network=net) as subnet:
                request = self.new_list_request(API_RESOURCE)
                # Consume 2 ports
                with self.port(subnet=subnet), self.port(subnet=subnet):
                    response = self.deserialize(self.fmt,
                                                request.get_response(
                                                    self.ext_api))
                    self._validate_from_usages(response[USAGES_KEY], net, 2)

    def test_usages_query_ip_version_v4(self):
        with self.network() as net:
            with self.subnet(network=net):
                # Get IPv4
                params = 'ip_version=4'
                request = self.new_list_request(API_RESOURCE, params=params)
                response = self.deserialize(self.fmt,
                                            request.get_response(self.ext_api))
                self.assertIn(USAGES_KEY, response)
                self.assertEqual(1, len(response[USAGES_KEY]))
                self._validate_from_usages(response[USAGES_KEY], net, 0)

                # Get IPv6 should return empty array
                params = 'ip_version=6'
                request = self.new_list_request(API_RESOURCE, params=params)
                response = self.deserialize(self.fmt,
                                            request.get_response(self.ext_api))
                self.assertEqual(0, len(response[USAGES_KEY]))

    def test_usages_query_ip_version_v6(self):
        with self.network() as net:
            with self.subnet(
                    network=net,
                    gateway_ip='fe80::1',
                    cidr='2607:f0d0:1002:51::/64',
                    ip_version=6,
                    ipv6_address_mode=constants.DHCPV6_STATELESS):
                # Get IPv6
                params = 'ip_version=6'
                request = self.new_list_request(API_RESOURCE, params=params)
                response = self.deserialize(self.fmt,
                                            request.get_response(self.ext_api))
                self.assertEqual(1, len(response[USAGES_KEY]))
                self._validate_from_usages(response[USAGES_KEY], net, 0,
                                           18446744073709551615)

                # Get IPv4 should return empty array
                params = 'ip_version=4'
                request = self.new_list_request(API_RESOURCE, params=params)
                response = self.deserialize(self.fmt,
                                            request.get_response(self.ext_api))
                self.assertEqual(0, len(response[USAGES_KEY]))

    def test_usages_ports_consumed_v6(self):
        with self.network() as net:
            with self.subnet(
                    network=net,
                    gateway_ip='fe80::1',
                    cidr='2607:f0d0:1002:51::/64',
                    ip_version=6,
                    ipv6_address_mode=constants.DHCPV6_STATELESS) as subnet:
                request = self.new_list_request(API_RESOURCE)
                # Consume 3 ports
                with self.port(subnet=subnet),\
                        self.port(subnet=subnet), \
                        self.port(subnet=subnet):
                    response = self.deserialize(
                        self.fmt, request.get_response(self.ext_api))

                    self._validate_from_usages(response[USAGES_KEY], net, 3,
                                               18446744073709551615)

    def test_usages_query_network_id(self):
        with self.network() as net:
            with self.subnet(network=net):
                network = net['network']
                test_id = network['id']
                # Get by query param: network_id
                params = 'network_id=%s' % test_id
                request = self.new_list_request(API_RESOURCE, params=params)
                response = self.deserialize(self.fmt,
                                            request.get_response(self.ext_api))
                self.assertIn(USAGES_KEY, response)
                self.assertEqual(1, len(response[USAGES_KEY]))
                self._validate_from_usages(response[USAGES_KEY], net, 0)

                # Get by NON-matching query param: network_id
                params = 'network_id=clearlywontmatch'
                request = self.new_list_request(API_RESOURCE, params=params)
                response = self.deserialize(self.fmt,
                                            request.get_response(self.ext_api))
                self.assertEqual(0, len(response[USAGES_KEY]))

    def test_usages_query_network_name(self):
        test_name = 'net_name_1'
        with self.network(name=test_name) as net:
            with self.subnet(network=net):
                # Get by query param: network_name
                params = 'network_name=%s' % test_name
                request = self.new_list_request(API_RESOURCE, params=params)
                response = self.deserialize(self.fmt,
                                            request.get_response(self.ext_api))
                self.assertIn(USAGES_KEY, response)
                self.assertEqual(1, len(response[USAGES_KEY]))
                self._validate_from_usages(response[USAGES_KEY], net, 0)

                # Get by NON-matching query param: network_name
                params = 'network_name=clearly-wont-match'
                request = self.new_list_request(API_RESOURCE, params=params)
                response = self.deserialize(self.fmt,
                                            request.get_response(self.ext_api))
                self.assertEqual(0, len(response[USAGES_KEY]))
