import os
import time
import json
import requests

from esipy import EsiSecurity

CLIENT_ID = os.getenv('ESI_CLIENT_ID', 'TO BE ADDED')
SECRET_KEY = os.getenv('ESI_SECRET_KEY', 'TO BE ADDED')
CALL_BACK = 'https://evetrade.space'
USER_AGENT = 'EVETrade.space - https://evetrade.space - Structure Market Data Application'

tokens = {
    'refresh_token': os.getenv('ESI_REFRESH_TOKEN', 'TO BE ADDED')
}

security = EsiSecurity(
    redirect_uri=CALL_BACK,
    client_id=CLIENT_ID,
    secret_key=SECRET_KEY,
    headers={'User-Agent': USER_AGENT},
)

def generate_auth_url(security):
    '''
    Generates an auth URL from the ESI endpoint (not used)
    '''
    from uuid import uuid4
    print(
        security.get_auth_uri(
            state=str(uuid4()), 
            scopes=['esi-universe.read_structures.v1', 'esi-markets.structure_markets.v1']
        )
    )


def generate_token(security):
    '''
    Generates the access token from the ESI endpoint (not used)
    '''
    AUTH_CODE = 'TO BE ADDED'
    print(security.auth(AUTH_CODE))


def refresh_token(tokens):
    '''
    Refreshes the access token from the ESI endpoint
    '''
    security.update_token({
        'access_token': '',  # leave this empty
        'expires_in': -1,  # seconds until expiry, so we force refresh anyway
        'refresh_token': tokens['refresh_token'],
    })

    return security.refresh()

def get_system_to_other_ids():
    '''
    Gets the region IDs from the universeList.json file
    '''
    s3_file = requests.get("https://evetrade.s3.amazonaws.com/resources/universeList.json", timeout=30)
    s3_file_json = s3_file.json()

    system_index = {}

    for region in s3_file_json:
        info = s3_file_json[region]
        if 'system' in info:
            system_index[info['system']] = {
                'region_id': info['region'],
                'security': info['security'],
            }

    return system_index

def get_structure_ids():
    '''
    Gets all structure ids from the ESI endpoint
    '''
    structure_ids = []

    response = requests.get(
        'https://esi.evetech.net/latest/universe/structures/?datasource=tranquility&filter=market', 
        timeout=30
    )

    if response.status_code == 200:
        structure_ids = response.json()

    return structure_ids

def get_security_code(security):
    if security >= 0.5:
        return "high_sec"
    elif security > 0:
        return "low_sec"
    elif security <= 0:
        return "null_sec"
    else:
        return -1


def get_structure_info(access_token, system_index):
    '''
    Gets all structure info from the ESI endpoint
    '''
    structure_ids = get_structure_ids()

    structure_info = {}
    structure_list = []

    for structure_id in structure_ids:
        response = requests.get(
            f'https://esi.evetech.net/latest/universe/structures/{structure_id}/?datasource=tranquility&token={access_token}', 
            timeout=30
        )

        if response.status_code == 200:
            structure = response.json()

            if structure['solar_system_id'] not in system_index:
                system_response = requests.get(
                    f'https://esi.evetech.net/latest/universe/systems/{structure["solar_system_id"]}/?datasource=tranquility', 
                    timeout=30
                )
                system_json = system_response.json()
                system_index[structure['solar_system_id']] = {
                    'security': system_json['security_status'],
                }

                constellation_response = requests.get(
                    f'https://esi.evetech.net/latest/universe/constellations/{system_json["constellation_id"]}/?datasource=tranquility', 
                    timeout=30
                )
                constellation_json = constellation_response.json()
                system_index[structure['solar_system_id']]['region_id'] = constellation_json['region_id']

            structure_info[structure_id] = {
                'name': structure['name'],
                'system_id': structure['solar_system_id'],
                'station_id': structure_id,
                'region_id': system_index[structure['solar_system_id']]['region_id'],
                'security': system_index[structure['solar_system_id']]['security'],
                'security_code': get_security_code(system_index[structure['solar_system_id']]['security']),
            }

            structure_list.append(structure['name'])

    return structure_info, structure_list



start = time.time()
print('Starting...')

token = refresh_token(tokens)
print('- Done refreshing token')

system_index = get_system_to_other_ids()
print('- Done getting system index')

structure_info, structure_list = get_structure_info(token['access_token'], system_index)
print('- Done getting structure info')

with open('resources/structureInfo.json', 'w', encoding='utf-8') as f:
    json.dump(structure_info, f, indent=4)
print('- Done writing structure info')

with open('resources/structureList.json', 'w', encoding='utf-8') as f:
    json.dump(structure_list, f, indent=4)
print('- Done writing structure list')

print(f'Finished in {time.time() - start} seconds')
