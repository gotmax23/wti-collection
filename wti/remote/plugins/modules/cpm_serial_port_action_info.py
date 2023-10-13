#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (C) 2023 Red Hat Inc.
# Copyright (C) 2023 Western Telematic Inc.
#
# GNU General Public License v3.0+
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Module to retrieve WTI Serial Port Connection status from WTI OOB and PDU devices.
# CPM remote_management
#
from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = """
---
module: cpm_serial_port_action_info
version_added: "2.9.0"
author: "Western Telematic Inc. (@wtinetworkgear)"
short_description: Get Serial port connection status in WTI OOB and PDU devices
description:
    - "Get Serial port connection status from WTI OOB and PDU devices"
options:
    cpm_url:
        description:
            - This is the URL of the WTI device to send the module.
        type: str
        required: true
    cpm_username:
        description:
            - This is the Username of the WTI device to send the module. If this value
            - is blank, then the cpm_password is presumed to be a User Token.
        type: str
        required: false
    cpm_password:
        description:
            - This is the Password of the WTI device to send the module. If the
            - cpm_username is blank, this parameter is presumed to be a User Token.
        type: str
        required: true
    use_https:
        description:
            - Designates to use an https connection or http connection.
        type: bool
        required: false
        default: false
    validate_certs:
        description:
            - If false, SSL certificates will not be validated. This should only be used
            - on personally controlled sites using self-signed certificates.
        type: bool
        required: false
        default: false
    use_proxy:
        description: Flag to control if the lookup will observe HTTP proxy environment variables when present.
        type: bool
        required: false
        default: false
    port:
        description:
            - This is the serial port number that is getting retrieved. It can include a single port
            - number, multiple port numbers separated by commas, a list of port numbers, or an '*' character for all ports.
        type: list
        elements: str
        default: ['*']
notes:
  - Use C(groups/cpm) in C(module_defaults) to set common options used between CPM modules.)
"""

EXAMPLES = """
- name: Get the Serial Port Parameters for port 2 of a WTI device
  cpm_serial_port_action_info:
    cpm_url: "nonexist.wti.com"
    cpm_username: "super"
    cpm_password: "super"
    use_https: true
    validate_certs: false
    port: 2

- name: Get the Serial Port Parameters for port 2 of a WTI device using a User Token
  cpm_serial_port_action_info:
    cpm_url: "nonexist.wti.com"
    cpm_username: ""
    cpm_password: "randomusertokenfromthewtidevice"
    use_https: true
    validate_certs: false
    port: 2

- name: Get the Serial Port Parameters for ports 2 and 4 of a WTI device
  cpm_serial_port_action_info:
    cpm_url: "nonexist.wti.com"
    cpm_username: "super"
    cpm_password: "super"
    use_https: true
    validate_certs: false
    port: 2,4

- name: Get the Serial Port Parameters for all ports of a WTI device
  cpm_serial_port_info:
    cpm_url: "nonexist.wti.com"
    cpm_username: "super"
    cpm_password: "super"
    use_https: true
    validate_certs: false
    port: "*"
"""

RETURN = """
data:
  description: The output JSON returned from the commands sent
  returned: always
  type: complex
  contains:
    ports:
      description: List of connection status for each serial port
      returned: success
      type: list
      sample:
        - port: 2
          connstatus: "Free"

        - port: 4
          connstatus: " C-06"
"""

import base64
import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text, to_bytes, to_native
from ansible.module_utils.six.moves.urllib.error import HTTPError, URLError
from ansible.module_utils.urls import open_url, ConnectionError, SSLValidationError


def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        cpm_url=dict(type='str', required=True),
        cpm_username=dict(type='str', required=False),
        cpm_password=dict(type='str', required=True, no_log=True),
        port=dict(type='list', elements='str', default=['*']),
        use_https=dict(type='bool', default=False),
        validate_certs=dict(type='bool', default=False),
        use_proxy=dict(type='bool', default=False)
    )

    result = dict(
        changed=False,
        data=''
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if (len(to_native(module.params['cpm_username'])) > 0):
        auth = to_text(base64.b64encode(to_bytes('{0}:{1}'.format(to_native(module.params['cpm_username']), to_native(module.params['cpm_password'])),
                       errors='surrogate_or_strict')))
        header = {'Content-Type': 'application/json', 'Authorization': "Basic %s" % auth}
    else:
        header = {'Content-Type': 'application/json', 'X-WTI-API-KEY': "%s" % (to_native(module.params['cpm_password']))}

    if module.params['use_https'] is True:
        protocol = "https://"
    else:
        protocol = "http://"

    ports = module.params['port']
    if isinstance(ports, list):
        ports = ','.join(to_native(x) for x in ports)
    fullurl = ("%s%s/api/v2%s/config/serialportsaction?ports=%s" % (protocol, to_native(module.params['cpm_url']),
               "" if len(to_native(module.params['cpm_username'])) else "/token", ports))

    try:
        response = open_url(fullurl, data=None, method='GET', validate_certs=module.params['validate_certs'], use_proxy=module.params['use_proxy'],
                            headers=header)

    except HTTPError as e:
        fail_json = dict(msg='GET: Received HTTP error for {0} : {1}'.format(fullurl, to_native(e)), changed=False)
        module.fail_json(**fail_json)
    except URLError as e:
        fail_json = dict(msg='GET: Failed lookup url for {0} : {1}'.format(fullurl, to_native(e)), changed=False)
        module.fail_json(**fail_json)
    except SSLValidationError as e:
        fail_json = dict(msg='GET: Error validating the server''s certificate for {0} : {1}'.format(fullurl, to_native(e)), changed=False)
        module.fail_json(**fail_json)
    except ConnectionError as e:
        fail_json = dict(msg='GET: Error connecting to {0} : {1}'.format(fullurl, to_native(e)), changed=False)
        module.fail_json(**fail_json)

    result['data'] = json.loads(response.read())

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
