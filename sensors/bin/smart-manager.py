from lib.config import settings
from lib.mqttconn import WhiteBoard
from lib.toinflux import Iflx
from lib.ncConnect import myNextcloud
from lib.valueManager import memorizedValue
import datetime, time, os, requests, tomllib, traceback

DEBUG = False

ZENDURE_HOST = os.getenv("ZENDURE_HOST")
ZENDURE_SN   = os.getenv("ZENDURE_SN")

INJECTION_MAX = settings.smartmanager.INJECTION_MAX
BATT_MIN      = settings.smartmanager.BATT_MIN
BATT_MAX      = settings.smartmanager.BATT_MAX
BATT_CAPACITY = settings.smartmanager.BATT_CAPACITY
BASELOAD      = settings.smartmanager.BASELOAD
DATADIR       = settings.smartmanager.SMART_MANAGER_DATADIR
INTERVAL      = settings.smartmanager.SMART_MANAGER_INTERVAL

# https://github.com/Zendure/zenSDK/issues/5
ZENDURE_MIN_LIMIT_INTERVAL = int(os.getenv("ZENDURE_MIN_LIMIT_INTERVAL","10"))

DRYRUN = (os.getenv("DRYRUN","FALSE") == "TRUE")
if DRYRUN:
    print("------- smart-manager: DRYRUN --------")

# how many watt to reserve for zendure itself
RESW = 8

