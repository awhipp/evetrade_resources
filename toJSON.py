# -*- coding: utf-8 -*-

import sys
import os
import glob
import requests
import zipfile
import io

from html.parser import HTMLParser


import yaml
try:
	from yaml import CLoader as Loader
	print('Using CLoader')
except ImportError:
	from yaml import Loader
	print('Using Python Loader')
import json

resources_link = "https://developers.eveonline.com/resource/resources"
map_regions = []
stargates = {}
map_region_jumps = []
map_constellations = []
map_constellation_jumps = []
map_solarsystem_jumps = []
inv_types = []
universeList = {}
stationList = [""]
regionList = [""]
stationIdToName = {}

class MyHTMLParser(HTMLParser):

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
           for name, value in attrs:
               if name == 'href' and 'sde.zip' in value:
                   self.resources_file_link = value


#
# Mapping function to shortened names of these popular stations
#
def getTradeHubName(stationName):
    if (stationName == "Jita IV - Moon 4 - Caldari Navy Assembly Plant"):
        return "Jita"
    elif (stationName == "Amarr VIII (Oris) - Emperor Family Academy"):
        return "Amarr"
    elif (stationName == "Rens VI - Moon 8 - Brutor Tribe Treasury"):
        return "Rens"
    elif (stationName == "Dodixie IX - Moon 20 - Federation Navy Assembly Plant"):
        return "Dodixie"
    elif (stationName == "Hek VIII - Moon 12 - Boundless Creation Factory"):
        return "Hek"

    return stationName

def getResources():
    if not os.path.exists('sde'):
        resources_page = requests.get(resources_link)
        parser = MyHTMLParser()
        parser.feed(resources_page.content.decode())
        print(parser.resources_file_link)
        resources_file = requests.get(parser.resources_file_link)
        if resources_file.ok:
            resources_zip = zipfile.ZipFile(io.BytesIO(resources_file.content))
            resources_zip.extractall()
    else:
        print("Folder already exists")

