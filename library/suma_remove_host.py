#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['Alpha'],
    'supported_by': 'elgeffo'
}

DOCUMENTATION = '''
---
module: suma_delete_host

short_description: This module is to delete a host from suse manager

version_added: "0.1"

description:
    - "With this module you can delete a host from from suse manager / uyuni"

options:

author:
    - Jeffrey Bekker @jeffrey44113 (gitlab.com)
'''

EXAMPLES = '''
- name: Delete host from suse manager
  suma_delete_host:
    host: https://suma.testing.lan/rhn/manager/api
    username: elgeffo
    password: testing123
    ssl_accept: False (if set to True then make sure that you have the internal certificate imported)
    hostname: host_001
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
import requests
import json

def delete_host():
    module_args = dict(
        host=dict(type='str', required=True),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        ssl_accept=dict(type='bool', required=False, default=False),
        hostname=dict(type='str', required=True)
    )

    module = AnsibleModule(
        arugement_spec=module_args,
        support_check_mode=False
    )

    result = dict(
        changed=False,
        original_message='',
        message=''
    )

   # First login
    host = module.params['host']
    username = module.params['username']
    password = module.params['password']
    ssl_accept = module.params['ssl_accept']

    data = {"login": username, "password": password}
    response = requests.post(host + '/auth/login', json=data, verify=ssl_accept)
    cookies = response.cookies

    # Get all hosts and finding the correct host
    hostname = module.params['hostname']

    all_systems = requests.get(host + '/system/listActiveSystems', cookies=cookies, verify=ssl_accept)
    all_systems_json = all_systems.json()

    for system in all_systems_json['result']:
        sys_name = system['name']
        if hostname.upper() in sys_name.upper():
            sys_id = system['id']
            sys_args = {"sid": sys_id}
            delete_sys = requests.post(host + '/system/deleteSystem', json=sys_args, cookies=cookies, verify=ssl_accept)
            delete_sys_json = delete_sys.json()

            if delete_sys_json['result'] == 1:
                result['changed'] = True
                result['message'] = "Host deleted"

        else:
           result['changed'] = False
           result['message'] = "No system with the name provided has been found"

    module.exit_json(**result)


def main():
    delete_host()

if __name__ == '__main__':
    main()
