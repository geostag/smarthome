from lib.config import settings
from lib.toinflux import Iflx
import requests, json, time, traceback

DEBUG = False

INTERVAL = settings.query_interval
if "interval" in settings.smartthings:
    INTERVAL = settings.smartthings.interval

INFLUX = Iflx()

def geturl(deviceid):
    return f'https://api.smartthings.com/v1/devices/{deviceid}/status'

def measure(device):
    url = geturl(device.id)
    r = requests.get(url, headers = {"Authorization": f"Bearer {settings.smartthings.token}"})
    
    if r.status_code == 200:
        d = json.loads(r.text)
        if DEBUG:
            print(d)

        cd = d["components"]["main"]

        if "temperatureMeasurement" in cd:
            t = cd["temperatureMeasurement"]["temperature"]["value"]
            INFLUX.write("smarthings","temperature",t,{"room": device.label, "domain": "temperature"})
        
        if "relativeHumidityMeasurement" in cd:
            h = cd["relativeHumidityMeasurement"]["humidity"]["value"]
            INFLUX.write("smarthings","humidity",h,{"room": device.label, "domain": "humidity"})

        if "powerMeter" in cd:
            p = cd["powerMeter"]["power"]["value"] * 1.0
            INFLUX.write("smarthings","power",p, {"electric": "switch", "room": device.label, "domain": "electricity" } )
            
        if "energyMeter" in cd:
            p = cd["energyMeter"]["energy"]["value"] * 1.0
            INFLUX.write("smarthings","energy",p, {"electric": "switch", "room": device.label, "domain": "electricity" } )
            
        if "switch" in cd:
            state = 1 if cd["switch"]["switch"]["value"] == "on" else 0
            INFLUX.write("smarthings","state",state, {"electric": "switch", "room": device.label, "domain": "electricity" } )
            
while True:
    for d in settings.smartthings.devices:
        try:
            measure(d)
            time.sleep(2)
            
        except:
            print(traceback.format_exc())
            print(f"measure and write failed: {d.id}")
            time.sleep(60)
        
    time.sleep(INTERVAL)    