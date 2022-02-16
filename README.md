# EVE Trade Resources

[![Convert SDE to JSON](https://github.com/awhipp/evetrade_resources/actions/workflows/download.yml/badge.svg)](https://github.com/awhipp/evetrade_resources/actions/workflows/download.yml)

Automatic conversion of EVE Online's official database to JSON format for use with the SPA [EveTrade](https://github.com/awhipp/evetrade).

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

The CI pipeline builds the resources on a monthly schedule via a CRON job.
