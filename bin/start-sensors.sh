#!/bin/bash

_basedir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
_basedir=`dirname $_basedir`

logdir=logs

cd ${_basedir} || exit 2
. env.sh

for sen in $SMARTHOME_SENSORS; do
    daemon-sensors.sh "$sen" >/dev/null 2>&1 </dev/null &
    echo $sen done
done
