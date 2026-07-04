from lib.toinflux import Iflx
from lib.myDatabase import mDb
from lib.ncConnect import myNextcloud
from lib.mqttconn import WhiteBoard, MqttConn
import os, requests, json, datetime, re, time, traceback

FORECASTURL = os.getenv("SUNFORECASTURL")
APPDIR = os.getenv("SMART_MANAGER_DATADIR","/app/sensors")
INTERVAL = int(os.getenv("QUERY_INTERVAL"))
DRYRUN = (os.getenv("DRYRUN","FALSE") == "TRUE")
if DRYRUN:
    print("------- DRYRUN (sunforecast) --------")

# days back we remember measured pv values
DAYSBACK = 10

DEBUG = False

class SunForecast:
    #
    # Intention: provide a list with one entry per hour with the 
    # expected solarintensity for the geolocation in question
    # for the recent day. List contains 24 entries, for the hours 0..23
    # several values for intensity are possible (depending on data given from url)
    #
    def __init__(self, **kwargs):
        self.rawdata = None
        self.today = None
        self.lastquery = 0
        self.url = kwargs.get("url",FORECASTURL)
        self.db = mDb(f"{APPDIR}/smart-manager-sunforecast2.json")
        
    def parse(self):
        hourly = self.rawdata.pop("hourly")
        meta = self.rawdata
        d = [ { "hour": re.sub(r'^\d+-\d+-\d+T(\d+):.*$',r'\1',x) } for x in hourly.get("time",[]) ]
        for t,vs in hourly.items():
            for i,v in enumerate(vs):
                d[i][t] = v

        # add derived forecast value: cloud_cover * sunshine_duration
        cc = hourly.get("cloud_cover",None)
        sd = hourly.get("sunshine_duration",None)
        if cc and sd:
            for i,(a,b) in enumerate(zip(cc,sd)):
                d[i]["cc_by_sd"] = b * (0.75 + 0.25 * (100-a)/100)

        # get daily data
        daily = self.rawdata.pop("daily",{})
        try:
            sunrise = datetime.datetime.fromisoformat(daily.get("sunrise")[0]).strftime("%H:%M")
            sunset  = datetime.datetime.fromisoformat(daily.get("sunset")[0]).strftime("%H:%M")

        except:
            sunrise = "07:30"
            sunset  = "18:30"
                
        self.db.hash = { "meta": meta, "hourly": d, "sunrise": sunrise, "sunset": sunset }
        self.db.write()
        
    def query(self,**kwargs):
        now = time.time()
        if self.lastquery < now - 1800 or kwargs.get("forced",False):
            if DEBUG:
                print("SF: query")

            try:
                r = requests.get(self.url)
                if r.status_code == 200:
                    self.rawdata = json.loads(r.text)
                    self.parse()
                    
                else:
                    self.rawdata = None
                    print(f"could not get SUNFORECAST data '{self.url}'")
            except:
                print(f"Failed to get sf data '{self.url}'")

            self.lastquery = now

    @property
    def sunrise(self):
        try:
            return self.db.hash["sunrise"]
        except:
            return "07:30"

    @property
    def sunset(self):
        try:
            return self.db.hash["sunset"]
        except:
            return "18:30"

    @property
    def hourlyData(self):
        t = datetime.datetime.today().strftime('%Y-%m-%d')
        if not self.today or self.today != t:
            self.query(forced = True)
            self.today = t

        return self.db.hash["hourly"]
            
    @property
    def forecastDimensions(self):
        d = list(self.hourlyData[0].keys())
        d.remove("hour")
        d.remove("time")
        return d
            
    def getHourlyValues(self,k):
        return [ x.get(k,None) for x in self.hourlyData ]

