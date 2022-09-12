# EVE Trade Resources

[![Convert SDE to JSON](https://github.com/awhipp/evetrade_resources/actions/workflows/download.yml/badge.svg)](https://github.com/awhipp/evetrade_resources/actions/workflows/download.yml)

[![Synchronize Redis Cache (Historical Volume)](https://github.com/awhipp/evetrade_resources/actions/workflows/sync-volume-data.yml/badge.svg)](https://github.com/awhipp/evetrade_resources/actions/workflows/sync-volume-data.yml)

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

This CI pipeline builds the resources on a daily schedule via a CRON job.

### Download and synchronize market volume data with a Redis Cache to prevent hitting API Rate Limits when querying for 100+ records at once

This CI pipeline synchronizes with Redis on an hourly cadence.

## Script Definitions

* `generate_historic_volume.py` is executed by GitHub Actions in order to ingest historical region volume data into REDIS on an hourly cadence.
* `generate_jump_data.py` creates a set of JSON files which represents jump data from all system routes. This data is backed up and maintained in AWS S3 after an intial ingestion.
* `ingest_jump_data.py` ingests the JSON files generated into Elasticsearch for query by hauling services.
* `sde_to_json.sh` is used to pull the EVE SDE into JSON format and then executes `toJSON.py` to convert it accordingly and create a release.