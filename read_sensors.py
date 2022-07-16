#!/usr/bin/python3
import time
import sys
import os
import socket
import paho.mqtt.client as mqtt

MQTT_HOST=os.getenv('MQTT_HOST','127.0.0.1')
MQTT_PORT=int(os.getenv('MQTT_PORT',1883))
MQTT_TIMEOUT=int(os.getenv('MQTT_TIMEOUT',60))
MQTT_MAIN_TOPIC=os.getenv('MQTT_MAIN_TOPIC','sensors')

DEBUG = False

def wr(msg):
    if DEBUG:
        f = open("/tmp/test.log","a")
        f.write(msg)
        f.close()

def on_connect(client, userdata, flags, rc):
    mqttc.subscribe(""+MQTT_MAIN_TOPIC+"/#")
    wr("Subscribed to " + ""+MQTT_MAIN_TOPIC+"/#\n")

def on_disconnect(client, userdata, tc):
    wr("Stopping MQTT loop\n")
    mqttc.loop_stop()

def on_message(client, userdata, msg):
    wr("Received message from MQTT " + msg.payload.decode("utf-8") + "\n")
    try:
         conn.sendall(bytes(msg.payload.decode("utf-8")+"\n",'utf-8'))
    except:
         mqttc.disconnect()

wr("Starting\n")

if __name__ == '__main__':
    global server
    server = socket.fromfd(sys.stdin.fileno(), family=socket.AF_UNIX, type=socket.SOCK_STREAM, proto=0)
    mqttc = mqtt.Client()
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.on_disconnect = on_disconnect

    while 1:
        global conn
        conn, addr = server.accept()
        wr("STDIN Accepted. Trying to connect to MQTT\n")
        try:
            mqttc.connect(MQTT_HOST, MQTT_PORT, MQTT_TIMEOUT)
            wr("Starting MQTT loop\n")
            mqttc.loop_forever()
        except:
            try:
                wr("MQTT is not available\n")
                conn.sendall(b'{"Error": "MQTT is not available"}\n')
            except:
                conn.close()
                conn = None
        else:
            try:
                wr("MQTT connection closed\n")
                conn.sendall(b'{"Error": "MQTT connectionclosed"}\n')
            except:
                wr("Error sending to STDIN\n")
                conn.close()
                conn = None
            
        wr("End of loop. Now sleep 1 sec\n")
        time.sleep(1)
