#!/usr/bin/python3

""" Some documentation string"""

from bluepy.btle import Scanner, DefaultDelegate, ScanEntry
#from bluepy.btle import *
import os
import time
import struct
import paho.mqtt.client as mqtt
import json
import os
import re
import binascii
from binascii import unhexlify

BLE_DEVICE=int(os.getenv('BLE_DEVICE',0))
SCAN_TIME=float(os.getenv('SCAN_TIME',7.0))
SLEEP_TIME=float(os.getenv('SLEEP_TIME',30.0))
MQTT_HOST=os.getenv('MQTT_HOST','127.0.0.1')
MQTT_PORT=int(os.getenv('MQTT_PORT',1883))
MQTT_TIMEOUT=int(os.getenv('MQTT_TIMEOUT',60))
MQTT_MAIN_TOPIC=os.getenv('MQTT_MAIN_TOPIC','sensors')

esp_sensor_scan_entry=None

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
#            print ("Discovered device", dev.addr)
            jsObj = {}
            if (bool(re.match('F5:29:6B',str(dev.addr),re.I))): #This is nRF51 HTS221 sensor
                print(f"Sensor nRF51 HTS221 found at {dev.addr}")
                raw = dev.getValueText(255)
                print ("Manufacturer data - 16-bit value: ",raw)
                if raw[0:4] == 'ffff':
                    if raw[4:6] == '2b' or raw[4:6] == '2d':
                        #raw_str = bytes.fromhex(raw[4:].decode("ascii")).decode("ascii")
                        raw_str = bytearray.fromhex(raw[4:]).decode()
                        print ("RAW_STR = ", raw_str)
                        data_list = raw_str.split()
                        temp = data_list[0]
                        hum = data_list[1]
                        batp = data_list[2]
                        batv = data_list[3]
                        mode = data_list[4]

                    if raw[4:6] == 'ee':
                        temp = int(raw[6:10],16)
                        if temp & 1 << 15: temp -= 1 << 16
                        temp = temp / 10
                        hum = int(raw[10:14],16)
                        hum = hum / 10
                        batp = int(raw[14:16],16)
                        batv = int(raw[16:20],16)
                        batv = batv / 1000
                        mode = int(raw[20:22],16)

                    if raw[4:6] == '2b' or raw[4:6] == '2d' or raw[4:6] == 'ee':
                        jsObj['DeviceName'] = "nRF51 HTS221"
                        jsObj['DeviceAddr'] = str(dev.addr)
                        print ("Temperature = ", temp)
                        topic = MQTT_MAIN_TOPIC + '/' + jsObj['DeviceAddr'] 
                        jsObj['Temperature']=round(float(temp),1)
                        jsObj['Humidity']=round(float(hum),1)
                        jsObj['BatteryP']=round(float(batp),0)
                        jsObj['BatteryV']=round(float(batv),3)
                        jsObj['UpdateInterval']=round(float(mode),0)
                        jsonStr = json.dumps(jsObj)
                        print(jsonStr) 
                        mqttc.publish(topic,jsonStr, qos=1, retain=True)

            if (bool(re.match('58:2D:34',str(dev.addr),re.I))): #This is Xiaomi Clear Glass sensor
                print(f"Sensor Qingping found at {dev.addr}")
                raw = dev.getValueText(22)
                print ("Service Data - 16-bit value: ",raw)
                if raw[0:4] == 'cdfd':
                    jsObj['DeviceName'] = "Xiaomi CGG1"
                    jsObj['DeviceAddr'] = str(dev.addr)
                    jsObj['Temperature'] = 0.0
                    jsObj['Humidity'] = 0.0
                    jsObj['BatteryP'] = 0
                    topic = MQTT_MAIN_TOPIC + '/' + jsObj['DeviceAddr'] 
                    if raw[22:24] == '04': #Temp + humidity 2 + 2 bytes
                        temp = int(raw[26:28]+raw[24:26],16)/10
                        humidity = int(raw[30:32]+raw[28:30],16)/10
                        jsObj['Temperature']=round(temp,2)
                        jsObj['Humidity']=round(humidity,2)
                    if raw[32:34] == '02': #battery 1 byte
                        battery = int(raw[36:38],16)
                        jsObj['BatteryP']=battery
                    jsonStr = json.dumps(jsObj)
                    print(jsonStr) 
                    mqttc.publish(topic,jsonStr, qos=1, retain=True)                                          
        elif isNewData:
            if (bool(re.match('58:2D:34',str(dev.addr),re.I))):
                print ("Received new data from Qingping sensor", dev.addr)
#                print ("Service Data - 16-bit value:", dev.getValueText(22))

print(f"Using the hci"+str(BLE_DEVICE)+" device")            
        
os.system('hciconfig hci'+str(BLE_DEVICE)+' down')
os.system('hciconfig hci'+str(BLE_DEVICE)+' up')

print(f"Connecting to MQTT broker {MQTT_HOST}:{MQTT_PORT}")
mqttc = mqtt.Client(clean_session=True)
mqttc.connect(MQTT_HOST, MQTT_PORT, MQTT_TIMEOUT)
mqttc.loop_start()

scanner = Scanner(BLE_DEVICE).withDelegate(ScanDelegate())
while True:
    print("New scan cycle")
    try:
        devices = scanner.scan(SCAN_TIME)
    except BTLEException as e:
        print("Error while scanning for BLE devices")
    print("Sleeping for {} seconds.".format(SLEEP_TIME))
    time.sleep(SLEEP_TIME)
