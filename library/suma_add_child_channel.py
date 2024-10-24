#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['Alpha'],
    'supported_by': 'elgeffo'
}

DOCUMENTATION = '''
---
module: suse_manager

short_description: This module controls child channels from a host

version_added: "0.1"

description:
    - "This module will add a child channel to a host and make sure it is scheduled as soon as possible"

options:

author:
    - Jeffrey Bekker @jeffrey44113 (gitlab.com)
'''

EXAMPLES = '''
- name: add child channel
  suma_add_child_channel:
    host: https://suma.testing.lan/rhn/manager/api
    username: elgeffo
    password: testing123
    hostname: testhost
    child_channel: zabbix7.0 (This must be the channel label)
    ssl_accept: False (if set to True then make sure that you have the internal certificate imported)
'''

RETURN = '''

'''

from ansible.module_utils.basic import AnsibleModule
import requests
import json
import datetime


def add_child_channel():
    module_args = dict(
        host=dict(type='str', required=True),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        hostname=dict(type='str', required=True),
        child_channel=dict(type='str', required=True),
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
            sys_id = system['id']
            base_params = {"sid": sys_id}

    # creating the channel list and then appending the provided child channel name
    channel = []
    channel.append(module.params['child_channel'])

    basechannel = requests.get(host + '/system/getSubscribedBaseChannel', json=base_params, cookies=cookies, verify=ssl_accept)
    base_json = basechannel.json()

    main_label = base_json['result']['label']

    child_channels = requests.get(host + '/system/listSubscribedChildChannels', json=base_params, cookies=cookies, verify=ssl_accept)
    child_channels_json=child_channels.json()
    for channels in child_channels_json['result']:
        cchannel_labels = str(channels['label'])
        channel.append(cchannel_labels)

    date_iso =datetime.datetime.utcnow().isoformat() + "Z"

    scheduleC_params={"sid": sys_id, "baseChannelLabel": main_label  ,"childLabels": channel, "earliestOccurrence": date_iso }

    scheduleC_change = requests.post(host + '/system/scheduleChangeChannels', json=scheduleC_params, cookies=cookies, verify=ssl_accept)

    if scheduleC_change.status_code == 200:
        result_message = f"child module added to system {hostname}"
        result['changed'] = True
        result['message'] = result_message
    else:
        result_message = "something went wrong, please check over your settings and check logs from suse manager"
        result['changed'] = False
        result['message'] = result_message

    module.exit_json(**result)

def main():
    add_child_channel()


if __name__ == '__main__':
    main()
