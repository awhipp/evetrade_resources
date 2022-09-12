import os
import json
import time

from elasticsearch import Elasticsearch, helpers

start_time = time.time()

routes = []

file_paths = []

index_name = 'evetrade_jump_data'
ES_HOST = os.getenv('ES_HOST', 'localhost')

es_client = Elasticsearch(ES_HOST)

def delete_index():
    '''
    Deletes an index from the Elasticsearch instance
    '''
    print(f'Deleting index {index_name}')
    if index_name and es_client.indices.exists(index_name):
        es_client.indices.delete(index_name)

def create_index():
    '''
    Creates the index for the data sync service
    '''    
    print(f'Creating new index {index_name}')

    es_index_settings = {
	    "settings" : {
            "index.max_result_window": 2000000
	    }
    }

    es_client.indices.create(index = index_name, body = es_index_settings)
    return index_name

def Merge(dict1, dict2):
    dict1.update(dict2)
    return dict1

for root, dirs, files in os.walk('data'):
    for file in files:
        if file.endswith('.json'):
            file_paths.append(os.path.join(root, file))

delete_index()
create_index()

completed_keys = set()

for idx, file in enumerate(file_paths):
    with open(f'{file}', 'r', encoding='utf-8') as fp:
        data = json.load(fp)
        data['last_modified'] = start_time
        key = file.replace('.json', '').split('\\')[-1].split('-')

        try:
            key1 = f'{key[0]}-{key[1]}'
            if key1 not in completed_keys:
                routes.append(Merge({
                    'route': key1
                }, data))
                completed_keys.add(key1)

            key2 = f'{key[1]}-{key[0]}'
            if key[0] != key[1]:
                if key2 not in completed_keys:
                    routes.append(Merge({
                        'route': key2
                    }, data))
                    completed_keys.add(key2)

        except Exception as e:
            print(e)
            print(f'Error with {file}')
            continue

    if idx % 10000 == 0:
        print(f'{round(100*(idx/len(file_paths)),10)}% Complete')

print(f'Ingesting {len(routes)} orders into {index_name}')
helpers.bulk(es_client, routes, index=index_name, request_timeout=30)
es_client.indices.refresh(index=index_name)

print(f'Finished in {time.time() - start_time} seconds')