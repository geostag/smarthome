from xml.etree import ElementTree
from zoneinfo import ZoneInfo
from datetime import datetime, timezone
from lib.toinflux import Iflx
import requests, os

NEXTCLOUD_URL = os.getenv("NEXTCLOUD_URL")
ADMIN_USER    = os.getenv("NEXTCLOUD_USER")
APP_PASSWORD  = os.getenv("NEXTCLOUD_APITOKEN")
TOKEN         = os.getenv("INFLUX_TOKEN_LONGRANGE")


# Liste aller Benutzer abrufen
r_users = requests.get(
    f"{NEXTCLOUD_URL}/ocs/v1.php/cloud/users",
    auth=(ADMIN_USER, APP_PASSWORD),
    headers={"OCS-APIRequest": "true"}
)
r_users.raise_for_status()
tree = ElementTree.fromstring(r_users.content)
user_list = [u.text for u in tree.findall(".//users/element")]

dt = datetime.now()
dt = dt.replace(tzinfo=ZoneInfo("Europe/Berlin"))
dt = dt.replace(hour=0,minute=0, second=0, microsecond=0)

INFLUX = Iflx(bucket="longrange",token=TOKEN)

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
    
    INFLUX.write("nextcloud","used",int(used),{"domain": "storage", "user": user},dt)
