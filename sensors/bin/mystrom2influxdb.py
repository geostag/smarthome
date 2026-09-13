from lib.config import settings
import requests, json, time, traceback
from lib.toinflux import Iflx

DEBUG = False

devices = []
for s in settings.mystrom.devices:
    devices.append({
        "HOST": s.host,
        "TOKEN": s.token,
        "room": s.room,
        "electric": s.electric,
        "DEVICELABEL": s.devicelabel
    })
    
INFLUX = Iflx()

def measure(host, token, room, electric, label):
    url = f"{host}report"
    header = { "Token": token }
    try:
        r = requests.get(url, headers=header)

    except:
        print(f"Failed to query myStrom '{url}'")
        return False
    
    if r.status_code == 200:
        d = json.loads(r.text)
        if DEBUG:
            print(d)
        
        for k,v in d.items():
            if k == "power":
                domain = "electricity"
                v = v * 1.0
            elif k == "Ws":
                domain = "electricity"
                v = v * 1.0
            elif k == "temperature":
                domain = "temperature"
                v = v * 1.0
            elif k == "energy_since_boot":
                domain = "electricity"
                v = v *1.0
            else:
                domain = "generic"

            if domain == "electricity":
                INFLUX.write("mystrom",k,v, {"device": label, "room": room, "domain": domain, "electric": electric } )
            else:
                INFLUX.write("mystrom",k,v, {"device": label, "room": room, "domain": domain } )
                
            if DEBUG:
                print(f"{k} > {v} / {domain} / {electric}")
            
    return True

while True:
    for dev in devices:
        try:
            measure(dev["HOST"],dev["TOKEN"],dev["room"],dev["electric"],dev["DEVICELABEL"])
            
        except:
            print(traceback.format_exc())
            print("measure and write failed")
            pass
            
    time.sleep(settings.query_interval)