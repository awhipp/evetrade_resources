#!/bin/bash

wget -O page https://developers.eveonline.com/resource/resources

link=$(grep "https.*sde.*zip" page | awk -F '"' '{print $2}')
currentrev=$(curl -s -v -X HEAD $link 2>&1 | grep '< Last-Modified:' | awk -F ':' '{print $2":"$3":"$4}' | xargs -0 date +"%Y%m%d" -d)

echo 'Latest commit was :' $(git log -1 --pretty=%B)
echo 'Building resources files for revision' $currentrev

git config --global user.email "$GH_USER_EMAIL"
git config --global user.name "$GH_USER_NAME"

mkdir -p resources
python3 sde_to_json.py
python3 generate_citadel_data.py
python3 generate_typeid_to_name.py
python3 generate_systemid_to_security.py
git add resources/*

git commit -m "Up to date DB with resources $currentrev"
git push