class Forecast:
    def __init__(self,wb):
        self.wb = wb

    @property
    def energyToCome(self):
        return self.wb.dataGet("sunforecast","FNTM_cc_by_sd")
    
    
    @property
    def sunrise(self):
        t = self.wb.dataGet("sunforecast","sunrise")
        if not t:
            t = "07:00"
        return datetime.time.fromisoformat(t)

    @property
    def sunset(self):
        t = self.wb.dataGet("sunforecast","sunset")
        if not t:
            t = "20:00"
        return datetime.time.fromisoformat(t)

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
        self.lastOutputLimitChange = 0
        
    @property
    def solarInputPower(self):
        return self.wb.dataGet("zendure","solarInputPower")
        
    @property
    def electricLevel(self):
        return self.wb.dataGet("zendure","electricLevel")
        
    @property
    def isMaxOutput(self):
        return (self.outputLimit > 0.97 * INJECTION_MAX)
        
    @property
    def outputLimit(self):
        if self.injection < 0:
            self.injection = self.wb.dataGet("zendure","outputLimit")
            
        return self.injection
        
    @outputLimit.setter
    def outputLimit(self,value):
        value = max(value,0)
        value = int(min(INJECTION_MAX,value) + 0.5) * 1.0
        
        now = time.time()
        if self.lastOutputLimitChange > now - ZENDURE_MIN_LIMIT_INTERVAL:
            return False
            
        self.lastOutputLimitChange = now

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
    def __init__(self,zen,tasmota,forecast,influx):
        self.zen = zen
        self.tasmota = tasmota
        self.forecast = forecast
        self.gridpower = memorizedValue(60 * 10)
        self.solarInputPower = memorizedValue(60 * 15)
        self.neededPower = memorizedValue(60 * 60 * 6)
        self.baseload = BASELOAD
        self.chargefrombase = True
        self.paramterlast = 0
        self.nextcloud = myNextcloud()
        self.generosityHistory = []
        self.generosInjection = 0
        self.influx = influx

    def dynamicParameterUpdate(self):
        if time.time() > self.paramterlast + 900 and settings.DYNAMIC_CONFIG_PATH:
            self.paramterlast = time.time()
            try:
                ctext = self.nextcloud.getFile(settings.DYNAMIC_CONFIG_PATH)
                settings.update(tomllib.loads(ctext))
                self.baseload = settings.smartmanager.BASELOAD
            except:
                print(traceback.format_exc())
                print("dynamic parameter update failed")
        
    @property
    def isBlue(self):
        # we deliver upstream, but could do better
        return (self.tasmota.Power < -1 and not self.isGenerous)
        
    @property
    def isRed(self):
        # we use grid downstream but could do better
        return (self.tasmota.Power > 2 and not self.zen.isMaxOutput and not self.chargefrombase)
        
    @property
    def isGenerous(self):
        return (self.generosInjection > 0)
    
    @property
    def bratio(self):
        # battery fill ratio
        # range: 0...1
        b = self.zen.electricLevel
        return int(100 * (b - BATT_MIN)/(BATT_MAX-BATT_MIN) + 0.5) / 100
    
    @property
    def isSunshine(self):
        sunset  = self.forecast.sunset
        sunrise = self.forecast.sunrise
        now = datetime.datetime.now().time()
        return ( now > sunrise and now < sunset )

    def _timeFloat(self,ts):
        return ts.hour + ts.minute / 60 + ts.second / 3600
        
    @property
    def hourFloat(self):
        return self._timeFloat(datetime.datetime.now())
    
    @property
    def sunhours(self):
        return max(4,self._timeFloat(self.forecast.sunset) - self._timeFloat(self.forecast.sunrise))
        
    @property
    def remainingsunhours(self):
        return max(0,self._timeFloat(self.forecast.sunset) - self._timeFloat(datetime.datetime.now().time()))

    @property
    def battCapacityNeeded(self):
        return BATT_CAPACITY * 1.2
        
    @property
    def energyExcessToCome(self):
        avgLoad = self.neededPower.get("avg")
        if not avgLoad:
            avgLoad = self.baseload
            
        return max(0,self.forecast.energyToCome - avgLoad * self.remainingsunhours)

    @property
    def energyOverBattToCome(self):
        return max(0,self.energyExcessToCome - self.battCapacityNeeded * (1-self.bratio))

    @property
    def generosity(self):
        now = datetime.datetime.now().time()
        sunset  = self.forecast.sunset
        sunrise = self.forecast.sunrise

        if self.energyOverBattToCome > 0:
            gnow = min(2, 1 + 2 * self.energyOverBattToCome / self.battCapacityNeeded)

        else:
            energy = self.forecast.energyToCome + self.battCapacityNeeded * self.bratio
            needed = self.baseload * 24
            gnow = energy / needed
            gnow = min(1,gnow)
            gnow = max(0,gnow)

        # average g over last 30min
        nowsecs = time.time()
        self.generosityHistory.append({ "t": nowsecs, "v": gnow })
        self.generosityHistory = [ x for x in self.generosityHistory if x["t"] > nowsecs - 1800 ]
        vs = [ x["v"] for x in self.generosityHistory ]
        g = sum(vs)/len(vs)

        if now < sunrise:
            g = self.bratio + 0.5 * g
        
        elif now > sunset:
            g = self.bratio

        self.influx.write("debug","energyToCome",1.0 * self.forecast.energyToCome,{"synthetic": "yes", "debug": 1})
        self.influx.write("debug","energyExcessToCome",1.0 * self.energyExcessToCome,{"synthetic": "yes", "debug": 1})
        self.influx.write("debug","energyOverBattToCome",1.0 * self.energyOverBattToCome,{"synthetic": "yes", "debug": 1})
        return g

    def controller_update(self):
        #TODO
        #self.dynamicParameterUpdate()
        
        b = self.zen.electricLevel
        i = self.zen.outputLimit
        i_old = int(i)

        self.influx.write("smart-manager","generosity2",1.0 * self.generosity,{"synthetic": "yes", "debug": 1})

        s = self.zen.solarInputPower
        self.solarInputPower.add(s)
        s10 = self.solarInputPower.get("avg",60 * (11 - int(5 * self.generosity + 0.5)))
        
        p = self.tasmota.Power
        self.gridpower.add(p)

        if p < 0 and not self.isGenerous and self.bratio > 0.6:
            # we deliver upstream. react slowly in some cases
            p = max(self.gridpower.get("max",1 + 60*self.generosity),self.gridpower.get("avg",1 + 180*self.generosity))

        needed = i+p
        self.neededPower.add(needed)

        if b >= 2.0 * BATT_MIN:
            self.chargefrombase = False
        
        # values ready, lets do logic
        if b <= BATT_MIN:
            # first load battery
            i = 0
            self.chargefrombase = True
            
        elif self.chargefrombase and b < 1.5 * BATT_MIN:
            # we were discharged, first charge significant
            i = 0

        elif self.chargefrombase:
            i = min(s,needed)
                        
        elif b >= BATT_MAX:
            # batt full, still charging
            # approach: input = output; slow changes; at least needed power
            i = min(s10,INJECTION_MAX)
            i = max(i,needed)
            
        elif s10 > needed:
            # more sun than needed
            i = needed
            
            if self.isSunshine and self.generosity > 1:
                # add generosity upstream 
                reserve = 150 + 700 * self.remainingsunhours / self.sunhours
                upstream = max(0,(self.energyOverBattToCome - reserve) / min(0.1,self.remainingsunhours))
                gi = max(0,needed + upstream)
                gi = min(INJECTION_MAX,gi)
                self.generosInjection = self.generosInjection * 0.85 + gi * 0.15
                i = max(self.generosInjection,needed)
                i = min(s10 - RESW,i)

            else:
                self.generosInjection = 0

        else:
            # maximum discharge based on reserves in battery or sun (whatever is more)
            minj = (2 + 2 * self.generosity) * self.baseload
            maxj = self.bratio * (INJECTION_MAX - minj) + minj
            maxtotal = max(maxj,s10)
            i = min(maxtotal,needed + 5 * self.generosity )
            
        # round and limit to INJECTION_MAX
        i = int(min(INJECTION_MAX,i) + 0.5) * 1.0
        
        # whereever we land, if we have enough energy, provide at least BASELOAD
        if b > 1.5 * BATT_MIN:
            i = max(i,self.baseload)
                    
        if p > 0:
            # we use grid power
            if ( i > 5 and abs(i-i_old) < 3 ) or ( i > 100 and abs(i-i_old)/i < 0.03 ):
                # peanut change
                i = i_old
                
            elif i > i_old:
                # increase injection slowly
                i = (0.9 + 0.05 * self.generosity) * (i - i_old) + i_old
        
        if "HARDOUTPUT" in settings.smartmanager:
            i = settings.smartmanager.HARDOUTPUT

        if i != i_old:
            self.zen.outputLimit = i

# ----------------------------- main -------------------------------

# Whiteboard with recent data
WB  = WhiteBoard()
# Zendure management
ZM  = ZendureManager( Zendure(ZENDURE_HOST, ZENDURE_SN, WB), Tasmota(WB), Forecast(WB), Iflx() )

def tasmotaCallback(data):
    p = data.get("Power",0)
    if ( ZM.isBlue and p < -5 ) or ( ZM.isRed and p > 25 ):
        # we react immediately on significant upstream or downstream
        ZM.controller_update()

# trigger callback, when new tasmota values available
WB.addDeviceListener("tasmota",tasmotaCallback)

while True:
    time.sleep(INTERVAL)
    ZM.controller_update()
    
