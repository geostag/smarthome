#!/bin/bash

TDIR=$HOME/smarthome/schatzkiste

# ge raw data
df /var/nc-data/. > $TDIR/stats/log-`date +%Y%m%d`

../bin/run-cmd.sh schatzkiste-latest2influxdb.py
