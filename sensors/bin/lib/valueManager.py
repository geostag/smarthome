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


        