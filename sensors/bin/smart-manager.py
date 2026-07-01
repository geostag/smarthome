from lib.mqttconn import WhiteBoard
from lib.myLog import mLog
from lib.toinflux import Iflx
from lib.myDatabase import mDb
from lib.ncConnect import myNextcloud
import datetime, time, os, requests

DEBUG = True

ZENDURE_HOST = os.getenv("ZENDURE_HOST")
ZENDURE_SN   = os.getenv("ZENDURE_SN")

INJECTION_MAX = int(os.getenv("INJECTION_MAX",800))
BATT_MIN      = int(os.getenv("MATT_MIN",10))
BATT_MAX      = int(os.getenv("BATT_MAX",95))
BASELOAD      = int(os.getenv("BASELOAD",90))
GRIDPOWERREMEMBER_MINUTES = 6

DATADIR = os.getenv("SMART_MANAGER_DATADIR","/app/sensors")
DYNAMIC_PARAMETER_PATH = os.getenv("SMART_MANAGER_DYNAMIC_PARAMETER_PATH","")

INTERVAL = 90

DRYRUN = (os.getenv("DRYRUN","FALSE") == "TRUE")
if DRYRUN:
    print("------- DRYRUN --------")

# how many watt to reserve for zendure itself
RESW = 8

class Forecast:
    def __init__(self,wb):
        self.wb = wb

    @property
    def predictedEnergy(self):
        return self.wb.dataGet("sunforecast","sunshine_duration")

    @property
    def earnedEnergy(self):
        return self.wb.dataGet("sunforecast","energyEarnedToday")
    
    @property
    def energyToCome(self):
        return max(0,self.predictedEnergy - self.earnedEnergy)

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
        
        value = max(value,0)
        value = int(min(INJECTION_MAX,value) + 0.5) * 1.0

        if DRYRUN:
            print(f"DRYRUN: setting output to value {value}")
            return True
        
        data = { 
            "sn": self.sn,
            "properties": { "outputLimit": int(value) }
        }
        try:
            r = requests.post(self.url, json=data)

        except:
            return False
        
        if r.status_code != 200:
            print(f"ERROR setting outputlimit: {r.status_code}")
            return False
            
        else:
            self.injection = value
            return True
        
