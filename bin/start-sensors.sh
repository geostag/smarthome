#!/bin/bash

_basedir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
_basedir=`dirname $_basedir`

logdir=logs

cd ${_basedir} || exit 2
. env.sh

test -d $logdir || mkdir $logdir

stamp=`date '+%Y%m%d-%H%M%S'`

for sen in $SMARTHOME_SENSORS; do
  pkill -u $USERID -f "$sen".py
  sleep 2
  python bin/${sen}.py > ${logdir}/${sen}-${stamp}.log 2>&1 </dev/null & 
  echo $sen done
done
