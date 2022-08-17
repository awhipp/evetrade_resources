# EVE Trade Resources

[![Convert SDE to JSON](https://github.com/awhipp/evetrade_resources/actions/workflows/download.yml/badge.svg)](https://github.com/awhipp/evetrade_resources/actions/workflows/download.yml)

[![Synchronize Redis Cache (Historical Volume)](https://github.com/awhipp/evetrade_resources/actions/workflows/redis-push-volume-data.yml/badge.svg)](https://github.com/awhipp/evetrade_resources/actions/workflows/redis-push-volume-data.yml)

[![Synchronize Redis Cache (Route Jump Data)](https://github.com/awhipp/evetrade_resources/actions/workflows/redis-push-jump-data.yml/badge.svg)](https://github.com/awhipp/evetrade_resources/actions/workflows/redis-push-jump-data.yml)

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


