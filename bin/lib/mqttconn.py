import paho.mqtt.client as mqtt
import os

DEBUG = True

MQTT_BROKER   = os.getenv("MQTT_BROKER","")
MQTT_PORT     = int(os.getenv("MQTT_PORT","1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME","")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD","")

        
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
        self.client.connect(self.broker,self.port,60)
        self.client.loop_start()
        
    def reset(self):
        try:
            self.client.disconnect()
            
        except:
            pass
        
        self.client = None
        
    def publish(self,topic,sn,value):
        if not self.client:
            self.openClient()
            
        self.client.publish(
            topic   = topic,
            payload = value,
            qos     = 1,
            retain  = False
        )
    