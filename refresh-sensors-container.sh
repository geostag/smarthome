#!/bin/bash

# read logs
docker compose -f docker-compose-prod.yml logs sensors

# update containers
docker compose -f docker-compose-prod.yml up -d --pull always --force-recreate sensors

# update this script
FILE=`basename $0`
FILE_T="$FILE".`date "+%Y%m%d%H%M%S`

curl -k -o "$FILE_T" https://raw.githubusercontent.com/geostag/smarthome/refs/heads/main/"$FILE" \
&& chmod u+rx "$FILE_T" \
&& mv "$FILE_T" "$FILE
