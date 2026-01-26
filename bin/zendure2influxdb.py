import paho.mqtt.client as mqtt
import requests, json, time, os
from lib.toinflux import Iflx

DEBUG = False

INTERVAL = int(os.getenv("QUERY_INTERVAL"))

HOST   = os.getenv("ZENDURE_HOST")
REPORT_PROPERTIES = os.getenv("ZENDURE_REPORT_PROPERTIES").split()
REPORT_PACK_PROPERTIES = os.getenv("ZENDURE_REPORT_PACK_PROPERTIES").split()

# we may send Zendure data-copies to MQTT broken
SEND_DATA_TO_MQTT_BROKER = (os.getenv("ZENDURE_SEND_DATA_TO_MQTT_BROKER","no") == "yes")
MQTT_BROKER   = os.getenv("MQTT_BROKER","")
MQTT_PORT     = int(os.getenv("MQTT_PORT","1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME","")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD","")

INFLUX = Iflx()

class MQTTconnection:
    def __init__(self,broker,port,user,password):
        self.user = user
        self.password = password
        self.broker = broker
        self.port = port
        self.client = None
        
    def openClient(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.username_pw_set(self.user,self.password)
        self.client.connect(self.broker,self.port,60)
        self.client.loop_start()
        
    def reset(self):
        try:
            self.client.disconnect()
            
        except:
            pass
        
        self.client = None
        
    def publish(self,sn,value):
        if not self.client:
            self.openClient()
            
        #print(f"publish: {value}")
        self.client.publish(
            topic   = f"tele/zendure_{sn}/SENSOR",
            payload = value,
            qos     = 1,
            retain  = False
        )
        

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
            v = d["properties"].get(k,0)
            INFLUX.write("zendure", k, v, { "room": "2Stock", "domain": "electricity", "electric": "solar" })
            if DEBUG:
                print(f"{k}: {v}")
                
            dcopy[k] = v
                
        for pack in d["packData"]:
            # loop over battery packs
            psn = pack["sn"]
            for k in REPORT_PACK_PROPERTIES:
                v = pack.get(k,0)
                INFLUX.write("zendure", k, v, { "room": "2Stock", "domain": "electricity", "pack": psn })
        
            dcopy[k] = v
            
        if mqttconnection:
            #print(dcopy)
            mqttconnection.publish(sn,json.dumps(dcopy))


if SEND_DATA_TO_MQTT_BROKER:
    M = MQTTconnection(MQTT_BROKER, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD)
    
else:
    M = None
    
while True:
    try:
        measure(HOST,M)
    except:
        print("measure and write failed")
        if M:
            M.reset()
            
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