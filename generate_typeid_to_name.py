'''
Generates the Type ID to Name Mapping from invTypes.json
'''
import json
import os
import sys

def generate_typeid_to_name():
    '''Generates the Type ID to Name Mapping from invTypes.json'''

    # Get the path to the invTypes.json file
    invtypes_json = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources/invTypes.json')

    # Load the invTypes.json file
    with open(invtypes_json, 'r', encoding='utf-8') as invtypes_file:
        invtypes = json.load(invtypes_file)

    # Generate the Type ID to Name Mapping
    typeIDToName = {}
    for invType in invtypes:
        typeId = invType['typeID']
        name = invType['typeName']
        volume = invType['volume']
        typeIDToName[typeId] = {
            'name': name,
            'volume': volume
        }
    # Write the Type ID to Name Mapping to the file
    with open('resources/typeIDToName.json', 'w', encoding='utf-8') as f:
        json.dump(typeIDToName, f)

if __name__ == '__main__':
    generate_typeid_to_name()