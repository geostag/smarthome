import paho.mqtt.client as mqtt
import os, json, time

DEBUG = False

MQTT_BROKER   = os.getenv("MQTT_BROKER","")
MQTT_PORT     = int(os.getenv("MQTT_PORT","1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME","")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD","")

class WhiteBoard:
    def __init__(self):
        def onMessage(client,userdata,msg):
            payload = msg.payload.decode()
            topic   = msg.topic
            try:
                d = json.loads(payload)
                
            except:
                print(f"Whiteboard: could not decode '{payload}'")
                d = {}
                
            if "tele/tasmota" in topic:
                # this is tasmota message
                d = d.get("ENERGY")
                k = "tasmota"
                
            elif "tele/sunforecast" in topic:
                k = "sunforecast"

            elif "tele/zendure" in topic:
                k = "zendure"

            else:
                k = "lost+found"
                
            self.db[k] = d
            if k in self.listener:
                self.listener[k](d)
                
        self.db = {}
        self.mqtt = None
        self.mqttMasterListener = onMessage
        self.listener = {}
        self.mqttSubscribe()

    def mqttSubscribe(self):
        self.mqtt = MqttConn(topic = "tele/+/SENSOR",on_message=self.mqttMasterListener)
        if not self.healthy:
            print("MQTT subscription failed!")

    def addDeviceListener(self,device,callback):
        self.listener[device] = callback
        
    def dataGet(self,device,key):
        if not self.healthy:
            self.mqttSubscribe()

        return self.db.get(device,{}).get(key,0)

    @property
    def healthy(self):
        return self.mqtt.healthy
        
class MqttConn:
    def __init__(self, **kwargs):
        self.topic    = kwargs.get("topic",'#')
        def onMessage(client, userdata, msg):
            payload = msg.payload.decode()
            if DEBUG:
                print(payload)   
                
        def onConnect(client, userdata, flags, reason_code, properties):
            if reason_code == 0:
                if DEBUG:
                    print("✅ connection successful")
                client.subscribe(self.topic)
            else:
                print(f"❌ connection failed: {reason_code}")    

        self.user      = MQTT_USERNAME
        self.password  = MQTT_PASSWORD
        self.broker    = MQTT_BROKER
        self.port      = MQTT_PORT
        self.onMessage = kwargs.get("on_message",onMessage)
        self.onConnect = onConnect
        self.client    = None
        self.openClient()
        
    def openClient(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.username_pw_set(self.user,self.password)
        self.client.on_connect = self.onConnect
        self.client.on_message = self.onMessage
        try:
            self.client.connect(self.broker,self.port,60)
        except:
            print("MQTT connect failed")
            self.client = None
            time.sleep(60)
            
        self.client.loop_start()

    @property
    def healthy(self):
        if not self.client:
            self.openClient()

        return self.client != None
        
    def reset(self):
        try:
            self.client.disconnect()
            
        except:
            pass
        
        self.client = None
        
    def publish(self,topic,value):
        if not self.client:
            self.openClient()
            
        self.client.publish(
            topic   = topic,
            payload = value,
            qos     = 1,
            retain  = False
        )
    
    
#{
#    "Time": "2026-02-02T22:17:13",
#    "ENERGY": {
#        "Total": 8732.6868,
#        "Power": 246,
#        "Voltage": 235.1,
#        "Current": 1.42,
#        "phase_angle_L1": 311.0,
#        "Freq": 49.9,
#        "ID": "0a01454652220271ec73"
#    }
#}
#{
#    "solarPower1": 0,
#    "solarPower2": 0,
#    "solarPower3": 0,
#    "solarPower4": 0,
#    "electricLevel": 10,
#    "gridInputPower": 0,
#    "solarInputPower": 0,
#    "outputLimit": 0,
#    "gridOffPower": 0,
#    "BatVolt": 4770,
#    "packInputPower": 0,
#    "outputPackPower": 0,
#    "packState": 0,
#    "remainOutTime": 59940,
#    "hyperTmpD": 24.0,
#    "power": 0
#}
