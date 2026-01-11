##datatype measurement,tag,double,dateTime:RFC3339
##default,,,
#strom,haus,123.4,2024-01-01T12:00:00+01:00

from os import listdir
from os.path import isfile, join
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from zoneinfo import ZoneInfo
import re,json,os

INFLUX_URL   = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN_LONGRANGE")
INFLUX_ORG   = os.getenv("INFLUX_ORG")

srcdir = os.getenv("SCHATZKISTE_LOGDIR")



files = [f for f in listdir(srcdir) if isfile(join(srcdir, f))]

fn = sorted(files)[-1]

m = re.match(r'^log-(\d{4})(\d{2})(\d{2})$',fn)
if m:
    client = InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG
    )
    write_api = client.write_api(write_options=SYNCHRONOUS)
    d = "%04d-%02d-%02d" % (int(m.group(1)),int(m.group(2)),int(m.group(3)))
    with open(join(srcdir,fn),"r") as f:
        for line in f.readlines():
            m = re.match(r'^schatzkiste.*\s(\d+)\s+(\d+)\s+([,.0-9]+)\%\s', line)
            if m:
                used = m.group(1)
                percent = m.group(3)
                dt = datetime.strptime(d,"%Y-%m-%d")
                dt = dt.replace(tzinfo=ZoneInfo("Europe/Berlin"))
                p = (Point("schatzkiste").tag("domain","storage").field("used",int(used)).time(dt,WritePrecision.NS))
                write_api.write(bucket="longrange", record=p)
