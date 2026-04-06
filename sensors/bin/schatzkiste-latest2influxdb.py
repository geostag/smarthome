from os import listdir
from os.path import isfile, join
from datetime import datetime
from zoneinfo import ZoneInfo
from lib.toinflux import Iflx
import re, os, time

# this relies on files log-YYYMMDD in SCHATZKISTE_LOGDIR of the form:
#
# Filesystem                              1K-blocks       Used  Available Use% Mounted on
# schatzkiste:/volume1/pi-export/nc-data 3746108800 2349104768 1397004032  63% /var/nc-data
#
# created by a daily script:
# #!/bin/bash
# 
# TDIR=$HOME/smarthome/data/sensors/schatzkiste
# 
# df /var/nc-data/. > $TDIR/stats/log-`date +%Y%m%d`

TOKEN = os.getenv("INFLUX_LONGRANGE_TOKEN")
srcdir = os.getenv("SCHATZKISTE_LOGDIR")

def logSK():
    files = [f for f in listdir(srcdir) if isfile(join(srcdir, f))]

    fn = sorted(files)[-1]

    INFLUX = Iflx(bucket="longrange",token=TOKEN )

    m = re.match(r'^log-(\d{4})(\d{2})(\d{2})$',fn)
    if m:
        d = "%04d-%02d-%02d" % (int(m.group(1)),int(m.group(2)),int(m.group(3)))
        with open(join(srcdir,fn),"r") as f:
            for line in f.readlines():
                m = re.match(r'^schatzkiste.*\s(\d+)\s+(\d+)\s+([,.0-9]+)\%\s', line)
                if m:
                    used = m.group(1)
                    percent = m.group(3)
                    dt = datetime.strptime(d,"%Y-%m-%d")
                    dt = dt.replace(tzinfo=ZoneInfo("Europe/Berlin"))
                    INFLUX.write("schatzkiste","used",int(used),{"domain": "storage"},dt)

while True:
    if not os.path.isdir(srcdir):
        print(f"stats directory for schatzkiste das not exist. Waiting one day.")
    else:
        logSK()

    time.sleep(86400)
    