from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import os

INFLUX_URL   = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG   = os.getenv("INFLUX_ORG")
INFLUX_BUCKET= os.getenv("INFLUX_BUCKET")

class Iflx:
    def __init__(self):
        self.client = None
        self.api = None
        
    def openClient(self):
        self.client = InfluxDBClient(
            url=INFLUX_URL,
            token=INFLUX_TOKEN,
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

    def write(self,measurement,key,value,tags):
        if not self.api:
            self.openClient()
            
        p = Point(measurement)
        for t,v in tags.items():
            p.tag(t,v)
            
        p.field(key,value)
        #print(p)
        
        try:
            self.api.write(bucket=INFLUX_BUCKET, record = p)

        except:
            self.reset()
            