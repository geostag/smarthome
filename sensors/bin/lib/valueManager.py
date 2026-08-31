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

    def get(self,cf,backsecs):
        self._purge()
        now = time.time()
        l = [ x["v"] for x in filter(lambda x: x["t"] >= now - backsecs,self.values) ]
        if len(l):
            return None
        elif cf == "max":
            return max(l)
        elif cf == "min":
            return min(l)
        elif cf == "avg":
            return sum(l)/len(l)
        else:
            return None