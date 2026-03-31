#!/bin/bash

_basedir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
_basedir=`dirname $_basedir`

cd ${_basedir} || exit 2
if [ ! -f .env ]; then
  echo "ERROR: create .env first"
  exit 2
fi

. "${_basedir}/bin/load-env.sh"

chmod u+x bin/*.sh
chmod u+x docker/scripts-entrypoint.sh
chmod u+x docker/influxdb/init/*.sh

if [ ! -d "$sh_penvdir" ]; then
  python -m venv "$sh_penvdir"
fi

. "${_basedir}/bin/load-env.sh"
if [ -f "$sh_penvdir/bin/activate" ]; then
  . "$sh_penvdir/bin/activate"
  pip install -r requirements.txt
fi

mkdir -p influxdb-data
mkdir -p grafana-data
mkdir -p logs
mkdir -p config
mkdir -p schatzkiste/stats

echo "next steps:"
echo "1. adjust .env"
echo "2. docker compose up -d --build"
