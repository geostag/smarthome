import requests, json, time, os
from lib.toinflux import Iflx

DEBUG = False

INTERVAL = int(os.getenv("QUERY_INTERVAL"))
SWITCHLIST = os.getenv("MYSTROM_SWITCHLIST")
devices = []
for s in SWITCHLIST.split():
    i = {}
    for k in ["HOST","TOKEN","room","electric","DEVICELABEL"]:
        i[k] = os.getenv(f"MYSTROM_{s}_{k}")
        
    devices.append(i)
    
INFLUX = Iflx()

def measure(host, token, room, electric, label):
    url = f"{host}report"
    header = { "Token": token }
    r = requests.get(url, headers=header)
    
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
            

while True:
    for dev in devices:
        try:
            measure(dev["HOST"],dev["TOKEN"],dev["room"],dev["electric"],dev["DEVICELABEL"])
            
        except:
            print("measure and write failed")
            pass
            
    time.sleep(INTERVAL)