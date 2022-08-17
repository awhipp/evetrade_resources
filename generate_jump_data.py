'''
Scheduled job that runs every 20min and populates a redis cache
with jump data for all types in all systems.
'''

import os
import time
import asyncio
import traceback
import redis
import aiohttp
import requests

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_PW = os.getenv('REDIS_PW', 'password')

r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PW, decode_responses=True)

safety = [
    'shortest', 'secure', 'insecure'
]

system_ids = []

completed_keys = set()

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
    return response.json()

systemSecurity = get_request('https://evetrade.space/api/resource?file=systemIdToSecurity.json')
systemList = [30004684] # Jita First
for system in systemSecurity:
    systemList.append(int(system))

def add_to_pipe(pipe, start, end, jump_type, value):
    '''
    Helper function for adding to a pipeline
    '''

    key = f'{start}-{end}'

    pipe.hset(key, jump_type, value)


def get_all_subsets(arr, pipe, jump_type):
    '''
    Returns all subsets of an array
    '''

    newarr = []

    for idx1, arri in enumerate(arr):
        if idx1 < len(arr) :
            subarr = [arri]
            for idx2, arrj in enumerate(arr):
                if idx2 > idx1:
                    subarr.append(arrj)
            if len(subarr) > 1:
                newarr.append(subarr)

    for route in newarr:
        jumps = len(route)
        system_a = route[0]
        system_b = route[-1]

        add_to_pipe(pipe, system_a, system_b, jump_type, jumps)


async def process(pipe, session, from_system, to_system, jump_type):
    '''
    Processes a single jump set and pushes data into Redis
    '''
    try:
        existing_result = r.hget(f'{from_system}-{to_system}', jump_type) or r.hget(f'{to_system}-{from_system}', jump_type)

        if existing_result is None:
            jump_endpoint = create_jump_endpoint(from_system, to_system, jump_type)

            async with session.get(jump_endpoint, timeout=60) as response:

                if from_system == to_system:
                    add_to_pipe(pipe, from_system, to_system, jump_type, 0)
                    return
                else:
                    jump_data = await response.json(content_type=None)

                    rate_limit = int(response.headers['X-Esi-Error-Limit-Remain'])

                    # Sending to Redis for all subsets of routes
                    get_all_subsets(jump_data, pipe, jump_type)

                return rate_limit
        else:
            return 100

    except Exception: # pylint: disable=broad-except
        print(traceback.format_exc())
        return 100


def chunks(lst, length):
    """
    Returns successive length-sized chunks from lst.
    """
    return [lst[i:i + length] for i in range(0, len(lst), length)]


async def main(system_id_from):
    '''
    Main function
    '''

    async with aiohttp.ClientSession() as session:

        print(f'System: {system_id_from}')
        start_time = time.time()

        for idx, system_id_to in enumerate(systemList):
            if idx != 0 and idx % 100 == 0:
                print(f'{idx} of {len(systemList)} systems completed taking a break...')
                time.sleep(15)

            print(f'-- {idx+1} of {len(systemList)} System To: {system_id_to}')

            system_pipeline = r.pipeline()

            tasks = []

            for jump_type in safety:
                
                existing_result = r.hget(
                        f'{system_id_from}-{system_id_to}',
                        jump_type
                    ) or r.hget(
                        f'{system_id_from}-{system_id_to}',
                        jump_type
                    )

                if existing_result is not None:
                    continue

                tasks.append(asyncio.ensure_future(
                    process(system_pipeline, session, system_id_from, system_id_to, jump_type)
                ))

            rate_limits = await asyncio.gather(*tasks)
            system_pipeline.execute()

            rate_limit_hit = 100
            for rate_limit in rate_limits:
                if rate_limit is not None and rate_limit < 10:
                    rate_limit_hit = rate_limit
                    break

            if rate_limit_hit <= 10:
                print(f'!! Rate limit {rate_limit_hit} reached. Sleeping for a minute.') # pylint: disable=line-too-long
                time.sleep(60)

        print(f'---- Execution Time: {round(time.time() - start_time, 2)} seconds') # pylint: disable=line-too-long

        r.set('last_system_id', int(system_id_from))

system_id = r.get('last_system_id')

print(f'Last System ID: {system_id}')

NEXT_IDX = 0

if system_id is None:
    system_id = systemList[NEXT_IDX]
else:
    NEXT_IDX = systemList.index(int(system_id)) + 1
    if NEXT_IDX >= len(systemList):
        NEXT_IDX = 0 # pylint: disable=invalid-name

system_id = systemList[NEXT_IDX]

print(f'Now Running Against System #{NEXT_IDX+1} of {len(systemList)}: {system_id}')

asyncio.get_event_loop().run_until_complete(main(system_id))
