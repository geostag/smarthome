from lib.mqttconn import WhiteBoard
import datetime, time, os, requests

DEBUG = False

ZENDURE_HOST = os.getenv("ZENDURE_HOST")
ZENDURE_SN   = os.getenv("ZENDURE_SN")

INJECTION_MAX = int(os.getenv("INJECTION_MAX",800))
BATT_MIN      = int(os.getenv("MATT_MIN",10))
BATT_MAX      = int(os.getenv("BATT_MAX",95))
BASELOAD      = int(os.getenv("BASELOAD",90))

# how many watt to reserve for zendure itself
RESW = 8

# lookback items (tasmota sends every minute, thus 5 minutes)
LOOKBACK_ITEMS = 10

class Tasmota:
    def __init__(self,wb):
        self.wb = wb
        
    @property
    def Power(self):
        return self.wb.dataGet("tasmota","Power")

class Zendure:
    def __init__(self,host,sn,wb):
        self.host = host
        self.sn = sn
        self.wb = wb
        self.injection = 0
        self.url = f"{host}/properties/write"
        self.injection = -1
        
    @property
    def solarInputPower(self):
        return self.wb.dataGet("zendure","solarInputPower")
        
    @property
    def electricLevel(self):
        return self.wb.dataGet("zendure","electricLevel")
        
    @property
    def outputLimit(self):
        if self.injection < 0:
            self.injection = self.wb.dataGet("zendure","outputLimit")
            
        return self.injection
        
    @outputLimit.setter
    def outputLimit(self,value):
        #print(f"pushing to zendure: {value}")
        #return True
        
        value = max(value,0)
        value = int(min(INJECTION_MAX,value) + 0.5) * 1.0
        
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
            return True
        
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
            i = p + i - RESW
            
        elif b > 1.2 * BATT_MIN and s > (RESW+2) and s < p+i:
            # enough power there, baseload (discharge mode, while sun still there)
            mode = "low sun, use battery on top"
            i = min(2*BASELOAD,i+p - RESW)
            
        elif s > (RESW+2) and s < p+i:
            # sun there and completely needed, do not discharge
            # keep 3W for zendure itself
            mode = f"low sun {p},{s},{i}"
            i = s - RESW
            
        else:
            # maximum 3*baseload discharge
            mode = "6baseload"
            i = min(6*BASELOAD,i+p)
            
        # round and limit to INJECTION_MAX
        i = int(min(INJECTION_MAX,i) + 0.5) * 1.0
        i = max(i,0)
        
        if p > 0:
            # we use grid power
            if ( i > 10 and abs(i-i_old) < 3 ) or ( i > 100 and abs(i-i_old)/i < 0.03 ):
                # peanut change
                mode += f", peanuts {i} {i_old}"
                i = i_old
                
            elif i > i_old:
                # increase injection slowly
                mode += ", slow-raise"
                i = 0.6*(i_old + i)
        
        if i != i_old:
            print(f"p: {p}, s: {s}, b: {b} do i {i_old} -> {i} ({mode})")
            self.zen.outputLimit = i
            
        else:
            print(f"p: {p}, s: {s}, b: {b}, i: {i} ({mode})")


# ----------------------------- main -------------------------------

# Whiteboard with recent data
WB  = WhiteBoard()
# Zendure management
ZM  = ZendureManager( Zendure(ZENDURE_HOST, ZENDURE_SN, WB), Tasmota(WB) )

while True:
    time.sleep(60)
    ZM.controller_update()
