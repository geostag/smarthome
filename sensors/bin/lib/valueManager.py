import time

class changeLimitedFreq:
    def __init__(self,**kwargs):
        # minimum seconds to wait
        self.mindur = kwargs.get("mindur",60)
        self.minabs = kwargs.get("minabs",5)
        self.minper = kwargs.get("minper",5)
        self.lastvalue = 0
        self.lastchange = 0

    def targetValue(self,value,**kwargs):
        forced = kwargs.get("forced",False)
        now = time.time()
        md = now > self.lastchange + self.mindur
        ma = abs(self.lastvalue - value) > self.minabs
        mp = 100 * abs((self.lastvalue - value)/self.lastvalue) > self.minper
        if forced or (md and ma and mp):
            self.lastvalue = value
            self.lastchange = now

        return self.lastvalue

class memorizedValue:
    def __init__(self,maxbacksecs):
        self.values = []
        self.maxbacksecs = maxbacksecs

    def add(self,v):
        self.values.append({"v": v, "t": time.time()})

    def _purge(self):
        l = []
        now = time.time()
        for i in self.values:
            if i["t"] >= now - self.maxbacksecs:
                l.append(i)

        self.values = l

    def _getTrend(self,data):
        n = len(data)
        if n < 2:
            return 0.0

        t0 = data[0]["t"]
        x = [p["t"] - t0 for p in data]
        y = [p["v"] for p in data]
        xm = sum(x) / n
        ym = sum(y) / n
        numerator = sum((x[i] - xm) * (y[i] - ym) for i in range(n))
        denominator = sum((xi - xm) ** 2 for xi in x)
        if denominator == 0:
            return 0.0

        return numerator / denominator

    def get(self,cf,backsecs=None):
        self._purge()
        if backsecs:
            threshould = time.time() - backsecs
        else:
            threshould = 0

        lf = sorted(filter(lambda x: x["t"] >= threshould,self.values), key=lambda x: x["t"])
        l = [ x["v"] for x in lf ]
        if len(l) < 1:
            return None
        elif cf == "max":
            return max(l)
        elif cf == "min":
            return min(l)
        elif cf == "avg":
            return sum(l)/len(l)
        elif cf == "avglinweighted":
            start = lf[0]["t"]
            end   = lf[-1]["t"]
            if end > start:
                s = 0
                n = 0
                for i in lf:
                    f = (i["t"]-start)/(end-start)
                    s += i["v"] * f
                    n += f

                return s/n
            else:
                return lf[0]["v"]

        elif cf == "trend":
            return self._getTrend(lf)
            
        else:
            return None
