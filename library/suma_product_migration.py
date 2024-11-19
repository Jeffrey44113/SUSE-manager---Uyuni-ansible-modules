#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['Alpha'],
    'supported_by': 'elgeffo'
}

DOCUMENTATION = '''
---
module: suse_manager

short_description: This module schedules a product migration for a host

version_added: "0.1"

description:
    - "This module schedules a product migration for a host, it will check if it is prod or test or canary and adds the required channels"

options:

author:
    - Jeffrey Bekker @jeffrey44113 (gitlab.com)
'''

EXAMPLES = '''
- name: Product migration
  suma_product_migration:
    host: https://suma.testing.lan/rhn/manager/api
    username: Elgeffo
    password: testing123
    hostname: testhost
    env: test/canary/prod (Whatever you have in case of environments)
    sles_version: 15 (Major version)
    service_pack: SP5 (Service pack Don't forget the SP infront of it)
    dry_run: False (Default is false)
    ssl_accept: False (if set to True then make sure that you have the internal certificate imported)
'''

RETURN = '''

'''

from ansible.module_utils.basic import AnsibleModule
import requests
import json
import datetime


def schedule_product_migration():
    module_args = dict(
        host=dict(type='str', required=True),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        hostname=dict(type='str', required=True),
        env=dict(type='str', required=True),
        sles_version=dict(type='str', required=True),
        service_pack=dict(type='str', required=True),
        dry_run=dict(typpe='bool', required=False, default=False),
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


    # defining the vars needed later on from the module_args
    hostname = module.params['hostname']
    env = module.params['env']
    sles_ver = module.params['sles_version']
    sp_pack = module.params['service_pack']
    dry_run = module.params['dry_run']

    # Get all hosts and finding the correct host

    all_systems = requests.get(host + '/system/listActiveSystems', cookies=cookies, verify=ssl_accept)
    all_systems_json = all_systems.json()

    for system in all_systems_json['result']:
        sys_name = system['name']
        if hostname.upper() in sys_name.upper():
            sys_id_array = []
            sys_id = system['id']
            sys_id_array.append(sys_id)

    # Add the basechannel label + optional child channels
    migration_targets_params = {"sid": sys_id, 'excludeTargetWhereMissingSuccessors': False}

    migration_targets = requests.post(host + '/system/listMigrationTargets', cookies=cookies, json=migration_targets_params, verify=ssl_accept)

    migration_targetsjson = migration_targets.json()

    for target in migration_targetsjson['result']:
        target_ident = target['ident']
        target_friendly = target['friendly']
        if sp_pack in target_friendly:
            sp_ident = target_ident

    # datatime iso for later to be used
    date_iso = datetime.datetime.utcnow().isoformat() + "Z"

    # Base channel label
    subscribable_params = {'sid': sys_id}
    subscribable_base_list = requests.get(host + '/system/listSubscribableBaseChannels', cookies=cookies, json=subscribable_params, verify=ssl_accept)
    subscribable_base_list_json = subscribable_base_list.json()

    for base_sub in subscribable_base_list_json['result']:
        base_sub_name = base_sub['name']
        if sp_pack in base_sub_name and sles_ver in base_sub_name and env in base_sub_name:
            base_channel_label = base_sub['label']

    # empty for now since not figured out a propper way to do this yet
    option_child_channels = []

    schedule_product_migration_params = {"sid": sys_id,'targetIdent': sp_ident, 'baseChannelLabel': base_channel_label, 'optionalChildChannels': option_child_channels, 'dryRun': dry_run , 'allowVendorChange': True,'removeProductsWithNoSuccessorAfterMigration': True, 'earliestOccurrence': date_iso}
    schedule_product_migration = requests.post(host + '/system/scheduleProductMigration', cookies=cookies, json=schedule_product_migration_params, verify=ssl_accept)
    json_response = schedule_product_migration.json()

    if json_response['success'] is True:
        message = 'Product migration is scheduled, jobID: ' + str(json_response['result'])
        result['changed'] = True
        result['message'] = message 
    elif json_response['success'] is False:
        message = 'Something went wrong, please check the host'
        result['changed'] = False
        result['message'] = message 
    else:
        message = 'Something went wrong, please check the host'
        result['changed'] = False
        result['message'] = message 
    # send the results
    module.exit_json(**result)

def main():
    schedule_product_migration()

if __name__ == '__main__':
    main()