class HistoryMaker:
    #
    # store recent pv energy (Wh) values together with forecast data
    # use to get prediction for todays ov energy
    #
    # data model (reflected in persistent mDb)
    # ----------------------------------------
    # dataHistory:
    #   {
    #     "YYYY-MM-DD": [
    #        { "pvenergy": 12.3, "cloud_cover": 78, "sunshine_duration": 3450 },
    #        { "pvenergy": 12.3, "cloud_cover": 78, "sunshine_duration": 3450 },
    #         ... array with one record for each hour ...
    #     ]
    #   }
    # dataToday:
    #   [
    #       { "pvsum": 0,    "pvnum": 0 },
    #       { "pvsum": 34.5, "pvnum": 3 },
    #       ... array with one record for each hour ...
    #   ]
    # today: YYYY-MM-DD # tag of recent day
    #
    def __init__(self, **kwargs):
        self.sunforecast = kwargs.get("sunforecast",SunForecast())
        self.db = kwargs.get("database",mDb(f"{APPDIR}/smart-manager-solarhistory2.json",autoflush=False))
        self._normalizedEnergyProfileData = {}
        self.lastwrite = 0
        self.nextcloud = myNextcloud()
        self.mqttconnection = MqttConn()
        
    @property
    def dataHistory(self):
        return self.db.get("dataHistory",{})
        
    @dataHistory.setter
    def dataHistory(self,pv):
        self.db.set("dataHistory",pv)

    @property
    def dataToday(self):
        d = self.db.get("dataToday")
        if not d:
            d = [ { "pvsum": 0, "pvnum": 0 } for i in range(0,24) ]
        return d
        
    @dataToday.setter
    def dataToday(self,pv):
        self.db.set("dataToday",pv)

    @property
    def todaysEnergySoFar(self):
        e = 0
        for i in self.dataToday:
            if i["pvnum"] > 0:
                e += i["pvsum"] / i["pvnum"]

        return e

    def _normalizedEnergyProfile(self,dim):
        # returns an hourly array of energy under perfect conditions in specified dimenson
        if dim not in self._normalizedEnergyProfileData:
            energy = [ 0 for i in range(0,24) ]
            # fallback
            self._normalizedEnergyProfileData[dim] = energy
            if self.dataHistory:
                for day,ddata in self.dataHistory.items():
                    for i,hdata in enumerate(ddata):
                        c = hdata.get(dim,0)
                        if c > 0:
                            energy[i] += hdata["pvenergy"] / c

                num = len(self.dataHistory.keys())
                if num > 0:
                    self._normalizedEnergyProfileData[dim] = [ x / num for x in energy ]
        
        return self._normalizedEnergyProfileData[dim]
        
    def _predictedTodaysPowerDim(self,dim):
        # scalarproduct of normalizedEnergyProfile with recent forecast - based on selected dimension
        e = 0
        for p,c in zip(self._normalizedEnergyProfile(dim),self.sunforecast.getHourlyValues(dim)):
            e += p * c
            
        return e
        
    def purge(self,day):
        if not self.dataToday or not day:
            return
        
        m = []
        # build hourly average values for pv energy (unit: Wh)
        for hd in self.dataToday:
            if hd["pvnum"] > 0:
                m.append( {"pvenergy": hd["pvsum"]/hd["pvnum"]} )
                
            else:
                m.append( {"pvenergy": 0} )
            
        # enrich hourly data with forecast data of recent day
        for dim in self.sunforecast.forecastDimensions:
            data = self.sunforecast.getHourlyValues(dim)
            for a,b in zip(m,data):
                a[dim] = b

        # delete too old history data (based on DAYSBACK)
        dh = self.dataHistory
        days = dh.keys()
        for d in list( set(days) - set(sorted(days)[-DAYSBACK:]) ):
            dh.pop(d)
                
        # add todays data
        dh[day] = m
        self.dataHistory = dh
        # reset memorized energy profiles
        self._normalizedEnergyProfileData = {}
        self.db.write()

        # log to nextcloud
        if not DRYRUN:
            try:
                self.nextcloud.putFileFromFile("/cproj/Home-IT/smarthome/smart-manager-solarhistory2.json",f"{APPDIR}/smart-manager-solarhistory2.json")
                self.nextcloud.putFileFromFile("/cproj/Home-IT/smarthome/smart-manager-sunforecast2.json",f"{APPDIR}/smart-manager-sunforecast2.json")
            except:
                pass

    def storeSolarValue(self,s):
        n = datetime.datetime.now()
        d = n.strftime('%Y-%m-%d')
        h = n.hour
        
        t = self.db.get("today")
        if not t or t != d:
            # purge and reset todays data
            try:
                self.purge(t)
            except:
                print(traceback.format_exc())

            self.db.set("today",d)
            self.dataToday = None
            
        tdata = self.dataToday
        tdata[h]["pvsum"] += s
        tdata[h]["pvnum"] += 1
        self.dataToday = tdata
        
        if self.lastwrite < time.time() - 2 * INTERVAL:
            self.db.write()
            self.predictedTodaysPower()

        if DEBUG:
            print(f"solar: {s}")
        
    def predictedTodaysPower(self):
        data = {}
        for dim in self.sunforecast.forecastDimensions:
            e = self._predictedTodaysPowerDim(dim)
            #print(f"sunpredict: {dim}: {e}")
            INFLUX.write("sunforecast","sunpredict",e,{"synthetic": "yes", "dimension": dim})
            data[dim] = e

        if self.mqttconnection:
            data["energyEarnedToday"] = self.todaysEnergySoFar
            data["sunrise"] = self.sunforecast.sunrise
            data["sunset"]  = self.sunforecast.sunset
            self.mqttconnection.publish("tele/sunforecast/SENSOR",json.dumps(data))

class SolarInput:
    def __init__(self):
        self.wb = WhiteBoard()
        
    @property
    def solarInputPower(self):
        return self.wb.dataGet("zendure","solarInputPower")
        
INFLUX = Iflx()
SF = SunForecast()
HM = HistoryMaker(sunforecast = SF)
SI = SolarInput()

while True:
    SF.query()
    for i in range(10):
        HM.storeSolarValue(SI.solarInputPower)
        time.sleep(INTERVAL)

