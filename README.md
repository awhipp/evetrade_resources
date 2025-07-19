# EVE Trade Resources

[![Convert SDE to JSON](https://github.com/awhipp/evetrade_resources/actions/workflows/download.yml/badge.svg)](https://github.com/awhipp/evetrade_resources/actions/workflows/download.yml)

## Functions

### Automatic conversion of EVE Online's Static Data Export (SDE) to relevant JSON files for use by the [EveTrade](https://github.com/awhipp/evetrade) application.

Files available in code (get raw format):

* resources/invTypes.json
* resources/mapConstellationJumps.json
* resources/mapRegionJumps.json
* resources/mapRegions.json
* resources/mapSolarSystemJumps.json
* resources/regionList.json
* resources/staStations.json
* resources/stationIdToName.json
* resources/stationList.json
* resources/mapRegions.json
* resources/structureInfo.json
* resources/structureList.json

This CI pipeline builds the resources on a daily schedule via a CRON job and eventually is replicated to S3.

### Download and synchronize market volume data with a Redis Cache to prevent hitting API Rate Limits when querying for 100+ records at once

This CI pipeline synchronizes with Redis on an hourly cadence.

## Script Definitions

* `generate_jump_data.py` creates a set of JSON files which represents jump data from all system routes. This data is backed up and maintained in AWS S3 after an intial ingestion.
* `ingest_jump_data.py` ingests the JSON files generated into Elasticsearch for query by hauling services.
* `generate_citadel_data.py` creates a set of JSON files which represents citadel data from all citadels in the game. This data is backed up and maintained in AWS S3 after an intial ingestion.
* `generate_resources.sh` is used to pull the EVE SDE into JSON format and then executes `toJSON.py` to convert it accordingly and create a release.
