from lib.toinflux import Iflx
import requests, json, time, os, traceback

DEBUG = False

INTERVAL = int(os.getenv("QUERY_INTERVAL"))
INTERVAL = int(os.getenv("SMARTTHINGS_QUERY_INTERVAL",INTERVAL))
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

        cd = d["components"]["main"]

        if "temperatureMeasurement" in cd:
            t = cd["temperatureMeasurement"]["temperature"]["value"]
            INFLUX.write("smarthings","temperature",t,{"room": device["label"], "domain": "temperature"})
        
        if "relativeHumidityMeasurement" in cd:
            h = cd["relativeHumidityMeasurement"]["humidity"]["value"]
            INFLUX.write("smarthings","humidity",h,{"room": device["label"], "domain": "humidity"})

        if "powerMeter" in cd:
            p = cd["powerMeter"]["power"]["value"] * 1.0
            INFLUX.write("smarthings","power",p, {"electric": "switch", "room": device["label"], "domain": "electricity" } )
            
        if "energyMeter" in cd:
            p = cd["energyMeter"]["energy"]["value"] * 1.0
            INFLUX.write("smarthings","energy",p, {"electric": "switch", "room": device["label"], "domain": "electricity" } )
            
        if "switch" in cd:
            state = 1 if cd["switch"]["switch"]["value"] == "on" else 0
            INFLUX.write("smarthings","state",state, {"electric": "switch", "room": device["label"], "domain": "electricity" } )
            
while True:
    for d in ST_DEVICES:
        try:
            measure(d)
            time.sleep(2)
            
        except:
            print(traceback.format_exc())
            i = d.get("id","-")
            print(f"measure and write failed: {i}")
            time.sleep(60)
        
    time.sleep(INTERVAL)    