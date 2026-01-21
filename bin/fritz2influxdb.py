from fritzconnection import FritzConnection
from fritzconnection.lib.fritzstatus   import FritzStatus
from fritzconnection.lib.fritzhomeauto import FritzHomeAutomation
from fritzconnection.lib.fritzhosts    import FritzHosts
import json, time, os, datetime, re
from lib.toinflux import Iflx

DEBUG = False

INTERVAL = int(os.getenv("FRITZ_QUERY_INTERVAL"))
INFLUX = Iflx()

class Mapdevice:
    def __init__(self,mapfile):
        self.macmap = {}
        self.mapfile = mapfile
        self.devices = {}
        self.alwayson = []
        self.read_devicemap_last = 0
        self.readmap()
        
    def readmap(self):
        if self.mapfile:
            with open(self.mapfile,"r") as f:
                t = json.load(f)
                f.close()
                self.devices = t["devices"]
                self.alwayson = t["alwayson"]
                self.macmap = {}
                for mac,info in self.devices.items():
                    self.macmap[mac] = info["name"]
                    
                self.read_devicemap_last = datetime.datetime.now()
            
    def getMappedName(self,mac,default=""):
        if self.read_devicemap_last < datetime.datetime.now() - datetime.timedelta(hours=1):
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
        if not self.connect_last or self.connect_last < datetime.datetime.now() - datetime.timedelta(hours=1):
            self.connect_last = datetime.datetime.now()
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
                
                INFLUX.write("fritz_ha","temperature",t,{"room": name, "domain": "temperature"} )
                INFLUX.write("fritz_ha","t_reduced",t_reduced,{"room": name} )
                INFLUX.write("fritz_ha","t_compfort",t_compfort,{"room": name} )
                
        if self.do_transmission_rate:
            fs = FritzStatus(self.fc)
            (up,down) = fs.transmission_rate
            INFLUX.write("fritz_net","up",up*8,{"domain": "network"} )
            INFLUX.write("fritz_net","down",down*8,{"domain": "network"} )
                                                                                              
    def get_hosts(self,mergewith={}):
        for h in self.hosts_seen:
            mergewith[h] = self.hosts_seen[h]
            
        return mergewith


# initialization
DEVLIST = os.getenv("FRITZ_DEVICELIST")
devices = []
for s in DEVLIST.split():
    i = {}
    for k in ["HOST","USER","PASSWORD","FEATURES"]:
        i[k] = os.getenv(f"FRITZ_{s}_{k}",False)
        
    devices.append(i)
    
DEVICEMAP = Mapdevice(os.getenv('FRITZ_DEVICEMAP'))
fritzes = [ myFritz(dev,DEVICEMAP) for dev in devices ]

while True:
    hosts = {}
    for f in fritzes:
        f.measure()
        hosts = f.get_hosts(hosts)
        
    for h in hosts:
        if re.search(r'-pc$',h):
            domain = "presence_pc"
            
        else:
            domain = "presence"
        
        INFLUX.write("fritz_hosts",h,1,{"domain": domain})
        
    time.sleep(INTERVAL)
    
# from fritzconnection.lib.fritzhomeauto import FritzHomeAutomation
# fha = FritzHomeAutomation(address="fritz.box",user="georg",password="bbbbb")
# i = fha.device_information()

# [
# {
#     "NewAIN": "14080 0066824",
#     "NewDeviceId": 19,
#     "NewFunctionBitMask": 320,
#     "NewFirmwareVersion": "03.54",
#     "NewManufacturer": "AVM",
#     "NewProductName": "Comet DECT",
#     "NewDeviceName": "Joni",
#     "NewPresent": "CONNECTED",
#     "NewMultimeterIsEnabled": "DISABLED",
#     "NewMultimeterIsValid": "INVALID",
#     "NewMultimeterPower": 0,
#     "NewMultimeterEnergy": 0,
#     "NewTemperatureIsEnabled": "ENABLED",
#     "NewTemperatureIsValid": "VALID",
#     "NewTemperatureCelsius": 115,    <---------- ./10.0
#     "NewTemperatureOffset": -10,
#     "NewSwitchIsEnabled": "DISABLED",
#     "NewSwitchIsValid": "INVALID",
#     "NewSwitchState": "OFF",
#     "NewSwitchMode": "AUTO",
#     "NewSwitchLock": false,
#     "NewHkrIsEnabled": "ENABLED",
#     "NewHkrIsValid": "VALID",
#     "NewHkrIsTemperature": 115,
#     "NewHkrSetVentilStatus": "TEMP",
#     "NewHkrSetTemperature": 95,
#     "NewHkrReduceVentilStatus": "TEMP",
#     "NewHkrReduceTemperature": 100,
#     "NewHkrComfortVentilStatus": "TEMP",
#     "NewHkrComfortTemperature": 210
#   }
# ...


# from fritzconnection.lib.fritzhosts import FritzHosts
# fh = FritzHosts(address="fritz.box",user="georg",password="BBBBBBB")
# hosts = fh.get_hosts_info()

#[
#  {
#    "ip": "192.168.178.71",
#    "name": "A34-von-Angela",
#    "mac": "AA:EC:2F:C0:41:CC",
#    "status": false,
#    "interface_type": "",
#    "address_source": "DHCP",
#    "lease_time_remaining": 0
#  },
# ....

# from fritzconnection.lib.fritzstatus import FritzStatus
# fs = FritzStatus(fc)
# fs.transmission_rate
# (up,down) = fs.transmission_rate
# up = up *8
# down = down * 8


