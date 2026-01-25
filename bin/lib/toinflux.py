from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import os

INFLUX_URL   = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG   = os.getenv("INFLUX_ORG")
INFLUX_BUCKET= os.getenv("INFLUX_BUCKET")

class Iflx:
    def __init__(self,**kwargs):
        self.bucket = kwargs.get("bucket",INFLUX_BUCKET)
        self.token  = kwargs.get("token",INFLUX_TOKEN)
        self.client = None
        self.api = None
        
    def openClient(self):
        self.client = InfluxDBClient(
            url=INFLUX_URL,
            token=self.token,
            org=INFLUX_ORG
        )
        self.api = self.client.write_api(write_options=SYNCHRONOUS)
        
    def reset(self):
        if self.client:
            try:
                self.client.close()
                
            except:
                pass
        
        self.client = None
        self.api = None

    def write(self,measurement,key,value,tags,timestamp=None):
        if not self.api:
            self.openClient()
            
        p = Point(measurement)
        for t,v in tags.items():
            p.tag(t,v)
            
        p.field(key,value)
        
        if timestamp:
            p.time(timestamp,WritePrecision.NS)
            
        #print(p)
        
        try:
            self.api.write(bucket=self.bucket, record = p)

        except:
            self.reset()
            