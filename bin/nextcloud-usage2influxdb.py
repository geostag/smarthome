from xml.etree import ElementTree
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from zoneinfo import ZoneInfo
from datetime import datetime, timezone
import requests, os

INFLUX_URL   = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN_LONGRANGE")
INFLUX_ORG   = os.getenv("INFLUX_ORG")

NEXTCLOUD_URL = os.getenv("NEXTCLOUD_URL")
ADMIN_USER    = os.getenv("NEXTCLOUD_USER")
APP_PASSWORD  = os.getenv("NEXTCLOUD_APITOKEN")

# Liste aller Benutzer abrufen
r_users = requests.get(
    f"{NEXTCLOUD_URL}/ocs/v1.php/cloud/users",
    auth=(ADMIN_USER, APP_PASSWORD),
    headers={"OCS-APIRequest": "true"}
)
r_users.raise_for_status()
tree = ElementTree.fromstring(r_users.content)
user_list = [u.text for u in tree.findall(".//users/element")]

client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)
write_api = client.write_api(write_options=SYNCHRONOUS)

dt = datetime.now()
dt = dt.replace(tzinfo=ZoneInfo("Europe/Berlin"))
dt = dt.replace(hour=0,minute=0, second=0, microsecond=0)

for user in user_list:
    r = requests.get(
        f"{NEXTCLOUD_URL}/ocs/v1.php/cloud/users/{user}",
        auth=(ADMIN_USER, APP_PASSWORD),
        headers={"OCS-APIRequest": "true"}
    )
    tree = ElementTree.fromstring(r.content)
    used = tree.find(".//quota/used").text
    total = tree.find(".//quota/total").text
    #print(f"{user}: {int(used)/(1024**3):.2f} GB used of {int(total)/(1024**3):.2f} GB")
    
    p = (Point("nextcloud").tag("domain","storage").tag("user",user).field("used",int(used)).time(dt,WritePrecision.NS))
    write_api.write(bucket="longrange", record=p)
