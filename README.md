# EVE Trade Resources

[![Build Status](https://travis-ci.org/awhipp/evetrade_resources.svg?branch=master)](https://travis-ci.org/awhipp/evetrade_resources)

Automatic conversion of official database to JSON format usefull for EveTrade website.

Files available in code (get raw format):

* resources/staStations.json
* resources/mapRegions.json

To get it to work after forking follow instructions on https://github.com/alrra/travis-scripts/blob/master/docs/github-deploy-keys.md.

Needed steps are :

1. Enable Travis CI
2. Set up the SSH keys
  
    Get the 2 environmnent variables and modify the file `.travis.yml` line 15-16 with the name of the encrypted files.
    **Do not do step 2.6**
3. Add the environment variables `GH_USER_NAME` and `GH_USER_EMAIL`
  
    Get the secure key value and copy it to `.travis.yml` line 3

Add an environment variable `GH_REPO` in Travis CI which value is the Github repo : `<username>/<repo.git>` and which can be visible in the log.

Commit and push... Let's the magic operate.
