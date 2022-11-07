'''
Scheduled job that runs 12 times a day and populates a redis cache
with historic volume data for all types in all regions.
'''

import os
import time
import asyncio
import traceback
import redis
import aiohttp
import requests

BATCHES = 10

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_PW = os.getenv('REDIS_PW', 'password')

FILE_ENDPOINT = os.getenv('FILE_ENDPOINT', '')

r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PW, decode_responses=True)

ONE_WEEK = 60 * 60 * 24 * 7

def create_volume_endpoint(region_id, type_id):
    '''
    Creates the endpoint for the volume data
    '''
    return f'https://esi.evetech.net/latest/markets/{region_id}/history/?datasource=tranquility&type_id={type_id}&language=en-us' # pylint: disable=line-too-long

def get_request(url):
    '''
    Helper functions for sending get requests
    '''
    response = requests.get(url)
    return response.json()

regionList = get_request(FILE_ENDPOINT + 'regionList.json')[1:]
universeList = get_request(FILE_ENDPOINT + 'universeList.json')

async def process_region(pipe, session, type_id, volume_endpoint, region_id):
    '''
    Processes a single region and pulls historic volume data into Redis
    '''
    try:
        async with session.get(volume_endpoint, timeout=60) as response:
            volume_data = await response.json(content_type=None)
            rate_limit = int(response.headers['X-Esi-Error-Limit-Remain'])

            if rate_limit < BATCHES*2:
                seconds = 20
                print(f'!! Rate limit reached for {type_id}. Waiting {seconds} seconds.')
                time.sleep(seconds)


            volume_1d = 0
            volume_14d = 0
            volume_30d = 0

            if 'error' not in volume_data and len(volume_data) > 0:
                volume_1d = volume_data[len(volume_data) - 1]['volume']

                if len(volume_data) > 14:
                    for idx in range(1, 15):
                        volume_14d += volume_data[len(volume_data) - idx]['volume']
                        volume_14d = int(volume_14d / 14)
                else:
                    volume_14d = 0

                if len(volume_data) > 30:
                    for idx in range(1, 31):
                        volume_30d += volume_data[len(volume_data) - idx]['volume']
                        volume_30d = int(volume_30d / 30)
                else:
                    volume_30d = 0

                # Sending to Redis (regionid-typeid is mapped to comma-separated volume data)
                # Tried hashset but it was too slow and stored too much data
                # Expires after one week
                pipe.set(
                    name = f'{region_id}-{type_id}',
                    value = f'{volume_1d},{volume_14d},{volume_30d}',
                    ex = ONE_WEEK
                )

                return { f'{region_id}-{type_id}': f'{volume_1d},{volume_14d},{volume_30d}' }
            else:
                return { f'{region_id}-{type_id}': '0,0,0' }

    except Exception: # pylint: disable=broad-except
        print(traceback.format_exc())
        return { f'{region_id}-{type_id}': '0,0,0' }


def execute_request(url, attempts=0):
    '''
    Helper function for sending get requests
    '''

    if attempts > 5:
        raise Exception('Too many attempts were made.')

    try:
        response = requests.get(url)
        response.raise_for_status()
        pages = int(response.headers['X-Pages'])
        return [
            response.json(),
            pages
        ]
    except Exception: # pylint: disable=broad-except
        print(traceback.format_exc())
        time.sleep(10)
        return execute_request(url, attempts + 1)

def get_all_types(region_id):
    '''
    Gets all active types in a region
    '''

    response_arr = execute_request(f'https://esi.evetech.net/latest/markets/{region_id}/types/?datasource=tranquility&language=en-us') # pylint: disable=line-too-long
    type_ids = response_arr[0]
    pages = response_arr[1]

    for page in range(2, pages+1):
        type_ids += execute_request(
            f'https://esi.evetech.net/latest/markets/{region_id}/types/?datasource=tranquility&language=en-us&page={page}' # pylint: disable=line-too-long
        )[0]

    return type_ids


def chunks(lst, length):
    """
    Returns successive length-sized chunks from lst.
    """
    return [lst[i:i + length] for i in range(0, len(lst), length)]


async def main():
    '''
    Main function
    '''
    total_results = 0
    initial_time = time.time()

    async with aiohttp.ClientSession() as session:

        for region_idx, region_name in enumerate(regionList):
            print(f'Region: {region_name}')
            name = region_name.lower()

            start_time = time.time()

            universe_item = universeList[name]

            region_id = universe_item['id']

            type_ids = get_all_types(region_id)

            total_results += len(type_ids)
            type_ids = chunks(type_ids, BATCHES)

            tasks = []

            region_pipeline = r.pipeline()

            for batch in type_ids:
                for type_id in batch:
                    tasks.append(asyncio.ensure_future(
                        process_region(region_pipeline, session, type_id, create_volume_endpoint(region_id, type_id), region_id) # pylint: disable=line-too-long
                    ))

                await asyncio.gather(*tasks)

            region_pipeline.execute()

            print(f'-- Execution Time: {round(time.time() - start_time, 2)} seconds // {round((region_idx / len(regionList)) * 100, 2)}% complete') # pylint: disable=line-too-long

        print(f'Total results: {total_results}')
        print(f'Total time: {round(time.time() - initial_time, 2)} seconds')

        
# Fix for Python 3.10+
io_loop = None

try:
    io_loop = asyncio.get_running_loop()
except RuntimeError:
    io_loop = asyncio.new_event_loop()
asyncio.set_event_loop(io_loop)

asyncio.get_running_loop().run_until_complete(main())
