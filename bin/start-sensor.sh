#!/bin/bash

_basedir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
_basedir=`dirname $_basedir`

cd ${_basedir} || exit 2
. env.sh

sen="$1"
stamp=`date '+%Y%m%d-%H%M%S'`

test -d ${sh_logdir} || mkdir ${sh_logdir}

python bin/${sen}.py > ${sh_logdir}/${sen}-${stamp}.log 2>&1 < /dev/null &
echo started $sen
