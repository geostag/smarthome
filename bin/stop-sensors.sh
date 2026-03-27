#!/bin/bash

_basedir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
_basedir=`dirname $_basedir`

cd ${_basedir} || exit 2
. env.sh

for sen in $SMARTHOME_SENSORS; do
    stop-sensor.sh "$sen"
done
