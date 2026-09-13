from lib.config import settings
from lib.mqttconn import MqttConn
import requests, json, time
from lib.toinflux import Iflx

DEBUG = False

REPORT_PROPERTIES = settings.zendure.report_properties.split()
REPORT_PACK_PROPERTIES = settings.zendure.report_pack_properties.split()

INFLUX = Iflx()

def measure(host,mqttconnection):
    url = f"{host}/properties/report"
    r = requests.get(url)
    
    if r.status_code == 200:
        d = json.loads(r.text)
        if DEBUG:
            print(d)
        
        dcopy = {}
        sn = d.get("sn","serialnumber")
        
        for k in REPORT_PROPERTIES:
            tags = { "room": "2Stock", "domain": "electricity", "electric": "solar" }
            v = d["properties"].get(k,0)
            
            # value interception
            if k == "hyperTmp":
                k = "hyperTmpD"
                v = ( v - 2731 ) / 10.0
                del tags["electric"]
                tags["domain"] = "temperatureDevice"
                
            INFLUX.write("zendure", k, v, tags)
            if DEBUG:
                print(f"{k}: {v}")
                
            dcopy[k] = v
                
        dpack = {}
        npack = 0
        for pack in d["packData"]:
            # loop over battery packs
            psn = pack["sn"]
            npack += 1
            for k in REPORT_PACK_PROPERTIES:
                v = pack.get(k,0)
                if k == "maxTemp":
                    v = ( v - 2731 ) / 10.0
                    
                if DEBUG:
                    print(f"single pack data: {k} - {v}")

                INFLUX.write("zendure", k, v, { "room": "2Stock", "domain": "electricity", "pack": psn })
                if not k in dpack:
                    dpack[k] = 0

                dpack[k] += v

        for k in dpack:
            dcopy[k] = dpack[k] / npack 
            if DEBUG:
                print(f"total  pack data: {k} - {dcopy[k]} (npack: {npack})")
            
        if mqttconnection:
            #print(dcopy)
            topic = f"tele/zendure_{sn}/SENSOR"
            mqttconnection.publish(topic,json.dumps(dcopy))


if "send_data_to_mqtt_broker" in settings.zendure and settings.zendure.send_data_to_mqtt_broker == "yes":
    M = MqttConn()
    
else:
    M = None
    
while True:
    try:
        measure(settings.zendure.host,M)
    except:
        print("measure and write failed")
        if M:
            M.reset()
            
        time.sleep(240)
        
    time.sleep(settings.query_interval)
