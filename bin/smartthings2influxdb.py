from lib.toinflux import Iflx
import requests, json, time, os, traceback

DEBUG = False

INTERVAL = int(os.getenv("QUERY_INTERVAL"))
ST_TOKEN = os.getenv("SMARTTHINGS_TOKEN")
ST_DEVICES = []
for d in os.getenv("SMARTTHINGS_DEVUCELIST"):
    ST_DEVICES.append({
        "id": os.getenv(f"SMARTTHINGS_{d}_ID"),
        "label": os.getenv(f"SMARTTHINGS_{d}_LABEL")
    })
    
INFLUX = Iflx()

def geturl(deviceid):
    return f'https://api.smartthings.com/v1/devices/{deviceid}/status'

def measure(device):
    url = geturl(device["id"])
    r = requests.get(url, headers = {"Authorization": f"Bearer {ST_TOKEN}"})
    
    if r.status_code == 200:
        d = json.loads(r.text)
        if DEBUG:
            print(d)

        t = d["components"]["main"]["temperatureMeasurement"]["temperature"]["value"]
        INFLUX.write("smarthings","temperature",t,{"room": device["label"], "domain": "temperature"})
        
        if "relativeHumidityMeasurement" in d["components"]["main"]:
            h = d["components"]["main"]["relativeHumidityMeasurement"]["humidity"]["value"]
            INFLUX.write("smarthings","humidity",h,{"room": device["label"], "domain": "humidity"})
            
while True:
    for d in ST_DEVICES:
        try:
            measure(d)
            time.sleep(1)
            
        except:
            print(f"measure and write failed: {d[id]}")
            print(traceback.format_exc())
            time.sleep(60)
        
    time.sleep(INTERVAL)    