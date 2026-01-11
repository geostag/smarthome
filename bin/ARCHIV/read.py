from influxdb_client import InfluxDBClient

# Konfiguration
url = "http://nextcloudpi:8086"
token = "token"
org = "smarthome"
bucket = "smarthomederived"

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
  |> filter(fn: (r) => r._measurement == "daily_energy")
'''

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

