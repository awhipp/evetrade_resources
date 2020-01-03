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
        print('Load JSON')
        with open('invNames.json') as infile:
            inv_names = json.load(infile)
    else:
        print('Load YAML')
        with open(r'sde/bsd/invNames.yaml') as infile:
            inv_names = yaml.load(infile, Loader = Loader)

        with open('invNames.json', 'w') as outfile:
            json.dump(inv_names, outfile)

    print("Importing region static")
    regions = glob.glob(os.path.join('sde', 'fsd', 'universe', '*', '*', 'region.staticdata'))
    for region_file in regions:
        region = {}
        head, tail = os.path.split(region_file)
        with open(region_file,'r') as region_yaml:
            regiony = yaml.load(region_yaml, Loader = Loader)
        if int(regiony['regionID']) > 11000000 and int(regiony['regionID']) < 14000000:
            continue
        print("Importing Region {}".format(head))
        for item in inv_names:
            if item['itemID'] == regiony['regionID']:
                region_name = item['itemName']
                break
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

    map_region = sorted(map_regions, key = lambda i: i['regionID'])
    with open('resources/mapRegions.json', 'w') as outfile:
        json.dump(map_region, outfile, separators = (',', ':'))

    print("Converting stations data")
    with open(r'sde/bsd/staStations.yaml') as infile:
        with open('resources/staStations.json', 'w') as outfile:
            json.dump(yaml.load(infile, Loader = Loader), outfile, separators = (',', ':'))

getResources()
importYaml()
