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

import netaddr
import six
from sqlalchemy import func

import neutron.db.models_v2 as mod
import oslo_log.log as logging


LOG = logging.getLogger(__name__)


SUPPORTED_FILTERS = {
    'network_id': mod.Network.id,
    'network_name': mod.Network.name,
    'ip_version': mod.Subnet.ip_version,
}
SUPPORTED_FILTER_KEYS = six.viewkeys(SUPPORTED_FILTERS)


class IpUsageMixin(object):
    """Mixin class to query for IP usage."""

    data_columns = [
        mod.Network.id.label('network_id'),
        mod.Network.name.label('network_name'),
        mod.Subnet.id.label('subnet_id'),
        mod.Subnet.name.label('subnet_name'),
        mod.Subnet.ip_version,
        mod.Subnet.cidr,
        mod.IPAllocationPool.first_ip.label('first_ip'),
        mod.IPAllocationPool.last_ip.label('last_ip')]

    computed_columns = [
        func.count(mod.IPAllocation.subnet_id).label('used_ips')]

    @classmethod
    def get_network_ip_allocations(cls, context, filters=None):
        """Get IP usage stats on a per subnet basis.

        Returns a list of network summaries which internally contains a list
        of subnet summaries. The used_ip and total_ip counts are returned at
        both levels.
        """
        query = cls._build_query(context, filters)
        LOG.debug('Usage query generated: %s', query)

        # Assemble result
        result_dict = {}
        for row in query.all():
            cls._add_result(result_dict, row)

        # Convert result back into the list it expects
        net_ip_usages = list(six.viewvalues(result_dict))
        return net_ip_usages

    @classmethod
    def _build_query(cls, context, filters):
        # Generate a query to gather all information.
        # Ensure query is tolerant of missing child table data (outerjoins)
        # Process these outerjoin columns assuming their values may be None
        query = context.session.query()\
            .add_columns(*cls.data_columns)\
            .add_columns(*cls.computed_columns)\
            .outerjoin(mod.Subnet, mod.Network.id == mod.Subnet.network_id,)\
            .outerjoin(mod.IPAllocation,
                       mod.Subnet.id == mod.IPAllocation.subnet_id)\
            .outerjoin(mod.IPAllocationPool,
                       mod.Subnet.id == mod.IPAllocationPool.subnet_id)\
            .group_by(*cls.data_columns)

        # Apply filters directly to query (if applicable)
        return cls._adjust_query_for_filters(query, filters)

    @classmethod
    def _adjust_query_for_filters(cls, query, filters):
        # The intersect of sets gets us applicable filter keys
        common_keys = six.viewkeys(filters) & SUPPORTED_FILTER_KEYS
        for key in common_keys:
            # TODO(wwriverrat) consider 'or' when we get more than one in list
            # Example: (network_id='xxxx' or network_id='yyyy')
            filter_vals = filters[key]
            single_val = None
            if isinstance(filter_vals, list) and len(filter_vals) >= 1:
                single_val = filter_vals[0]
            elif isinstance(filter_vals, six.string_types):
                single_val = filter_vals

            if single_val:
                query = query.filter(
                    SUPPORTED_FILTERS[key] == single_val)
        return query

    @classmethod
    def _add_result(cls, result_dict, db_row):
        # Find network in results. Create and add if missing
        if db_row.network_id in result_dict:
            network = result_dict[db_row.network_id]
        else:
            network = {'id': db_row.network_id, 'name': db_row.network_name,
                       'subnet_ip_allocations': [], 'used_ips': 0,
                       'total_ips': 0}
            result_dict[db_row.network_id] = network

        # Skip rows without subnet data
        if not db_row.subnet_id:
            return

        cls._add_subnet_data_to_net(db_row, network)

    @classmethod
    def _add_subnet_data_to_net(cls, db_row, network):
        # Note: This method must assume db_row may not have subnet or
        # IPAllocationsPool information (i.e. value = None)

        # Skip rows without subnet data
        if not db_row.subnet_id:
            return

        subnet = {
            'subnet_id': db_row.subnet_id,
            'ip_version': db_row.ip_version,
            'cidr': db_row.cidr,
            'name': db_row.subnet_name,
            'used_ips': db_row.used_ips if db_row.used_ips else 0
        }
        # Handle missing IPAllocationPool data
        if db_row.last_ip:
            total_ips = netaddr.IPRange(netaddr.IPAddress(db_row.first_ip),
                                        netaddr.IPAddress(db_row.last_ip)).size
        else:
            total_ips = netaddr.IPNetwork(db_row.cidr,
                                          version=db_row.ip_version).size
        subnet['total_ips'] = total_ips

        # Attach subnet result and Rollup subnet sums into the parent
        network['subnet_ip_allocations'].append(subnet)
        network['total_ips'] += total_ips
        network['used_ips'] += subnet['used_ips']
