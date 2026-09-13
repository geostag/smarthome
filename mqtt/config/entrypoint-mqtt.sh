#!/bin/sh

PWFILE=/mosquitto/pwfile
echo ">> $SENSORS_MQTT_USERNAME // $SENSORS_MQTT_PASSWORD <<"

rm $PWFILE
touch $PWFILE
mosquitto_passwd -b $PWFILE "$SENSORS_MQTT_USERNAME" "$SENSORS_MQTT_PASSWORD"

chown mosquitto:mosquitto $PWFILE
chmod 600 $PWFILE

exec mosquitto -c /mosquitto/config/mosquitto.conf
