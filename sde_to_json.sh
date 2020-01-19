#!/bin/bash

wget -O page https://developers.eveonline.com/resource/resources

currentrev=$(grep "https.*sde.*zip" page | awk -F '-' '{print $2}')
echo 'Current resources revision :' $currentrev
lastrev=$(git describe --abbrev=0 --tags)
if [[ $(git log -1 --pretty=%B) == *"$currentrev"* ]]
then
    echo "Already lastest resources"
    exit
fi
echo 'Latest resources revision was :' $lastrev
echo 'Building resources files for new revision' $currentrev
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
git commit -m "Update DB to $currentrev"
git checkout -b temp
git checkout -B master temp
git push --quiet --set-upstream origin-ssh master
