from lib.config import settings
from lib.toinflux import Iflx
import requests, json, time

DEBUG = False

URL = f"{settings.remoteweather.url}&appid={settings.remoteweather.appid}"
INFLUX = Iflx()

def measure():
    r = requests.get(URL)
    
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
        
        v = 1.0 * d["wind"]["speed"]
        INFLUX.write("remoteweather", "windspeed", v, { "room": "outside", "domain": "weather" })

    else:
        print("could not connect remotewaether url")
        
while True:
    try:
        measure()
            
    except:
        print("measure and write failed")
        time.sleep(240)
        
    time.sleep(settings.remoteweather.interval)
    