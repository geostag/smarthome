#!/bin/bash

docker compose -f docker-compose-prod.yml logs sensors

docker compose -f docker-compose-prod.yml up -d --pull always --force-recreate sensors

git pull
