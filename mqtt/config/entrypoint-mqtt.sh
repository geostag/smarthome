#!/bin/sh

PWFILE=/mosquitto/pwfile

touch $PWFILE
chown mosquitto:mosquitto $PWFILE
chmod 600 $PWFILE

mosquitto_passwd -b $PWFILE "$MQTT_USERNAME" "$MQTT_PASSWORD"

exec mosquitto -c /mosquitto/config/mosquitto.conf
