#els-neutron Network Ip Usages Extension

The following article documents the API for the ELS OpenStack Extension: IP Usage

This extension is an information-only api that allows a user or process to determine the
amount of IPs that are consumed across networks and their subnets' allocation pools.

# Table of Contents #
[API Specification](#api-specification)
- [End Points](#end-points)
- [Get usage for all networks](#get-usage-for-all-networks)
- [Get usage by network uuid](#get-usage-by-network-id)


## API Specification ###

### Get IP usages ###
#### Get usage for all networks ####
Example curl
```
curl -i -k -H 'Content-Type: application/json' -H "X-Auth-Token: SOME_AUTH_TOKEN" https://neutron-dev:9696/v2.0/network-ip-usages
```
GET /v2.0/network-ip-usages
```
Request to url: v2.0/network-ip-usages
  headers: {'content-type': 'application/json', 'X-Auth-Token': 'SOME_AUTH_TOKEN'}
```
Example response
```
Response:
  HTTP/1.1 200 OK
  Content-Type: application/json; charset=UTF-8
  Content-Length: 1257
```
```javascript
{
    "network_ip_usages": [
        {
            "id": "36ef9bf1-e5aa-4572-9824-50249b24a53f",
            "name": "net3",
            "subnet_ip_allocations": [
                {
                    "cidr": "40.0.0.0/24",
                    "ip_version": 4,
                    "name": "",
                    "subnet_id": "0e4ab73b-4656-4b71-a4c6-db1bf214f234",
                    "total_ips": 253,
                    "used_ips": 2
                }
            ],
            "total_ips": 253,
            "used_ips": 2
        },
        {
            "id": "8d5ffe37-12a3-4c47-8de5-77ab43bf80c3",
            "name": "net1",
            "subnet_ip_allocations": [
                {
                    "cidr": "10.0.0.0/24",
                    "ip_version": 4,
                    "name": "",
                    "subnet_id": "40ec375e-bb90-428a-b7da-a4258c3ddc14",
                    "total_ips": 253,
                    "used_ips": 3
                }
            ],
            "total_ips": 253,
            "used_ips": 3
        },
        {
            "id": "d75ac80d-9aa7-4242-9048-a07536e91f0d",
            "name": "net2",
            "subnet_ip_allocations": [],
            "total_ips": 0,
            "used_ips": 0
        }
    ]
}
```

#### Get usage by network ID ####
Example curl
```
curl -i -k -H 'Content-Type: application/json' -H "X-Auth-Token: SOME_AUTH_TOKEN" https://neutron-dev:9696/v2.0/network-ip-usages/2d5fe344-4e98-4ccc-8c91-b8064d17c64c
```
GET /v2.0/network-ip-usages/{network_uuid}
```
Request to url: /v2.0/network-ip-usages/8d5ffe37-12a3-4c47-8de5-77ab43bf80c3
  headers: {'content-type': 'application/json', 'X-Auth-Token': 'SOME_AUTH_TOKEN'}
```
Example response
```
Response:
  HTTP/1.1 200 OK
  Content-Type: application/json; charset=UTF-8
  Content-Length: 468
```
```javascript
{
    "network_ip_usage": {
        "id": "8d5ffe37-12a3-4c47-8de5-77ab43bf80c3",
        "name": "net1",
        "subnet_ip_allocations": [
            {
                "cidr": "10.0.0.0/24",
                "ip_version": 4,
                "name": "",
                "subnet_id": "40ec375e-bb90-428a-b7da-a4258c3ddc14",
                "total_ips": 253,
                "used_ips": 3
            }
        ],
        "total_ips": 253,
        "used_ips": 3
    }
}
```
