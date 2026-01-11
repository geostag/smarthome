from os import listdir
from os.path import isfile, join
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from zoneinfo import ZoneInfo
import re,json,os, time

INFLUX_URL   = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN_LONGRANGE")
INFLUX_ORG   = os.getenv("INFLUX_ORG")


srcfile = "/var/www/pi/b70it/data/nc-usage.json"

client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)
write_api = client.write_api(write_options=SYNCHRONOUS)

c = 0
with open(srcfile,"r") as f:
    d = f.read()
    d = json.loads(d)
    for u in d:
        for r in d[u]:
            x = r["x"]
            y = r["y"]
            dt = datetime.strptime(x,"%Y-%m-%d %H:%M:%S")
            dt = dt.replace(tzinfo=ZoneInfo("Europe/Berlin"))
            dt = dt.replace(hour=0,minute=0, second=0, microsecond=0)
            p = (Point("nextcloud").tag("domain","storage").tag("user",u).field("used",int(y)).time(dt,WritePrecision.NS))
            print(p)
            write_api.write(bucket="longrange", record=p)
            c = c + 1
            if c % 20 == 0:
                print("lssep")
                time.sleep(1)

    