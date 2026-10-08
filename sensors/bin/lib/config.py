from dynaconf import Dynaconf
from pathlib import Path
import json, hashlib, os

settings = Dynaconf(
    settings_files=['/app/sensors-config-default.toml','/app/sensors-config.toml'],
    #settings_files=['sensors/sensors-config-default.toml','./sensors-config.toml'],
    envvar_prefix="SENSORS",
    merge_enabled=True
)

# check and update config-hash
hash_old = ""
file = Path(f"{settings.secret_dir}/config-hash")
if file.is_file() and os.access(file, os.R_OK):
    with open(f"{settings.secret_dir}/config-hash", "r") as f:
        hash_old = f.read()

allconfig = settings.to_dict()
serialized = json.dumps(allconfig,sort_keys=True,separators=(",", ":"),default=str,)
hash = hashlib.sha256(serialized.encode('utf-8')).hexdigest()
if hash != hash_old:
    with open(f"{settings.secret_dir}/config-hash", "w") as f:
        f.write(hash)

    with open(f"{settings.secret_dir}/env-mqtt.sh", "w") as f:
        f.write(f"USERNAME='{settings.MQTT_USERNAME}'\n")
        f.write(f"PASSWORD='{settings.MQTT_PASSWORD}'\n")

    with open(f"{settings.secret_dir}/env-influxdb.sh", "w") as f:
        f.write(f"INFLUX_ORG='{settings.influx.org}'\n")
        f.write(f"INFLUX_BUCKET='{settings.influx.bucket}'\n")
        f.write(f"INFLUX_RETENTION='{settings.influx.retention}'\n")
        f.write(f"INFLUX_DERIVED_BUCKET='{settings.influx.derived_bucket}'\n")
        f.write(f"INFLUX_DERIVED_RETENTION='{settings.influx.derived_retention}'\n")
        f.write(f"INFLUX_LONGRANGE_BUCKET='{settings.influx.longrange_bucket}'\n")
        f.write(f"INFLUX_LONGRANGE_RETENTION='{settings.influx.longrange_retention}'\n")
        f.write(f"INFLUX_URL='{settings.influx.url}'\n")

    with open(f"{settings.secret_dir}/env-grafana.sh", "w") as f:
        f.write(f"USERID='{settings.grafana.userid}'\n")

    print("ATTENTION >>> update configs - restart all containers <<<")

