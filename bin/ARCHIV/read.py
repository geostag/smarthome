from influxdb_client import InfluxDBClient
import os

# Konfiguration
url    = os.getenv("INFLUX_URL")
token  = os.getenv("INFLUX_TOKEN")
token = '3FyT8Zn5MgH16K_2dwOX1SntmPsrTZ_wa_kydBrSGWiLdgneM7dgfosvduGRanE2Eb4tUqn7z9WeMCREpRU3Hw=='
org    = os.getenv("INFLUX_ORG")
bucket = os.getenv("INFLUX_BUCKET")

# Client erstellen
client = InfluxDBClient(
    url=url,
    token=token,
    org=org
)

query_api = client.query_api()

# Flux-Abfrage
query = f'''
from(bucket: "{bucket}")
  |> range(start: -8d)
  |> filter(fn: (r) => r._field == "hyperTmpD")
'''

print(query)

# Query ausführen
tables = query_api.query(query)

# Ergebnisse auslesen
for table in tables:
    for record in table.records:
        print(
            record.get_time(),
            record.get_measurement(),
            record.get_field(),
            record.get_value()
        )

client.close()