class ZendureManager:
    def __init__(self,zen,tasmota,forecast):
        self.zen = zen
        self.tasmota = tasmota
        self.forecast = forecast
        self.gridpower = []
        self.solarInputPower = []
        self.last_controller_update = 0
        self.db = mDb(f"{DATADIR}/smart-manager-state.json")
        self.baseload = BASELOAD
        self.chargefrombase = True
        self.parameterurl = os.getenv("SMART_MANAGER_DYNAMIC_PARAMETER_PATH","")
        self.paramterlast = 0
        self.nextcloud = myNextcloud()

    def dynamicParameterUpdate(self):
        if time.time() > self.paramterlast + 900 and DYNAMIC_PARAMETER_PATH:
            self.paramterlast = time.time()
            ptext = self.nextcloud.getFile(DYNAMIC_PARAMETER_PATH)
            p = {}
            for l in ptext.splitlines():
                l = l.strip()
                if not l:
                    continue

                k,v = l.split(":",1)
                k = k.strip()
                v = v.strip()
                if v.isdigit():
                    v = int(v)

                p[k] = v

            #self.baseload = p.get("BASELOAD", BASELOAD)
            bl = p.get("BASELOAD", BASELOAD)
            if self.baseload != bl:
                print(f"BASELOAD: {self.baseload} > {bl}")
                self.baseload = p.get("BASELOAD", BASELOAD)
        
    def rememberGridPower(self,p):
        self.gridpower.append( { "t": time.time(), "v": p } )
        now = time.time()
        self.gridpower = [ x for x in self.gridpower if x["t"] > now - GRIDPOWERREMEMBER_MINUTES*60 ]
        
    def minRememberGridPower(self):
        return min( [ x["v"] for x in self.gridpower ] )
        
    def avgRememberGridPower(self):
        vs = [ x["v"] for x in self.gridpower ]
        return sum(vs)/len(vs)
        
    def weightedAvgRememberGridPower(self):
        vs = [ x["v"] for x in self.gridpower ]
        n = len(vs)
        if n > 1:
            weights = [i / (n - 1) for i in range(n)]
            weighted_sum = sum(v * w for v, w in zip(vs, weights))
            return weighted_sum / sum(weights)
        
        else:
            return vs[0]

    @property
    def isUpstream(self):
        return (self.tasmota.Power < 0)
    
    @property
    def hourFloat(self):
        hour = datetime.datetime.now().hour
        minute = datetime.datetime.now().minute
        return hour + minute / 60
    
    @property
    def bratio(self):
        # battery fill ratio
        # range: 0...1
        b = self.zen.electricLevel
        return int(100 * (b - BATT_MIN)/(BATT_MAX-BATT_MIN) + 0.5) / 100
    
    @property
    def generosity(self):
        tc = self.forecast.energyToCome / 4000
        return min(2, self.bratio + tc)

    def controller_update(self,force = False):
        if self.last_controller_update > time.time() - INTERVAL and not force:
            return True
        
        self.last_controller_update = time.time()

        self.dynamicParameterUpdate()
        
        b = self.zen.electricLevel
        i = self.zen.outputLimit
        i_old = int(i)
                
        lookback_items = 11 - int(5 * self.generosity + 0.5)
        s = self.zen.solarInputPower
        self.solarInputPower.append(s)
        self.solarInputPower = self.solarInputPower[(-1 * lookback_items):]
        s10 = int( 10 * sum(self.solarInputPower) / len(self.solarInputPower) + 0.5) / 10
        p = self.tasmota.Power
        self.rememberGridPower(p)
        if b > 20:
            p = self.weightedAvgRememberGridPower()

        else:
            p = self.minRememberGridPower()
        
        needed = i+p
        mode = ""

        if b >= 2.0 * BATT_MIN:
            self.chargefrombase = False
        
        # values ready, lets do logic
        if b <= BATT_MIN:
            # first load battery
            mode = "super low batt"
            i = 0
            self.chargefrombase = True
            
        elif self.chargefrombase and b < 1.5 * BATT_MIN:
            # we were discharged, first charge significant
            mode = "charge from base < 1.5"
            i = 0

        elif self.chargefrombase:
            mode = "charge from base >= 1.5"
            i = s
                        
        elif b >= 0.95 * BATT_MAX and s10 > 0.5 * i_old:
            # batt full, still charging
            # approach: input = output; slow changes; at least needed power
            mode = "super hi batt"
            i = BASELOAD + self.bratio * INJECTION_MAX
            i = 0.5 * (i - i_old) + i_old
            i = max(i,needed)
            
        elif s10 > needed:
            # more sun than needed
            mode = "hi sun"
            i = needed
            
        else:
            # maximum discharge based on reserves in battery or sun (whatever is more)
            minj = 2.0 * self.baseload
            maxj = self.bratio * (INJECTION_MAX - minj) + minj
            maxtotal = max(maxj,s10)
            mode = f"blow out {self.bratio}, {maxj}, {s}({s10})"
            i = min(maxtotal,needed)

        # round and limit to INJECTION_MAX
        i = int(min(INJECTION_MAX,i) + 0.5) * 1.0
        
        # whereever we land, if we have enough energy, provide at least BASELOAD
        if b > 1.5 * BATT_MIN:
            i = max(i,self.baseload)
                    
        if p > 0:
            # we use grid power
            if ( i > 10 and abs(i-i_old) < 3 ) or ( i > 100 and abs(i-i_old)/i < 0.03 ):
                # peanut change
                mode += f", peanuts {i} {i_old}"
                i = i_old
                
            elif i > i_old:
                # increase injection slowly
                mode += ", slow-raise"
                i = (0.9 + 0.05 * self.generosity) * (i - i_old) + i_old
        
        if i != i_old:
            if ML:
                ML.log(f"p: {p}, s: {s}({s10}), b: {b} do i {i_old} -> {i} ({mode})")

            if DEBUG:
                print(f"p: {p}, s: {s}({s10}), b: {b} do i {i_old} -> {i} ({mode}; CFB:{self.chargefrombase})")
                
            self.zen.outputLimit = i
            
        else:
            if ML: 
                ML.log(f"p: {p}, s: {s}({s10}), b: {b}, i: {i} ({mode})")


# ----------------------------- main -------------------------------

# InfluxDB connection to create a heartbeat
INFLUX = Iflx()
# Whiteboard with recent data
WB  = WhiteBoard()
# Zendure management
ZM  = ZendureManager( Zendure(ZENDURE_HOST, ZENDURE_SN, WB), Tasmota(WB), Forecast(WB) )

def tasmotaCallback(data):
    if data.get("Power",0) < 0:
        # we deliver power to the grid, call the smart manager immediately
        if DEBUG:
            ML.log("yusha, call update")
            
        ZM.controller_update(True)

# trigger callback, when new tasmota values available
WB.addDeviceListener("tasmota",tasmotaCallback)

if DEBUG:
    ML = mLog("smart-manager")
    
else:
    ML = None

while True:
    time.sleep(INTERVAL)
    ZM.controller_update()
    INFLUX.heartbeat("smart-manager")
