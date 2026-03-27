#!/bin/bash

sen="$1"

_basedir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
_basedir=`dirname $_basedir`

cd ${_basedir} || exit 2
. env.sh

stop-sensor.sh "$sen"
start-sensor.sh "$sen"