def importYaml():
    print("Importing Universe Data")

    if os.path.exists('invNames.json'):
        print('Load invNames JSON')
        with open('invNames.json') as infile:
            inv_names = json.load(infile)
    else:
        print('Load invNames YAML')
        with open(r'sde/bsd/invNames.yaml') as infile:
            inv_names = yaml.load(infile, Loader = Loader)

        with open('invNames.json', 'w') as outfile:
            json.dump(inv_names, outfile)

    print("Importing region static data")
    region_files = glob.glob(os.path.join('sde', 'fsd', 'universe', 'eve', '*', 'region.staticdata'))
    for region_file in region_files:
        region = {}
        headr, tail = os.path.split(region_file)
        with open(region_file,'r') as region_yaml:
            regiony = yaml.load(region_yaml, Loader = Loader)
        for item in inv_names:
            if item['itemID'] == regiony['regionID']:
                region_name = item['itemName']
                break
        print("Importing Region {}".format(region_name))
        region['regionID'] = regiony['regionID']
        region['regionName'] = region_name
        region['x'] = regiony['center'][0]
        region['y'] = regiony['center'][1]
        region['z'] = regiony['center'][2]
        region['xMax'] = regiony['max'][0]
        region['yMax'] = regiony['max'][1]
        region['zMax'] = regiony['max'][2]
        region['xMin'] = regiony['min'][0]
        region['yMin'] = regiony['min'][1]
        region['zMin'] = regiony['min'][2]
        region['factionID'] = regiony.get('factionID')
        map_regions.append(region)

        constellation_files = glob.glob(os.path.join(headr, '*', 'constellation.staticdata'))
        for constellation_file in constellation_files:
            headc, tail = os.path.split(constellation_file)
            with open(constellation_file,'r') as constellation_yaml:
                constellationy = yaml.load(constellation_yaml, Loader = Loader)
            map_constellations.append((regiony['regionID'], constellationy['constellationID']))

            solarsystem_files = glob.glob(os.path.join(headc, '*', 'solarsystem.staticdata'))
            for solarsystem_file in solarsystem_files:
                with open(solarsystem_file,'r') as solarsystem_yaml:
                    solarsystemy = yaml.load(solarsystem_yaml, Loader = Loader)
                for stargate, data in solarsystemy['stargates'].items():
                    stargates[stargate] = (regiony['regionID'], constellationy['constellationID'], solarsystemy['solarSystemID'], data['destination'])

    map_region = sorted(map_regions, key = lambda i: i['regionID'])
    with open('resources/mapRegions.json', 'w') as outfile:
        json.dump(map_region, outfile, separators = (',', ':'))

    print("Converting stations data")
    with open(r'sde/bsd/staStations.yaml') as infile:
        with open('resources/staStations.json', 'w') as outfile:
            sta_stations = yaml.load(infile, Loader = Loader)
            json.dump(sta_stations, outfile, separators = (',', ':'))

    print("Creating region / constellation / solar system jumps DB")
    regions_jump = []
    constellations_jump = []
    solarsystems_jump = []
    for stargate, data in stargates.items():
        if data[0] != stargates[data[3]][0]:
            regions_jump.append({'fromRegionID': data[0], 'toRegionID': stargates[data[3]][0]})
        if data[1] != stargates[data[3]][1]:
            constellations_jump.append({"fromRegionID":data[0],"fromConstellationID":data[1],"toConstellationID":stargates[data[3]][1],"toRegionID":stargates[data[3]][0]})
        solarsystems_jump.append({"fromRegionID":data[0],"fromConstellationID":data[1],"fromSolarSystemID":data[2],"toSolarSystemID":stargates[data[3]][2],"toConstellationID":stargates[data[3]][1],"toRegionID":stargates[data[3]][0]})

    map_region_jumps = [i for n, i in enumerate(regions_jump) if i not in regions_jump[n + 1:]]
    map_region_jumps = sorted(map_region_jumps, key = lambda i: i['toRegionID'])
    map_region_jumps = sorted(map_region_jumps, key = lambda i: i['fromRegionID'])
    with open('resources/mapRegionJumps.json', 'w') as outfile:
        json.dump(map_region_jumps, outfile, separators = (',', ':'))
    map_constellation_jumps = [i for n, i in enumerate(constellations_jump) if i not in constellations_jump[n + 1:]]
    map_constellation_jumps = sorted(map_constellation_jumps, key = lambda i: i['toRegionID'])
    map_constellation_jumps = sorted(map_constellation_jumps, key = lambda i: i['fromRegionID'])
    map_constellation_jumps = sorted(map_constellation_jumps, key = lambda i: i['toConstellationID'])
    map_constellation_jumps = sorted(map_constellation_jumps, key = lambda i: i['fromConstellationID'])
    with open('resources/mapConstellationJumps.json', 'w') as outfile:
        json.dump(map_constellation_jumps, outfile, separators = (',', ':'))
    map_solarsystem_jumps = sorted(solarsystems_jump, key = lambda i: i['toRegionID'])
    map_solarsystem_jumps = sorted(map_solarsystem_jumps, key = lambda i: i['fromRegionID'])
    map_solarsystem_jumps = sorted(map_solarsystem_jumps, key = lambda i: i['toConstellationID'])
    map_solarsystem_jumps = sorted(map_solarsystem_jumps, key = lambda i: i['fromConstellationID'])
    map_solarsystem_jumps = sorted(map_solarsystem_jumps, key = lambda i: i['toSolarSystemID'])
    map_solarsystem_jumps = sorted(map_solarsystem_jumps, key = lambda i: i['fromSolarSystemID'])
    with open('resources/mapSolarSystemJumps.json', 'w') as outfile:
        json.dump(map_solarsystem_jumps, outfile, separators = (',', ':'))

    print("Importing items data")
    if os.path.exists('invTypes.json'):
        print('Load invTypes JSON')
        with open('invTypes.json') as infile:
            inv_typesy = json.load(infile)
    else:
        print('Load invTypes YAML')
        with open(r'sde/fsd/typeIDs.yaml') as infile:
            inv_typesy = yaml.load(infile, Loader = Loader)

        with open('invTypes.json', 'w') as outfile:
            json.dump(inv_typesy, outfile)
    
    for item_id, data in inv_typesy.items():
        inv_type = {}
        inv_type['typeID'] = item_id
        inv_type['typeName'] = data.get('name').get('en')
        inv_type['volume'] = data.get('volume')

        inv_types.append(inv_type)

    with open('resources/invTypes.json', 'w') as outfile:
        json.dump(inv_types, outfile, separators = (',', ':'))

    for station in sta_stations:
        stationName = station['stationName']
        #add trade hubs for easy of use
        tradeHubName = getTradeHubName(stationName)
        if (stationName != tradeHubName):
            lowerCaseStationName = tradeHubName.lower()

            universeList[lowerCaseStationName] = {}
            universeList[lowerCaseStationName]['region'] = station['regionID']
            universeList[lowerCaseStationName]['station'] = station['stationID']
            universeList[lowerCaseStationName]['system'] = station['solarSystemID']
            universeList[lowerCaseStationName]['constellation'] = station['constellationID']
            universeList[lowerCaseStationName]['security'] = station['security']
            universeList[lowerCaseStationName]['name'] = tradeHubName
            stationList.append(tradeHubName)

        lowerCaseStationName = stationName.lower()
        universeList[lowerCaseStationName] = {}
        universeList[lowerCaseStationName]['region'] = station['regionID']
        universeList[lowerCaseStationName]['station'] = station['stationID']
        universeList[lowerCaseStationName]['system'] = station['solarSystemID']
        universeList[lowerCaseStationName]['constellation'] = station['constellationID']
        universeList[lowerCaseStationName]['security'] = station['security']
        universeList[lowerCaseStationName]['name'] = stationName
        stationList.append(stationName)
        stationList.sort()
        stationIdToName[station['stationID']] = stationName

    for region in map_region:
        regionName = region['regionName']
        lcRegionName = regionName.lower()
        universeList[lcRegionName] = {}
        universeList[lcRegionName]['name'] = region['regionName']
        universeList[lcRegionName]['id'] = region['regionID']
        universeList[lcRegionName]['around'] = []
        regionList.append(regionName)
        regionList.sort()
    
    i = 0
    j = 0
    for jump in map_region_jumps:
        get_it = False
        while i  < len(map_region):
            if jump['fromRegionID'] == map_region[i]['regionID']:
                while j < len(map_region):
                    if jump['toRegionID'] == map_region[j]['regionID']:
                        universeList[map_region[i]['regionName'].lower()]['around'].append(map_region[j]['regionName'].lower())
                        get_it = True
                        break
                    else:
                        j += 1
            else:
                i += 1
                j = 0
            if get_it:
                break

    with open('resources/universeList.json', 'w') as outfile:
        json.dump(universeList, outfile, separators = (',', ':'))
    with open('resources/stationList.json', 'w') as outfile:
        json.dump(stationList, outfile, separators = (',', ':'))
    with open('resources/stationIdToName.json', 'w') as outfile:
        json.dump(stationIdToName, outfile, separators = (',', ':'))
    with open('resources/regionList.json', 'w') as outfile:
        json.dump(regionList, outfile, separators = (',', ':'))

getResources()
importYaml()
