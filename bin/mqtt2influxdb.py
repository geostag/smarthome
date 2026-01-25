from lib.toinflux import Iflx
import paho.mqtt.client as mqtt
import dateutil.parser, datetime, json, re, time, os, requests

DEBUG = False

BROKER   = os.getenv("MQTT_BROKER")
PORT     = int(os.getenv("MQTT_PORT"))
TOPIC    = os.getenv("MQTT_TOPIC")
USERNAME = os.getenv("MQTT_USERNAME")
PASSWORD = os.getenv("MQTT_PASSWORD")

INFLUX = Iflx()

def datetime_parser(dct):
    for k, v in dct.items():
        if isinstance(v, str) and re.search("^2\d{3}-\d{2}-\d{2}[A-Z]", v):
            try:
                dct[k] = dateutil.parser.isoparse(v)
            except:
                if DEBUG:
                    print("parsing date did not work '%s'" % v)
                    
                pass
            
        elif isinstance(v, str) and re.search("^2\d{3}-\d{2}-\d{2} ", v):
            try:
                dct[k] = datetime.datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
            except:
                if DEBUG:
                    print("parsing date did not work '%s'" % v)
                    
                pass
            
    return dct


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        if DEBUG:
            print("✅ Erfolgreich verbunden")
        client.subscribe(TOPIC)
    else:
        print(f"❌ Verbindung fehlgeschlagen: {reason_code}")

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    if DEBUG:
        print(f"{msg.topic}: {payload}")
        
    d = json.loads(payload,object_hook=datetime_parser)
    p = 0
    
    if DEBUG:
        print(d)
    
    try:
        for k,v in d["ENERGY"].items():
            INFLUX.write("tasmota",k,v,{"room": "keller", "domain": "electricity", "electric": "swm" })
            
        p = d["ENERGY"]["Power"]
        if p < 0:
            INFLUX.write("tasmota","upstream",  p,{"room": "keller", "domain": "electricity", "electric": "swm" })
            INFLUX.write("tasmota","downstream",0,{"room": "keller", "domain": "electricity", "electric": "swm" })
            
        else:
            INFLUX.write("tasmota","upstream",  0,{"room": "keller", "domain": "electricity", "electric": "swm" })
            INFLUX.write("tasmota","downstream",p,{"room": "keller", "domain": "electricity", "electric": "swm" })
            
    except:
        print("write to influxdb failed")
        

# setup MQTT Client 
client = mqtt.Client( mqtt.CallbackAPIVersion.VERSION2 )
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, keepalive=60)
client.loop_forever()
