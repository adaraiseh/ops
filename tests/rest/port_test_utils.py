#!/usr/bin/env python
#
# Copyright (C) 2015 Hewlett Packard Enterprise Development LP
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json
import httplib
import urllib
from copy import deepcopy

import request_test_utils


test_data = {"configuration": {
        "name": "Port1",
        "interfaces": ["/rest/v1/system/interfaces/1"],
        "trunks": [413],
        "ip4_address_secondary": ["192.168.0.1"],
        "lacp": "active",
        "bond_mode": "l2-src-dst-hash",
        "tag": 654,
        "vlan_mode": "trunk",
        "ip6_address": "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
        "external_ids": {"extid1key": "extid1value"},
        "bond_options": {"key1": "value1"},
        "mac": "01:23:45:67:89:ab",
        "other_config": {"cfg-1key": "cfg1val"},
        "bond_active_slave": "null",
        "ip6_address_secondary": ["01:23:45:67:89:ab"],
        "vlan_options": {"opt1key": "opt2val"},
        "ip4_address": "192.168.0.1",
        "admin": "up"
    },
    "referenced_by": [{"uri":"/rest/v1/system/bridges/bridge_normal"}]}


def get_switch_ip(switch):
    return switch.cmd("python -c \"import socket; print socket.gethostbyname(socket.gethostname())\"")

def create_test_port (ip):
    path = "/rest/v1/system/ports"
    status_code, response_data = request_test_utils.execute_request(path, "POST", json.dumps(test_data), ip)
    return status_code

def compare_dict(dict1, dict2):
    if dict1 == None or dict2 == None:
        return False

    if type(dict1) is not dict or type(dict2) is not dict:
        return False

    shared_keys = set(dict2.keys()) & set(dict2.keys())

    if not (len(shared_keys) == len(dict1.keys()) and len(shared_keys) == len(dict2.keys())):
        return False

    dicts_are_equal = True
    for key in dict1.keys():
        if type(dict1[key]) is dict:
            dicts_are_equal = dicts_are_equal and compare_dict(dict1[key], dict2[key])
        elif type(dict1[key]) is list:
            intersection = set(dict1[key]) ^ set(dict2[key])
            dicts_are_equal = dicts_are_equal and len(intersection) == 0
        else:
            dicts_are_equal = dicts_are_equal and (dict1[key] == dict2[key])

    return dicts_are_equal

def execute_port_operations(data, port_name, http_method, operation_uri, switch_ip):

    results = []

    for attribute in data:

        attribute_name = attribute[0]
        attribute_value = attribute[1]
        expected_code = attribute[2]

        request_data = deepcopy(test_data)
        request_data['configuration']['name'] = "{0}_{1}_{2}".format(port_name, attribute_name, expected_code)

        if http_method == 'PUT':

            # Create a test port
            status_code, response_data = request_test_utils.execute_request(operation_uri, "POST", json.dumps(request_data), switch_ip)

            if status_code != httplib.CREATED:
                return []

            port_uri = operation_uri + "/%s" % request_data['configuration']['name']

            # Delete reference_by from PUT
            del request_data['referenced_by']
        else:
            port_uri = operation_uri

        # Execute request

        print "Attempting to {0} a port with value '{1}' ({3}) for attribute '{2}'".format(http_method, attribute_value, attribute_name, type(attribute_value).__name__)
        # Change value for specified attribute
        request_data['configuration'][attribute_name] = attribute_value
        # Execute request
        status_code, response_data = request_test_utils.execute_request(port_uri, http_method, json.dumps(request_data), switch_ip)

        # Check if status code was as expected

        if status_code != expected_code:
            results.append((attribute_name, False, status_code, expected_code))
        else:
            results.append((attribute_name, True, status_code))

    return results
