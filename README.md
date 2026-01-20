# my own smarthome scripts and setup

## purpose?

I want to have an overview over all of my smarthome devices. I don't like HA, because there is so much fiddling around
to get things up and running - it leaves me with a feeling of "this might brake unforseen and I will have to fiddle around again".
I prefer a stable, to-the-point-I-want-it setup. 

In addition I control my solar battery pack with an agent.

AI suggested to use a combination of influxDB and grafana. And I added some scripts to query sensors.

## list of sensors

- Fritz Box
   - status of devices (online?)
   - network throughput
   - smarthome devices
- Tasmota smart meter sensor
   - read grid meter
- myStrom switches
   - power 
   - temperature
- Zendure Powerflow
   - electric properties like solar panel power, battery charging, power delivered, ... 
- Smartthings sensors
   - temperature and humidity sensors
- weather.com
   - climate data of a destinct location

## architecture

- influxDB and grafana are run as docker containers, storing the collected and configured data in corresponding bind mounted directories
- an MQTT broker 
   - to collect smart meter data (tasmota sends data by MQTT) and send it over to influxdb
   - to collect recent data for an agent to control the solar output power
- further data is collected by sensors doing queries against REST APIs
- all collected data is forwarded to an influxDB bucket called "smarthome"
- derived data is created by influxDB tasks and stored in an influxDB bucket called "smarthomederived"
- visualizations are done in grafana dashboards

## setup

1. `cp env.sh.template env.sh`
2. adjust env.sh
3. run the setup tool once: `bin/setup-once.sh`
4. start servers: `start-servers.sh`
5. start sensors: `start-sensors.sh`
6. add tasks in influxdb by importing from files in doc/influx-tasks
7. add dashboards in grafana by importing from files in doc/grafana-dashboards

## result

![screenshot of a dashboard](/doc/screenshot.png "screenshot")


