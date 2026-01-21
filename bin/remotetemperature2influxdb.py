from lib.toinflux import Iflx
import requests, json, time, os

DEBUG = False

REMOTEWEATHER_INTERVAL = int(os.getenv("REMOTEWEATHER_INTERVAL"))
REMOTEWEATHER_URL = os.getenv("REMOTEWEATHER_URL")

INFLUX = Iflx()

def measure():
    r = requests.get(REMOTEWEATHER_URL)
    
    if r.status_code == 200:
        d = json.loads(r.text)
        if DEBUG:
            print(d)

        v = d["main"]["temp"] - 273.15
        INFLUX.write("remoteweather", "temperature", v, { "room": "outside", "domain": "temperature" })
        
        v = d["main"]["humidity"]
        INFLUX.write("remoteweather", "humidity", v, { "room": "outside", "domain": "humidity" })
        
        v = d["main"]["pressure"]
        INFLUX.write("remoteweather", "pressure", v, { "room": "outside", "domain": "weather" })
        
        v = d["wind"]["speed"]
        INFLUX.write("remoteweather", "windspeed", v, { "room": "outside", "domain": "weather" })
        
while True:
    try:
        measure()
            
    except:
        print("measure and write failed")
        time.sleep(240)
        
    time.sleep(REMOTEWEATHER_INTERVAL)
    