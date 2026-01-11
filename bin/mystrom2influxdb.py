from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import requests, json, time, os

DEBUG = False

INFLUX_URL   = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG   = os.getenv("INFLUX_ORG")

INTERVAL = int(os.getenv("QUERY_INTERVAL"))

SWITCHLIST = os.getenv("MYSTROM_SWITCHLIST")
devices = []
for s in SWITCHLIST.split():
    i = {}
    for k in ["HOST","TOKEN","measurement","room","electric"]:
        i[k] = os.getenv(f"MYSTROM_{s}_{k}")
        
    devices.append(i)

def measure(host, token, name, room, electric):
    url = f"{host}report"
    header = { "Token": token }
    r = requests.get(url, headers=header)
    
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
                point = ( Point(name).tag("room",room).tag("domain",domain).tag("electric",electric).field(k,v) )
            else:
                point = ( Point(name).tag("room",room).tag("domain",domain).field(k,v) )
                
            write_api.write(bucket="smarthome", record=point)
            if DEBUG:
                print(f"{k} > {v} / {domain} / {electric}")
            
        client.close()
    

while True:
    for dev in devices:
        try:
            measure(dev["HOST"],dev["TOKEN"],dev["measurement"],dev["room"],dev["electric"])
            
        except:
            print("measure and write failed")
            pass
            
    time.sleep(INTERVAL)