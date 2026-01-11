from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
from zoneinfo import ZoneInfo
import os

DEBUG = False

INFLUX_URL   = os.getenv("INFLUX_URL")
INFLUX_TOKEN = '--replace-token--
INFLUX_ORG   = os.getenv("INFLUX_ORG")


data = [
    {
        "d": 1,
        "values": {
            "green_injected": 888.0,
            "green_upstream": 0.0,
            "green_used": 888.0,
            "swm_used": 8800.0
        }
    },
    {
        "d": 2,
        "values": {
            "green_injected": 124.0,
            "green_upstream": 0.0,
            "green_used": 124.0,
            "swm_used": 7440.0
        }
    },
    {
        "d": 3,
        "values": {
            "green_injected": 638.0,
            "green_upstream": 0.0,
            "green_used": 638.0,
            "swm_used": 9970.0
        }
    },
    {
        "d": 4,
        "values": {
            "green_injected": 976.0,
            "green_upstream": -0.7,
            "green_used": 975.3,
            "swm_used": 10900.0
        }
    },
    {
        "d": 5,
        "values": {
            "green_injected": 213.41946877630699,
            "green_upstream": 0.0,
            "green_used": 213.41946877630699,
            "swm_used": 19211.00000000115
        }
    },
    {
        "d": 6,
        "values": {
            "green_injected": 875.9691954617684,
            "green_upstream": -5.133971321330139,
            "green_used": 881.1031667830986,
            "swm_used": 10297.300000000178
        }
    }
]
    
    

        
client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)
write_api = client.write_api(write_options=SYNCHRONOUS)

for r in data:
    dt = datetime(2026,1,r["d"],12,0,0)
    dt = dt.replace(tzinfo=ZoneInfo("Europe/Berlin"))
    
    r["values"]["green_used"] = r["values"]["green_injected"] + r["values"]["green_upstream"]

    for k in r["values"]:
        v = r["values"][k]

        point = Point("daily_energy").field(k,v).time(dt,WritePrecision.NS)
        print(dt,point)
        write_api.write(bucket="smarthomederived", record=point )
        
client.close()

