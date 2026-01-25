##datatype measurement,tag,double,dateTime:RFC3339
##default,,,
#strom,haus,123.4,2024-01-01T12:00:00+01:00

from os import listdir
from os.path import isfile, join
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from lib.toinflux import Iflx
import re,json,os

TOKEN = os.getenv("INFLUX_TOKEN_LONGRANGE")
srcdir = os.getenv("SCHATZKISTE_LOGDIR")

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
