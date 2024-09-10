#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['Alpha'],
    'supported_by': 'elgeffo'
}

DOCUMENTATION = '''
---
module: suse_manager

short_description: This module removes a schedule from a host

version_added: "0.1"

description:
    - "This module will remove a schedule from a host, usefull if you need to do anything related to the host"

options:

author:
    - Jeffrey Bekker @jeffrey44113 (gitlab.com)
'''

EXAMPLES = '''
- name: remove child channel
  suma_remove_schedule:
    host: https://suma.testing.lan/rhn/manager/api
    username: jbekker
    password: testing123
    hostname: testhost
    ssl_accept: False (if set to True then make sure that you have the internal certificate imported)
'''

RETURN = '''

'''

from ansible.module_utils.basic import AnsibleModule
import requests
import json
import datetime


def remove_schedule():
    module_args = dict(
        host=dict(type='str', required=True),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        hostname=dict(type='str', required=True),
        ssl_accept=dict(type='bool', required=False, default=False)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    result = dict(
        changed=False,
        original_message='',
        message=''
    )
    # api calls part
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
            sys_id_array = []
            sys_id = system['id']
            sys_id_array.append(sys_id)

    retract_schedule_params = {"sids": sys_id_array}
    retract_schedule = requests.post(host + '/maintenance/retractScheduleFromSystems', cookies=cookies, json=retract_schedule_params, verify=ssl_accept)
    
    if retract_schedule.status_code == 200:
        result_message = f"Schedule remove from {hostname}"
        result['changed'] = True
        result['message'] = result_message
    else:
        result_message = "something went wrong, please check over your settings and check logs from suse manager"
        result['changed'] = False
        result['failed'] = True
        result['message'] = result_message

    module.exit_json(**result)

def main():
    remove_schedule()

if __name__ == '__main__':
    main()
