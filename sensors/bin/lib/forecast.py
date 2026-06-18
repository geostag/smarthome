from lib.toinflux import Iflx
from lib.myDatabase import mDb
from lib.ncConnect import myNextcloud
import os, requests, json, datetime, re, time, traceback

# usage:
#   f = Forecast()
#   print(json.dumps(f.todayData,indent=2))
#   print(f.todaySunMinutes)

FORECASTURL = os.getenv("SUNFORECASTURL")
#FORECASTURL = 'https://api.open-meteo.com/v1/forecast?latitude=48.137&longitude=11.575&hourly=temperature_2m,weather_code,cloud_cover,sunshine_duration,direct_radiation,diffuse_radiation,direct_normal_irradiance&timezone=Europe%2FBerlin&forecast_days=1'

APPDIR = os.getenv("SMART_MANAGER_DATADIR","/app/sensors")

# days back we remember measured pv values
DAYSBACK = 20

INFLUX = Iflx()

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
                d[i]["cc_by_sd"] = (100-a)*b/100
                
        self.db.hash = { "meta": meta, "hourly": d }
        self.db.write()
        
    def query(self):
        r = requests.get(self.url)
        if r.status_code == 200:
            self.rawdata = json.loads(r.text)
            self.parse()
            self.lastquery = time.time()
            
        else:
            self.rawdata = None
            print(f"could not get SUNFORECAST data '{self.url}'")

    @property
    def hourlyData(self):
        t = datetime.datetime.today().strftime('%Y-%m-%d')
        if not self.today or self.today != t or self.lastquery < time.time() - 3600:
            self.query()
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
        
        if self.lastwrite < time.time() - 30:
            self.db.write()
            self.predictedTodaysPower()
        
    def predictedTodaysPower(self):
        for dim in self.sunforecast.forecastDimensions:
            e = self._predictedTodaysPowerDim(dim)
            #print(f"sunpredict: {dim}: {e}")
            INFLUX.write("smart-manager","sunpredict",e,{"synthetic": "yes", "dimension": dim})
    