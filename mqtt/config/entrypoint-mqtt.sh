#!/bin/sh

PWFILE=/mosquitto/pwfile

touch $PWFILE
chown mosquitto:mosquitto $PWFILE
chmod 600 $PWFILE

mosquitto_passwd -b $PWFILE "$SENSORS_MQTT_USERNAME" "$SENSORS_MQTT_PASSWORD"

exec mosquitto -c /mosquitto/config/mosquitto.conf
