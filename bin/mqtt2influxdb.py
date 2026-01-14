from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import paho.mqtt.client as mqtt
import dateutil.parser, datetime, json, re, time, os, requests

DEBUG = False

INFLUX_URL   = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG   = os.getenv("INFLUX_ORG")

BROKER   = os.getenv("MQTT_BROKER")
PORT     = int(os.getenv("MQTT_PORT"))
TOPIC    = os.getenv("MQTT_TOPIC")
USERNAME = os.getenv("MQTT_USERNAME")
PASSWORD = os.getenv("MQTT_PASSWORD")

ZENDURE_HOST   = os.getenv("ZENDURE_HOST")
ZENDURE_SN     = os.getenv("ZENDURE_SN")

QUERY_ZENDURE_INTERVAL = 97
INJECTION_MAX = 850
BATT_MIN = 10
BATT_MAX = 95

# hysterese swm lookback items (tasmota sends every minute, thus 5 minutes)
LOOKBACK_ITEMS = 4

class Zendure:
    def __init__(self,host,sn):
        self.host = host
        self.sn = sn
        self.properties = {}
        self.lastqueried = False
        
    def query(self):
        # rate limitation
        if not self.lastqueried or self.lastqueried < datetime.datetime.now() - datetime.timedelta(seconds=QUERY_ZENDURE_INTERVAL):
            url = f"{self.host}/properties/report"
            try:
                r = requests.get(url)
                
            except:
                self.properties = {}
                return
                
            if r.status_code == 200:
                d = json.loads(r.text)
                try:
                    self.properties = d["properties"]
                    self.lastqueried = datetime.datetime.now()
                    
                except:
                    # save fallback
                    self.properties = {}
                    
    @property
    def batteryLevel(self):
        self.query()
        return self.properties.get("electricLevel",0)
        
    @property
    def solarInputPower(self):
        self.query()
        return self.properties.get("solarInputPower",0)
    
    @property
    def greenInjection(self):
        self.query()
        return self.properties.get("outputLimit",0)
        
    @greenInjection.setter
    def greenInjection(self,value):
        url = f"{self.host}/properties/write"
        data = { 
            "sn": self.sn,
            "properties": { "outputLimit": int(value) }
        }
        r = requests.post(url, json=data)
        if r.status_code != 200:
            print(f"ERROR setting outputlimit: {r.status_code}")
            return False
            
        else:
            self.lastqueried = False
            return True
        
class ZendureManager:
    def __init__(self,zen):
        self.zen = zen
        self.swmpower = []
        self.solarInputPower = []
        
    def update(self,p):
        self.swmpower.append(p)
        self.swmpower = self.swmpower[(-1 * LOOKBACK_ITEMS):]
        self.solarInputPower.append(self.zen.solarInputPower)
        self.solarInputPower = self.solarInputPower[(-1 * LOOKBACK_ITEMS):]
        p = int( 10 * sum(self.swmpower) / len(self.swmpower) + 0.5) / 10
        s = int( 10 * sum(self.solarInputPower) / len(self.solarInputPower) + 0.5) / 10
        b = self.zen.batteryLevel
        i = self.zen.greenInjection
        i_old = int(i)
        
        # values ready, lets do logic
        if b <= BATT_MIN:
            # first load battery
            i = 0
            
        elif b >= BATT_MAX:
            # discharge
            i = INJECTION_MAX
            
        elif s > p:
            # inject only needed power
            i = p
            
        else:
            # use battery
            ontop_needed = p - s
            ratio = (b  - BATT_MIN) / (BATT_MAX - BATT_MIN)
            i = s + ontop_needed * ratio
            
        i = int(min(INJECTION_MAX,i))
        if i != i_old:
            self.zen.greenInjection = i
            print(f"p: {p}, s: {s}({self.zen.solarInputPower}), b: {b} do i {i_old} -> {i}")
            
        else:
            print(f"p: {p}, s: {s}({self.zen.solarInputPower}), b: {b}, i: {i}")
            

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
        client = InfluxDBClient(
            url=INFLUX_URL,
            token=INFLUX_TOKEN,
            org=INFLUX_ORG
        )
        write_api = client.write_api(write_options=SYNCHRONOUS)
        for k,v in d["ENERGY"].items():
            point = ( Point("tasmota").tag("room","keller").tag("domain","electricity").tag("electric","swm").field(k,v) )
            write_api.write(bucket="smarthome", record=point)
            
        p = d["ENERGY"]["Power"]
        if p < 0:
            write_api.write(bucket="smarthome", record=Point("tasmota").tag("room","keller").tag("domain","electricity").tag("electric","swm").field("upstream",p))
            write_api.write(bucket="smarthome", record=Point("tasmota").tag("room","keller").tag("domain","electricity").tag("electric","swm").field("downstream",0))
            
        else:
            write_api.write(bucket="smarthome", record=Point("tasmota").tag("room","keller").tag("domain","electricity").tag("electric","swm").field("upstream",0))
            write_api.write(bucket="smarthome", record=Point("tasmota").tag("room","keller").tag("domain","electricity").tag("electric","swm").field("downstream",p))
            
        client.close()
        
    except:
        print("write to influxdb failed")
        time.sleep(60)
        
    ZM.update(p)

# Client mit neuer Callback-API
client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2
)

# Zendure management
ZM  = ZendureManager( Zendure(ZENDURE_HOST,ZENDURE_SN) )

# Authentifizierung setzen
client.username_pw_set(USERNAME, PASSWORD)

# Callbacks
client.on_connect = on_connect
client.on_message = on_message

# Verbindung
client.connect(BROKER, PORT, keepalive=60)

# Loop starten
client.loop_forever()
