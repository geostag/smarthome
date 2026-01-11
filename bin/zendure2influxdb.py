from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import requests, json, time, os

DEBUG = False

INFLUX_URL   = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG   = os.getenv("INFLUX_ORG")
INFLUX_BUCKET= os.getenv("INFLUX_BUCKET")

INTERVAL = int(os.getenv("QUERY_INTERVAL"))

HOST   = os.getenv("ZENDURE_HOST")
REPORT_PROPERTIES = os.getenv("ZENDURE_REPORT_PROPERTIES").split()

def measure(host):
    url = f"{host}/properties/report"
    r = requests.get(url)
    
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
        
        for k in REPORT_PROPERTIES:
            v = d["properties"][k]
            write_api.write(bucket=INFLUX_BUCKET, record=Point("zendure").tag("room","2Stock").tag("domain","electricity").tag("electric","solar").field(k,v) )
            if DEBUG:
                print(f"{k}: {v}")
                
        for pack in d["packData"]:
            # loop over battery packs
            sn = pack["sn"]
            k = "socLevel"
            v = pack["socLevel"]
            write_api.write(bucket=INFLUX_BUCKET, record=Point("zendure").tag("room","2Stock").tag("domain","electricity").tag("pack",sn).field(k,v) )
        
        client.close()

while True:
    try:
        measure(HOST)
    except:
        print("measure and write failed")
        time.sleep(240)
        
    time.sleep(INTERVAL)
    
#    
#{
#   "timestamp":1767623689,
#   "messageId":42,
#   "sn":"EOA1NHN3N246446",
#   "version":2,
#   "product":"solarFlow800Pro",
#   "properties":{
#      "heatState":0,
#      "packInputPower":103,
#      "outputPackPower":0,
#      "outputHomePower":117,
#      "remainOutTime":125,
#      "packState":2,
#      "electricLevel":12,
#      "gridInputPower":0,
#      "solarInputPower":14,
#      "solarPower1":7,
#      "solarPower2":0,
#      "solarPower3":7,
#      "solarPower4":0,
#      "pass":0,
#      "reverseState":0,
#      "socStatus":1,
#      "hyperTmp":3001,
#      "gridOffPower":0,
#      "dcStatus":1,
#      "pvStatus":0,
#      "acStatus":1,
#      "dataReady":1,
#      "gridState":1,
#      "BatVolt":4645,
#      "socLimit":0,
#      "writeRsp":0,
#      "acMode":2,
#      "inputLimit":0,
#      "outputLimit":118,
#      "socSet":1000,
#      "minSoc":100,
#      "gridStandard":0,
#      "gridReverse":2,
#      "inverseMaxPower":800,
#      "lampSwitch":1,
#      "gridOffMode":2,
#      "IOTState":2,
#      "Fanmode":1,
#      "Fanspeed":0,
#      "bindstate":0,
#      "factoryModeState":0,
#      "OTAState":0,
#      "LCNState":0,
#      "oldMode":0,
#      "VoltWakeup":0,
#      "ts":1767622045,
#      "tsZone":13,
#      "smartMode":0,
#      "chargeMaxLimit":1000,
#      "packNum":1,
#      "rssi":-68,
#      "is_error":0
#   },
#   "packData":[
#      {
#         "sn":"CO4EHNCDN247220",
#         "packType":300,
#         "socLevel":12,
#         "state":2,
#         "power":106,
#         "maxTemp":2921,
#         "totalVol":4640,
#         "batcur":65513,
#         "maxVol":310,
#         "minVol":308,
#         "softVersion":4117
#      }
#   ]
#}