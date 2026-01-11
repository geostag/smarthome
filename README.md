# my own smarthome scripts and setup

## whats the purpose?

I want to have an overview over all of my smarthome devices. I don't like HA, because there is so much fiddling around
to get things up and running - it leaves me with a feeling of "this might brake unforseen and I will have to fddle around again".
I prefer a stable, to-the-point-I-want-it setup.

AI suggested to use a combination of inflixDB and grafana. And I added some scripts to query sensors.

## architecture

- influxDB and grafana are run as docker containers, storing the collected and configured data in a bind mounted directory
- an MQTT broker is queried for the smart grid-meter
- the rest of the data is collected by sensorrs doing queries against REST APIs
- data is stored in an influxDB bucket called "smarthome"
- derived data is created by influxDB tasks and stored in an influxDB bucket called "smarthomederived"
- visualizations are done in grafana dashbaords

## setup

1. create your own env.sh from env.sh.template
2. run the setup tool: `bin/setup-once.sh`
3. start servers: `start-servers.sh`
4. start sensors: `start-sensors.sh`

 
