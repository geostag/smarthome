#!/bin/bash

sen="$1"

_basedir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
_basedir=`dirname $_basedir`

logdir=logs

cd ${_basedir} || exit 2
. env.sh

if [ ! -f "bin/${sen}.py" ]; then
    echo "sensor '$sen' not found"
    exit 2
fi

test -d $logdir || mkdir $logdir

stamp=`date '+%Y%m%d-%H%M%S'`

pkill -u $USERID -f "$sen".py
sleep 2
python bin/${sen}.py > ${logdir}/${sen}-${stamp}.log 2>&1 </dev/null & 
echo $sen done
