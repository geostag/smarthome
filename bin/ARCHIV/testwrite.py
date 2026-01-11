from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

client = InfluxDBClient(
    url="http://localhost:8086",
    token="--replace-token--",
    org="smarthome"
)

write_api = client.write_api(write_options=SYNCHRONOUS)

point = (
    Point("climate")
    .tag("room", "wohnzimmer")
    .field("temperature", 22.7)
)

write_api.write(bucket="smarthome", record=point)
client.close()

