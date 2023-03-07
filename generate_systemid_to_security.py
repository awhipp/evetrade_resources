'''
Generate System ID to Security Mapping from universeList.json and structureInfo.json
'''
import os
import json

def get_security_code(rating):
    '''Get the security code from the security rating'''
    if rating >= 0.5:
        return 'high_sec'
    elif rating > 0:
        return 'low_sec'
    elif rating <= 0:
        return 'null_sec'
    else:
        return -1

def generate_security_details():
    '''Generate System ID to Security Mapping from universeList.json and structureInfo.json'''
    systemIdToSecurity = {}

    # Get the path to the universeList.json file
    universe_list_json = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources/universeList.json')

    # Load the universeList.json file
    with open(universe_list_json, 'r', encoding='utf-8') as universe_list_file:
        universe_list = json.load(universe_list_file)

        # Generate the System ID to Security Mapping
        for item in universe_list:
            universe_item = universe_list[item]
            if 'security' in universe_item:
                systemId  = universe_item['system']
                security = universe_item['security']
                security_code = get_security_code(security)

                systemIdToSecurity[systemId] = {
                    'rating': security,
                    'security_code': security_code
                }

    # Get the path to the structureInfo.json file
    structure_info_json = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources/structureInfo.json')

    # Load the structureInfo.json file
    with open(structure_info_json, 'r', encoding='utf-8') as structure_info_file:
        structure_info = json.load(structure_info_file)

        # Generate the System ID to Security Mapping
        for item in structure_info:
            structure_object = structure_info[item]
            systemId  = structure_object['system_id']
            print(systemId)
            if systemId in systemIdToSecurity:
                continue
            else:
                security = structure_object['security']
                security_code = structure_object['security_code']

                systemIdToSecurity[systemId] = {
                    'rating': security,
                    'security_code': security_code
                }

    # Write the System ID to Security Mapping to the file
    with open('resources/systemIdToSecurity.json', 'w', encoding='utf-8') as f:
        json.dump(systemIdToSecurity, f)


if __name__ == '__main__':
    generate_security_details()