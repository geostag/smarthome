#!/bin/bash

update_file()
{
    local FILE="$1"
    local FILE_T="${FILE}.$(date '+%Y%m%d%H%M%S')"

    curl -s -k -o "$FILE_T" \
        "https://raw.githubusercontent.com/geostag/smarthome/refs/heads/main/$FILE" \
        && chmod u+rx "$FILE_T" \
        && mv "$FILE_T" "$FILE"
}

# update dockerfile
update_file docker-compose-prod.yml

# read logs
docker compose -f docker-compose-prod.yml logs sensors

# update containers
docker compose -f docker-compose-prod.yml up -d --pull always --force-recreate sensors

# update this script
update_file "$(basename "$0")"