#!/bin/bash

wget -O page https://developers.eveonline.com/resource/resources

currentrev=$(grep "https.*sde.*zip" page | awk -F '-' '{print $2}')
echo 'Current resources revision :' $currentrev
if [[ $(git log -1 --pretty=%B) == *"$currentrev"* ]]
then
    echo "Already lastest resources"
    exit
fi
echo 'Latest commit was :' $(git log -1 --pretty=%B)
echo 'Building resources files for revision' $currentrev
git config --global user.email "$GH_USER_EMAIL"
git config --global user.name "$GH_USER_NAME"
git remote add origin-ssh git@github.com:$GH_REPO
mkdir -p resources
python3 toJSON.py
git add resources/mapRegions.json
git add resources/staStations.json
git add resources/mapRegionJumps.json
git add resources/mapConstellationJumps.json
git add resources/mapSolarSystemJumps.json
git add resources/invTypes.json
git commit -m "Up to date DB with resources $currentrev"
git checkout -b temp
git checkout -B $TRAVIS_BRANCH temp
git push --quiet --set-upstream origin-ssh $TRAVIS_BRANCH
