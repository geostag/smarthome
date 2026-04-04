#!/bin/bash

# execute this script once to initially set up influxdb and grafana
. .env

# create influx buckets; bucket "smarthome" is already created by docker-setup
docker exec sh-influxdb influx bucket create --org "$INFLUX_ORG" --name "$INFLUX_DERIVED_BUCKET"   --retention "$INFLUX_DERIVED_RETENTION"
docker exec sh-influxdb influx bucket create --org "$INFLUX_ORG" --name "$INFLUX_LONGRANGE_BUCKET" --retention "$INFLUX_LONGRANGE_RETENTION"

# create access tokens for the influx buckets
docker exec sh-influxdb influx auth create --org "$INFLUX_ORG"
