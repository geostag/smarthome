zendure

```
import requests
sn = '--replace-serial-number--'
url = 'https://app.zendure.tech/eu/developer/api/apply'
account = '--replace-youremail--'
data = {
    'snNumber': sn,
    'account': account
    }
r = requests.post(url,json = data)
print(r.text)


{"code":200,"success":true,"data":{"appKey":"--your-appkey--","secret":"--your-secret--","mqttUrl":"mqtt-eu.zen-iot.com","port":1883},"msg":"Successful operation"}


https://github.com/Zendure/zenSDK/blob/main/README.md

# enable loca mqtt and send to local mqtt broker
sudo mosquitto_password -b /etc/mosquittopw zendureuser zendurepassword
sudo /etc/init.d/mosquitto reload
curl -X POST -H "Content-Type: application/json" http://--replace-zendure-hostname--/rpc -d '{"sn":"--replace-serial-number--", "method": "HA.Mqtt.SetConfig", "params": { "config": { "enable": true, "server": "--reaplce-local-mqttserver--", "port": 1883, "protocol": "mqtt", "username": "zendurepassword", "password": "zendurepassword" }}}'

mosquitto_sub -v -h nextcloudpi.fritz.box -u zendure -P zendure -t 'Zendure/#'



Zendure/sensor/CO4EHNCDN247220/CO4EHNCDN247220_softVersion 1.0.21
Zendure/sensor/CO4EHNCDN247220/CO4EHNCDN247220_minVol 3.11
Zendure/sensor/CO4EHNCDN247220/CO4EHNCDN247220_maxVol 3.13
Zendure/sensor/CO4EHNCDN247220/CO4EHNCDN247220_batcur 0.9
Zendure/sensor/CO4EHNCDN247220/CO4EHNCDN247220_totalVol 46.90
Zendure/sensor/CO4EHNCDN247220/CO4EHNCDN247220_maxTemp 20.0
Zendure/sensor/CO4EHNCDN247220/CO4EHNCDN247220_power 42
Zendure/sensor/CO4EHNCDN247220/CO4EHNCDN247220_state charging
Zendure/sensor/CO4EHNCDN247220/CO4EHNCDN247220_socLevel 11
Zendure/sensor/EOA1NHN3N246446/heatState not_heating
Zendure/sensor/EOA1NHN3N246446/packInputPower 0
Zendure/sensor/EOA1NHN3N246446/outputPackPower 40
Zendure/sensor/EOA1NHN3N246446/outputHomePower 0
Zendure/sensor/EOA1NHN3N246446/remainOutTime 400
Zendure/sensor/EOA1NHN3N246446/packState charging
Zendure/sensor/EOA1NHN3N246446/packNum 1
Zendure/sensor/EOA1NHN3N246446/electricLevel 11
Zendure/sensor/EOA1NHN3N246446/gridInputPower 0
Zendure/sensor/EOA1NHN3N246446/solarInputPower 40
Zendure/sensor/EOA1NHN3N246446/solarPower1 20
Zendure/sensor/EOA1NHN3N246446/solarPower2 0
Zendure/sensor/EOA1NHN3N246446/solarPower3 20
Zendure/sensor/EOA1NHN3N246446/solarPower4 0
Zendure/sensor/EOA1NHN3N246446/pass no
Zendure/sensor/EOA1NHN3N246446/reverseState no
Zendure/sensor/EOA1NHN3N246446/socStatus idle
Zendure/sensor/EOA1NHN3N246446/hyperTmp 25.0
Zendure/sensor/EOA1NHN3N246446/gridOffPower 0
Zendure/switch/EOA1NHN3N246446/lampSwitch ON
Zendure/select/EOA1NHN3N246446/acMode Output mode
Zendure/select/EOA1NHN3N246446/gridReverse Disallow backflow
Zendure/select/EOA1NHN3N246446/gridOffMode OFF
Zendure/number/EOA1NHN3N246446/socSet 100
Zendure/number/EOA1NHN3N246446/minSoc 10
Zendure/number/EOA1NHN3N246446/inverseMaxPower 800
Zendure/number/EOA1NHN3N246446/outputLimit 0
Zendure/number/EOA1NHN3N246446/inputLimit 0


curl http://--replace-zendurehostname--/properties/report
{
   "timestamp":1767039133,
   "messageId":4,
   "sn":"--serial-number--",
   "version":2,
   "product":"solarFlow800Pro",
   "properties":{
      "heatState":0,
      "packInputPower":0,
      "outputPackPower":0,
      "outputHomePower":0,
      "remainOutTime":59940,
      "packState":0,
      "electricLevel":10,
      "gridInputPower":0,
      "solarInputPower":0,
      "solarPower1":0,
      "solarPower2":0,
      "solarPower3":0,
      "solarPower4":0,
      "pass":0,
      "reverseState":0,
      "socStatus":0,
      "hyperTmp":2891,
      "gridOffPower":0,
      "dcStatus":0,
      "pvStatus":1,
      "acStatus":0,
      "dataReady":1,
      "gridState":1,
      "BatVolt":4461,
      "socLimit":2,
      "writeRsp":0,
      "acMode":2,
      "inputLimit":0,
      "outputLimit":0,
      "socSet":1000,
      "minSoc":100,
      "gridStandard":0,
      "gridReverse":2,
      "inverseMaxPower":800,
      "lampSwitch":1,
      "gridOffMode":2,
      "IOTState":2,
      "Fanmode":1,
      "Fanspeed":0,
      "bindstate":0,
      "factoryModeState":0,
      "OTAState":0,
      "LCNState":0,
      "oldMode":0,
      "VoltWakeup":0,
      "ts":1767038412,
      "tsZone":13,
      "smartMode":0,
      "chargeMaxLimit":1000,
      "packNum":1,
      "rssi":-31,
      "is_error":0
   },
   "packData":[
      {
         "sn":"--serial-number--",
         "packType":300,
         "socLevel":10,
         "state":0,
         "power":0,
         "maxTemp":2881,
         "totalVol":4450,
         "batcur":0,
         "maxVol":297,
         "minVol":294,
         "softVersion":4117
      }
   }
}
```