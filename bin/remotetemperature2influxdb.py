from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import requests, json, time, os

DEBUG = False

INFLUX_URL   = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG   = os.getenv("INFLUX_ORG")

REMOTEWEATHER_INTERVAL = int(os.getenv("REMOTEWEATHER_INTERVAL"))

REMOTEWEATHER_URL = os.getenv("REMOTEWEATHER_URL")

def measure():
    r = requests.get(REMOTEWEATHER_URL)
    
    if r.status_code == 200:
        d = json.loads(r.text)
        if DEBUG:
            print(d)

        client = InfluxDBClient(
            url=INFLUX_URL,
            token=INFLUX_TOKEN,
            org=INFLUX_ORG
        )
        write_api = client.write_api(write_options=SYNCHRONOUS)

        v = d["main"]["temp"] - 273.15
        write_api.write(bucket="smarthome", record=Point("remoteweather").tag("room","outside").tag("domain","temperature").field("temperature",v))
        v = d["main"]["humidity"]
        write_api.write(bucket="smarthome", record=Point("remoteweather").tag("room","outside").tag("domain","humidity").field("humidity",v))
        v = d["main"]["pressure"]
        write_api.write(bucket="smarthome", record=Point("remoteweather").tag("room","outside").tag("domain","weather").field("pressure",v))
        v = d["wind"]["speed"]
        write_api.write(bucket="smarthome", record=Point("remoteweather").tag("room","outside").tag("domain","weather").field("windspeed",v))
        
        client.close()

while True:
    try:
        measure()
            
    except:
        print("measure and write failed")
        time.sleep(240)
        
    time.sleep(REMOTEWEATHER_INTERVAL)
    