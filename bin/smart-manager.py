import paho.mqtt.client as mqtt
import dateutil.parser, datetime, json, re, time, os, requests

DEBUG = False

BROKER   = os.getenv("MQTT_BROKER")
PORT     = int(os.getenv("MQTT_PORT"))
#TOPIC    = os.getenv("MQTT_TOPIC")
TOPIC    = "#"
USERNAME = os.getenv("MQTT_USERNAME")
PASSWORD = os.getenv("MQTT_PASSWORD")
ZENDURE_HOST = os.getenv("ZENDURE_HOST")
ZENDURE_SN   = os.getenv("ZENDURE_SN")

TASMOTA_TAG = os.getenv("TASMOTA_TAG")

UPDATE_ZENDURE_INTERVAL = 59
INJECTION_MAX = 400
BATT_MIN = 10
BATT_MAX = 95
BASELOAD = 95

# lookback items (tasmota sends every minute, thus 5 minutes)
LOOKBACK_ITEMS = 15


class Tasmota:
    def __init__(self,tag,db):
        self.mqtt_topic = f"tele/{tag}/SENSOR"
        self.db = db
        
    def get_db_value(self,key):
        data = self.db.get(self.mqtt_topic,{})
        energy = data.get("ENERGY",{})
        return energy.get(key,0)
        
    @property
    def Power(self):
        return self.get_db_value("Power")

class Zendure:
    def __init__(self,host,sn,db):
        self.host = host
        self.sn = sn
        self.injection = 0
        self.lastupdate = False
        self.url = f"{host}/properties/write"
        self.mqtt_topic = f"zendure/datacopy/{sn}"
        self.db = db
        self.injection = 0
        
    def get_db_value(self,key):
        data = self.db.get(self.mqtt_topic,{})
        return data.get(key,0)
        
    @property
    def solarInputPower(self):
        return self.get_db_value("solarInputPower")
        
    @property
    def electricLevel(self):
        return self.get_db_value("electricLevel")
        
    @property
    def outputLimit(self):
        return self.get_db_value("outputLimit")
        #return self.injection
        
    @outputLimit.setter
    def outputLimit(self,value):
        #print(f"pushing to zendure: {value}")
        #return True
        
        if not self.lastupdate or self.lastupdate < datetime.datetime.now() - datetime.timedelta(seconds=UPDATE_ZENDURE_INTERVAL):
            data = { 
                "sn": self.sn,
                "properties": { "outputLimit": int(value) }
            }
            r = requests.post(self.url, json=data)
            if r.status_code != 200:
                print(f"ERROR setting outputlimit: {r.status_code}")
                return False
                
            else:
                self.injection = value
                self.lastupdate = datetime.datetime.now()
                print("DONE" + str(self.lastupdate))
                return True
        
        else:
            print(f"last update less than {UPDATE_ZENDURE_INTERVAL}s ago - doing nothing")
        
class ZendureManager:
    def __init__(self,zen,tasmota):
        self.zen = zen
        self.tasmota = tasmota
        self.swmpower = []
        self.solarInputPower = []
        
    def controller_update(self):
        b = self.zen.electricLevel
        
        p = self.tasmota.Power
        self.swmpower.append(p)
        self.swmpower = self.swmpower[(-1 * LOOKBACK_ITEMS):]
        #p = int( 10 * sum(self.swmpower) / len(self.swmpower) + 0.5) / 10
        
        s = self.zen.solarInputPower
        self.solarInputPower.append(s)
        self.solarInputPower = self.solarInputPower[(-1 * LOOKBACK_ITEMS):]
        s = int( 10 * sum(self.solarInputPower) / len(self.solarInputPower) + 0.5) / 10
        
        i = self.zen.outputLimit
        i_old = int(i)
        
        hour = datetime.datetime.now().hour
        mode = ""
        
        # values ready, lets do logic
        if b <= BATT_MIN:
            # first load battery
            mode = "super low batt"
            i = 0
            
        elif b >= BATT_MAX:
            # discharge
            mode = "super hi batt"
            i = INJECTION_MAX
            
        elif s > p + i:
            # more sun than needed
            mode = "hi sun"
            i = p + i
            
        elif b > 1.2 * BATT_MIN and s > 9 and s < p+i:
            # enough power there, baseload (discharge mode, while sun still there)
            mode = "low sun, use battery on top"
            i = min(2*BASELOAD,i+p)
            
        elif s > 9 and s < p+i:
            # sun there and completely needed, do not discharge
            mode = f"low sun {p},{s},{i}"
            i = s
            
        else:
            # maximum baseload discharge
            mode = "baseload"
            i = min(BASELOAD,i+p)
            
        i = int(min(INJECTION_MAX,i) + 0.5) * 1.0
        
        if ( i > 10 and abs(i-i_old) < 2 ) or (i > 100 and abs(i-i_old)/i < 0.03) :
            # peanuts
            mode += f", peanuts {i} {i_old}"
            i = i_old
        
        if i != i_old:
            if i > i_old:
                # increase slowly; reduction untouched
                mode += ", slow-raise"
                i = 0.8*(i_old + i)
                
            self.zen.outputLimit = i
            print(f"p: {p}, s: {s}, b: {b} do i {i_old} -> {i} ({mode})")
            
        else:
            print(f"p: {p}, s: {s}, b: {b}, i: {i} ({mode})")
            n = False
            


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
        
    try:
        d = json.loads(payload)
        DB[msg.topic] = d
        
    except:
        d = payload
    
    if DEBUG:
        print("------------")
        print(d)
        print("------------")
    
    
    ZM.controller_update()

# ----------------------------- main -------------------------------
DB = {}

# Zendure management
ZM  = ZendureManager( Zendure(ZENDURE_HOST, ZENDURE_SN, DB), Tasmota(TASMOTA_TAG, DB) )

# setup MQTT client
client = mqtt.Client( mqtt.CallbackAPIVersion.VERSION2 )
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, keepalive=60)

# start loop
client.loop_forever()


# tele/tasmota_828769/STATE {"Time":"2026-01-23T20:22:02","Uptime":"211T14:53:51","UptimeSec":18284031,"Heap":18,"SleepMode":"Dynamic","Sleep":50,"LoadAvg":19,"MqttCount":2379,"POWER":"ON","Wifi":{"AP":1,"SSId":"EagleView","BSSId":"38:10:D5:A4:69:51","Channel":6,"Mode":"11n","RSSI":78,"Signal":-61,"LinkCount":1475,"Downtime":"0T22:51:11"}}
# tele/tasmota_828769/SENSOR {"Time":"2026-01-23T20:22:02","ENERGY":{"Total":8650.0075,"Power":63,"Voltage":238.2,"Current":0.95,"phase_angle_L1":284.0,"Freq":50.0,"ID":"0a01454652220271ec73"}}
# zendure/datacopy/CO4EHNCDN247220 {"solarPower1": 0, "solarPower2": 0, "solarPower3": 0, "solarPower4": 0, "electricLevel": 13, "gridInputPower": 0, "solarInputPower": 0, "outputLimit": 95, "gridOffPower": 0, "BatVolt": 4745, "packInputPower": 95, "outputPackPower": 0, "packState": 2, "remainOutTime": 143, "power": 104}
