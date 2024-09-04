#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['Alpha'],
    'supported_by': 'elgeffo'
}

DOCUMENTATION = '''
---
module: suse_manager

short_description: This module is to control run items in suse manager

version_added: "0.1"

description:
    - "With this module you can accept the pending salt keys from suse manager / uyuni"

options:

author:
    - Jeffrey Bekker @jeffrey44113 (gitlab.com)
'''

EXAMPLES = '''
- name: Accept salt keys
  suma_accept_salt:
    host: https://suma.testing.lan/rhn/manager/api
    username: elgeffo
    password: testing123
    ssl_accept: False (if set to True then make sure that you have the internal certificate imported)
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
import requests

def accept_salt():
    module_args = dict(
        host=dict(type='str', required=True),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
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

    # check if any salt keys need to be accepted
    # list of pending keys
    key_list = requests.get(host + '/saltkey/pendingList', cookies=cookies, verify=ssl_accept)
    pending_keys = key_list.json()['result']

    # accepting the key then..
    # Getting the minion ID in some way
    if len(pending_keys) < 1:
        result['changed'] = False
        result['message'] = "no keys to accept"
    else:
        for to_be_accepted in pending_keys:
            parameters = {"minionId": to_be_accepted}
            accept = requests.post(host + '/saltkey/accept', json=parameters, cookies=cookies, verify=ssl_accept)

        result['changed'] = True
        result['message'] = 'Salt keys accepted'
    # send the results on success
    module.exit_json(**result)


def main():
    accept_salt()


if __name__ == '__main__':
    main()
