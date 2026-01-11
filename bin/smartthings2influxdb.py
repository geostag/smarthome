from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import requests, json, time, os

DEBUG = False

INFLUX_URL    = os.getenv("INFLUX_URL")
INFLUX_TOKEN  = os.getenv("INFLUX_TOKEN")
INFLUX_ORG    = os.getenv("INFLUX_ORG")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET")

INTERVAL = int(os.getenv("QUERY_INTERVAL"))

ST_TOKEN = os.getenv("SMARTTHINGS_TOKEN")
ST_DEVICES = []
for d in os.getenv("SMARTTHINGS_DEVUCELIST"):
    ST_DEVICES.append({
        "id": os.getenv(f"SMARTTHINGS_{d}_ID"),
        "label": os.getenv(f"SMARTTHINGS_{d}_LABEL")
    })
    

def geturl(deviceid):
    return f'https://api.smartthings.com/v1/devices/{deviceid}/status'

def measure(device):
    url = geturl(device["id"])
    r = requests.get(url, headers = {"Authorization": f"Bearer {ST_TOKEN}"})
    
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

        t = d["components"]["main"]["temperatureMeasurement"]["temperature"]["value"]
        write_api.write(bucket="smarthome", record=Point("smarthings").tag("room",device["label"]).tag("domain","temperature").field("temperature",t) )
        
        if "relativeHumidityMeasurement" in d["components"]["main"]:
            h = d["components"]["main"]["relativeHumidityMeasurement"]["humidity"]["value"]
            write_api.write(bucket=INFLUX_BUCKET, record=Point("smarthings").tag("room",device["label"]).tag("domain","humidity").field("humidity",h) )
            
        
        client.close()

while True:
    try:
        for d in ST_DEVICES:
            measure(d)
            
    except:
        print("measure and write failed")
        time.sleep(240)
        
    time.sleep(INTERVAL)    