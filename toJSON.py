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

class MyHTMLParser(HTMLParser):

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
           for name, value in attrs:
               if name == 'href' and 'tranquility' in value:
                   self.resources_file_link = value


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
        head, tail = os.path.split(region_file)
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

        constellation_files = glob.glob(os.path.join(head, '*', 'constellation.staticdata'))
        for constellation_file in constellation_files:
            head, tail = os.path.split(constellation_file)
            with open(constellation_file,'r') as constellation_yaml:
                constellationy = yaml.load(constellation_yaml, Loader = Loader)
            map_constellations.append((regiony['regionID'], constellationy['constellationID']))

            solarsystem_files = glob.glob(os.path.join(head, '*', 'solarsystem.staticdata'))
            for solarsystem_file in solarsystem_files:
                with open(solarsystem_file,'r') as solarsystem_yaml:
                    solarsystemy = yaml.load(solarsystem_yaml, Loader = Loader)
                for stargate, data in solarsystemy['stargates'].items():
                    stargates[stargate] = (regiony['regionID'], data['destination'])

    map_region = sorted(map_regions, key = lambda i: i['regionID'])
    with open('resources/mapRegions.json', 'w') as outfile:
        json.dump(map_region, outfile, separators = (',', ':'))

    print("Converting stations data")
    with open(r'sde/bsd/staStations.yaml') as infile:
        with open('resources/staStations.json', 'w') as outfile:
            json.dump(yaml.load(infile, Loader = Loader), outfile, separators = (',', ':'))

    print("Creating region jumps DB")
    regions_jump = []
    for stargate, data in stargates.items():
        if data[0] != stargates[data[1]][0]:
            regions_jump.append({'fromRegionID': data[0], 'toRegionID': stargates[data[1]][0]})
    map_region_jumps = [i for n, i in enumerate(regions_jump) if i not in regions_jump[n + 1:]]
    map_region_jumps = sorted(map_region_jumps, key = lambda i: i['toRegionID'])
    map_region_jumps = sorted(map_region_jumps, key = lambda i: i['fromRegionID'])
    with open('resources/mapRegionJumps.json', 'w') as outfile:
        json.dump(map_region_jumps, outfile, separators = (',', ':'))

getResources()
importYaml()
