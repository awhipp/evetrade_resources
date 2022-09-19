'''
Scheduled job that runs every 20min and populates a redis cache
with jump data for all types in all systems.
'''

import os
import time
import json
import traceback
import requests

FILE_ENDPOINT = os.getenv('FILE_ENDPOINT', '')

completed_keys = set()

for root, dirs, files in os.walk('data'):
    for file in files:
        if file.endswith('.json'):
            already_processed = file.replace('.json', '').split('-')
            completed_keys.add(f'{already_processed[0]}-{already_processed[1]}')
            completed_keys.add(f'{already_processed[1]}-{already_processed[0]}')


def create_jump_endpoint(from_system, to_system, jump_type):
    '''
    Creates the endpoint for the jump data
    '''
    return f'https://esi.evetech.net/latest/route/{from_system}/{to_system}/?datasource=tranquility&flag={jump_type}' # pylint: disable=line-too-long

def get_request(url):
    '''
    Helper functions for sending get requests
    '''
    response = requests.get(url)
    return response

systemSecurity = get_request(FILE_ENDPOINT + 'systemIdToSecurity.json')
systemSecurity = systemSecurity.json()
systemList = []
for system in systemSecurity:
    systemList.append(int(system))

def create_file(start, end, obj):
    '''
    Helper function for adding to a pipeline
    '''
    path = f'./data/{start}/'
    isExist = os.path.exists(path)

    if not isExist:
        # Create a new directory because it does not exist 
        os.makedirs(path)

    file_name = f'{path}/{start}-{end}.json'

    with open(file_name, 'w', encoding='utf-8') as fp:
        json.dump(obj, fp)

    completed_keys.add(f'{start}-{end}')
    completed_keys.add(f'{end}-{start}')


def get_all_subsets(arr, jump_data, jump_type):
    '''
    Returns all subsets of an array
    '''

    newarr = []

    for idx1, arri in enumerate(jump_data):
        if idx1 < len(jump_data) :
            subarr = [arri]
            for idx2, arrj in enumerate(jump_data):
                if idx2 > idx1:
                    subarr.append(arrj)
            if len(subarr) > 1:
                newarr.append(subarr)

    for route in newarr:
        jumps = len(route)
        key = f'{route[0]}-{route[-1]}'

        if key not in arr:
            arr[key] = {}

        arr[key][jump_type] = jumps

    return arr


def process(from_system, to_system, attempt=0):
    '''
    Processes a single jump set and pushes data into Redis
    '''
    if attempt > 10:
        raise Exception(f'Too many attempts. {from_system}-{to_system}')

    try:
        global jump_json

        if from_system == to_system:
            jump_json[f'{from_system}-{to_system}'] = {
                'shortest': 0,
                'secure': 0,
                'insecure': 0
            }
            # create_file(from_system, to_system, jump_json)
            return 100
        else:
            rate_limit = 100

            for jump_type in ['shortest', 'secure', 'insecure']:
                jump_endpoint = create_jump_endpoint(from_system, to_system, jump_type)

                response = get_request(jump_endpoint)
                jump_data = response.json()
                rate_limit = int(response.headers['X-Esi-Error-Limit-Remain'])

                if 'error' in jump_data:
                    key = f'{from_system}-{to_system}'

                    if key in completed_keys:
                        continue

                    jump_json[key] = {
                        'shortest': -1,
                        'secure': -1,
                        'insecure': -1
                    }
                    
                    return rate_limit
                else:
                    for idx1, i in enumerate(jump_data):
                        for idx2, j in enumerate(jump_data):
                            if idx2 >= idx1:
                                key = f'{i}-{j}'
                                if key in completed_keys:
                                    continue
                                if key not in jump_json:
                                    jump_json[key] = {}
                                jump_json[key][jump_type] = idx2-idx1

            return rate_limit

    except Exception: # pylint: disable=broad-except
        print(traceback.format_exc())
        print(f'!! Error processing {from_system}-{to_system}. Trying again in 60 seconds.')
        time.sleep(60)
        return process(from_system, to_system, attempt+1)


jump_json = {}

def main(system_id_from):
    '''
    Main function
    '''
    global jump_json
    jump_json = {}

    skipped = 0


    for idx, system_id_to in enumerate(systemList):

        if f'{system_id_from}-{system_id_to}' in completed_keys or f'{system_id_to}-{system_id_from}' in completed_keys:
            skipped += 1
            continue
        
        rate_limit = process(system_id_from, system_id_to)

        if isinstance(rate_limit, int):
            # print(f'-- {system_id_from}-{system_id_to}: {idx+1} of {len(systemList)} systems (rate limit {rate_limit})')

            if rate_limit <= 10:
                print(f'!! Rate limit {rate_limit} reached. Sleeping for a minute.')
                time.sleep(60)
    
    new_routes_created = 0
    if len(jump_json) > 0:
        print(f'JSON length: {len(jump_json)}')
        for key, value in jump_json.items():
            if len(value) == 3:
                create_file(key.split('-')[0], key.split('-')[1], value)
                new_routes_created += 1

        print(f'-- {new_routes_created} new routes created. {skipped} skipped. Total routes: {len(completed_keys)}\n')
        return new_routes_created


path = './data/'
isExist = os.path.exists(path)
if not isExist:
    # Create a new directory because it does not exist
    os.makedirs(path)

for idx, system_id in enumerate(systemList):
    print(f'System: {system_id} ({idx+1} of {len(systemList)})')
    main(system_id)
