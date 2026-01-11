#!/bin/bash

_basedir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
_basedir=`dirname $_basedir`

cd ${_basedir} || exit 2
if [ ! -f env.sh ]; then
  echo "ERROR: create env.sh first"
  exit 2
fi

. env.sh

chmod u+x bin/*.sh
python -m venv "$sh_penvdir"
. env.sh
pip install -r requirements.txt

mkdir influxdb-data
mkdir grafana-data

echo "next steps:"
echo "start-servers.sh"
echo "start-sensors.sh"
