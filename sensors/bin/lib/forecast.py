import os, requests, json, datetime, re, time, traceback

# usage:
#   f = Forecast()
#   print(json.dumps(f.todayData,indent=2))
#   print(f.todaySunMinutes)

FORECASTURL = os.getenv("SUNFORECASTURL")
# https://api.open-meteo.com/v1/forecast?latitude=48.137&longitude=11.575&hourly=temperature_2m,weather_code,cloud_cover,sunshine_duration&timezone=Europe%2FBerlin&forecast_days=1
# https://open-meteo.com/en/docs?forecast_days=1&timezone=Europe%2FBerlin&bounding_box=-90,-180,90,180&latitude=48.137&longitude=11

DAYSBACK = 10

class SunForecast:
    def __init__(self):
        self.rawdata = None
        self.data = {}
        self.today = None
        
    def query(self):
        r = requests.get(FORECASTURL)
        if r.status_code == 200:
            self.rawdata = json.loads(r.text)
            self.parse()
            
        else:
            self.rawdata = None
            self.data = None
            self.datahash = None
            print("could not get SUNFORECAST data")
            
    def parse(self):
        hourly = self.rawdata.get("hourly",{})
        d = [ { "hour": re.sub(r'^\d+-\d+-\d+T(\d+):.*$',r'\1',x) } for x in hourly.get("time",[]) ]
        for t,vs in hourly.items():
            for i,v in enumerate(vs):
                d[i][t] = v
                
        for r in d:
            self.data[r["hour"]] = r
            
    @property
    def todayData(self):
        t = datetime.datetime.today().strftime('%Y-%m-%d')
        if not self.today or self.today != t:
            self.query()
            self.today = t
            
        return self.data
                
    @property
    def todaySunMinutes(self):
        return sum([x["sunshine_duration"] for x in self.todayData])
        
    def getHoursSunMinutes(self,h):
        h = "%02d" % int(h)
        return self.todayData.get(h,{}).get("sunshine_duration",0)

class HistoryMaker:
    def __init__(self,DB,FC):
        self.db = DB
        self.memory = self.db.hash
        self.normalizedSun = {}
        self.today = datetime.datetime.now().strftime('%Y-%m-%d')
        self.sunforecast = FC
        self.lastwrite = 0

    def getTodaysSunPOwerPrediction(self):
        p = 0
        for h in range(0,24):
            h = f"{h:02d}"
            p += self.nomalizedSun.get(h,0) * self.sunforecast.getHoursSunMinutes(h)

        return p

    def nomalizeSunProfile(self):
        # create an over days averaged daily hourly sunshine profile
        n = {}
        for d,c in self.memory.items():
            for h,s in c.items():
                if not h in n:
                    n[h] = { "s": 0, "n": 0 }

                if type(s).__name__ == "int":
                    n[h]["s"] += s
                    n[h]["n"] += 1

        for h,d in n.items():
            n[h] = (d["s"] / d["n"]) if d["n"] > 0 else 0

        self.nomalizedSun = n
        
    def purge(self):
        today_d = datetime.datetime.now().strftime('%Y-%m-%d')
        days = sorted(self.memory.keys())[-DAYSBACK:]
        m = {}
        for d,r in self.memory.items():
            if d != today_d:
                for h,s in r.items():
                    if type(s).__name__ == "dict" and "solarsum" in s:
                        try:
                            s = s["solarsum"] / s["solarnumber"] / s["sun"]

                        except ZeroDivisionError:
                            s = 0

                        r[h] = s

                if d in days:
                    m[d] = r

        self.memory = m
        self.db.hash = self.memory

        try:
            self.nomalizeSunProfile()
            print(self.normalizedSun)
            print(">> today sun predict: %.2f" % self.getTodaysSunPOwerPrediction() )

        except:
            print(traceback.format_exc())
            print("went wrong!!")
        
    def storeSolarValue(self,s):
        n = datetime.datetime.now()
        d = n.strftime('%Y-%m-%d')
        h = n.strftime('%H')
        
        if not self.today or self.today != d:
            self.purge()
            self.today = d
        
        if d not in self.memory:
            self.memory[d] = {}

        if h not in self.memory[d]:
            self.memory[d][h] = { "solarsum": 0, "solarnumber": 0, "sun": 0 }
            
        if type(self.memory[d][h]).__name__ == "dict":
            self.memory[d][h]["solarsum"] += s
            self.memory[d][h]["solarnumber"] += 1
            self.memory[d][h]["sun"] = self.sunforecast.getHoursSunMinutes(h)

        else:
            print(f"dict error: {d} / {h}")
            print(self.memory)

        if self.lastwrite < time.time() - 300:
            self.db.hash = self.memory
            self.lastwrite = time.time()
    