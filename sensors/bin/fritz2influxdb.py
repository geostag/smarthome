from fritzconnection import FritzConnection
from fritzconnection.lib.fritzstatus   import FritzStatus
from fritzconnection.lib.fritzhomeauto import FritzHomeAutomation
from fritzconnection.lib.fritzhosts    import FritzHosts
import json, time, os, re, requests, traceback
from lib.toinflux import Iflx
from lib.ncConnect import myNextcloud

DEBUG = False

INTERVAL = int(os.getenv("FRITZ_QUERY_INTERVAL"))
INFLUX = Iflx()
DEVICEMAPCACHETIME = 3600
DEVICEMAP = os.getenv("FRITZ_DEVICEMAP","/cproj/Home-IT/smarthome/device-map.json")

class Mapdevice:
    def __init__(self):
        self.macmap = {}
        self.devices = {}
        self.alwayson = []
        self.nextcloud = myNextcloud()
        self.read_devicemap_last = 0
        self.readmap()

    def readmap(self):
        try:
            t = json.loads(self.nextcloud.getFile(DEVICEMAP,cachetime = DEVICEMAPCACHETIME - 2))
            self.devices = t["devices"]
            self.alwayson = t["alwayson"]
            self.macmap = {}
            for mac,info in self.devices.items():
                self.macmap[mac] = info["name"]
                
            self.read_devicemap_last = time.time()

        except:
            print(traceback.format_exc())
            print(f"failed to download DEVICEMAP '{DEVICEMAP}'")
            
    def getMappedName(self,mac,default=""):
        if self.read_devicemap_last < time.time() - DEVICEMAPCACHETIME:
            self.readmap()
            
        return self.macmap.get(mac,default)

class myFritz:
    def __init__(self,dev,dm):
        self.host = dev["HOST"]
        self.user = dev["USER"]
        self.password = dev["PASSWORD"]
        self.devicemap = dm
        self.fc = None
        self.do_hosts = False
        self.hosts_seen = {}
        self.do_ha = False
        self.do_transmission_rate = False
        self.connect_last = False
        for f in dev["FEATURES"].split():
            if f == "hosts":
                self.do_hosts = True
                
            elif f == "transmission_rate":
                self.do_transmission_rate = True
                
            elif f == "ha":
                self.do_ha = True
                
    def connect(self):
        now = time.time()
        if not self.connect_last or self.connect_last < now - 3600:
            self.connect_last = now
            try:
                self.fc = FritzConnection(address=self.host, password=self.password, user=self.user)
                
            except:
                pass
        
    def measure(self):
        if not self.fc:
            self.connect()
            
        if not self.fc:
            return False
            
        if self.do_hosts:
            fh = FritzHosts(self.fc)
            self.hosts_seen = {}
            for h in filter(lambda hi: hi.get("status",False), fh.get_hosts_info()):
                name = self.devicemap.getMappedName(h["mac"],h["name"])
                self.hosts_seen[name] = h
                
        if self.do_ha:
            fha = FritzHomeAutomation(self.fc)
            for h in fha.device_information():
                t          = h.get("NewTemperatureCelsius",False)/10.0
                t_offset   = h.get("NewTemperatureOffset",False)/10.0
                t_reduced  = h.get("NewHkrReduceTemperature",False)/10.0
                t_compfort = h.get("NewHkrComfortTemperature",False)/10.0
                name       = h.get("NewDeviceName",h.get("NewDeviceName","--"))
                
                # respect offset
                t = t - t_offset
                
                INFLUX.write("fritz","temperature",t,{"room": name, "domain": "temperature"} )
                INFLUX.write("fritz","t_reduced",t_reduced,{"room": name} )
                INFLUX.write("fritz","t_compfort",t_compfort,{"room": name} )
                
        if self.do_transmission_rate:
            fs = FritzStatus(self.fc)
            (up,down) = fs.transmission_rate
            INFLUX.write("fritz","up",up*8,{"domain": "network"} )
            INFLUX.write("fritz","down",down*8,{"domain": "network"} )
                                                                                              
    def get_hosts(self,mergewith={}):
        for h in self.hosts_seen:
            mergewith[h] = self.hosts_seen[h]
            
        return mergewith
    
    def macmap(self,mergewith={}):
        for name in self.hosts_seen:
            mergewith[name] = self.hosts_seen[name].get("mac","-")

        return mergewith


# initialization
DEVLIST = os.getenv("FRITZ_DEVICELIST")
devices = []
for s in DEVLIST.split():
    i = {}
    for k in ["HOST","USER","PASSWORD","FEATURES"]:
        i[k] = os.getenv(f"FRITZ_{s}_{k}",False)
        
    devices.append(i)

MD = Mapdevice()    
fritzes = [ myFritz(dev,MD) for dev in devices ]

while True:
    hosts = {}
    macmap = {}
    for f in fritzes:
        f.measure()
        hosts = f.get_hosts(hosts)
        macmap = f.macmap(macmap)
        
    for h in hosts:
        if re.search(r'-pc$',h):
            domain = "presence_pc"
            
        else:
            domain = "presence"

        INFLUX.write("fritz",h,1,{"domain": domain, "mac": macmap[h]})
        
    time.sleep(INTERVAL)
    


