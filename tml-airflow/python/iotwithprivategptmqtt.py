# Developed by Sebastian Maurice
# Date: Sept 2023

import requests
import json
import os
import random
import paho.mqtt.client as paho
from paho import mqtt
import time
import sys
from datetime import datetime
import maadstml

default_args = {
  'mqtt_broker' : '', # <<<****** Enter MQTT broker i.e. test.mosquitto.org
  'mqtt_port' : '8883', # <<<******** Enter MQTT port i.e. 1883    
  'mqtt_subscribe_topic' : 'tml/iot', # <<<******** enter name of MQTT to subscribe to i.e. encyclopedia/#
  'mqtt_enabletls' : '1', # << Enable TLS if connecting to a cloud cluster like HiveMQ
}


##################################################  MQTT SERVER #####################################
# This is a MQTT server that will handle connections from a client.  It will handle connections
# from an MQTT client for on_message, on_connect, and on_subscribe

######################################## USER CHOOSEN PARAMETERS ########################################

def mqttconnection():
     username="" # <<<<< Enter username
     password="" # <<<<< Enter password

     client = paho.Client(paho.CallbackAPIVersion.VERSION2)
     
     mqttBroker = default_args['mqtt_broker'] 
     mqttport = int(default_args['mqtt_port'])
     client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
     client.username_pw_set(username, password)     
     client.connect(mqttBroker,mqttport)

     b=client.subscribe(default_args['mqtt_subscribe_topic'], qos=1)
     if 'MQTT_ERR_SUCCESS' in str(b):
       return client
     else:
       return NULL   

def publishtomqttbroker(client,line):
     try:
      b=client.publish(topic=default_args['mqtt_subscribe_topic'], payload=line, qos=1, retain=False)
      if 'MQTT_ERR_SUCCESS' in str(b):
        print(line)
        client.loop()
      else:
        print("ERROR Making a connection to HiveMQ:",b)
   
     except Exception as e:
       print(e)
       
###################################################### START MAIN PROCESS #######################################

if __name__ == '__main__':

    # Connect to MQTT broker:
    try:
     client=mqttconnection()
    except Exception as e:
     print("Cannot connect")    

    if client:
        
        inputfile='C:/MAADS/tml-airflow/myawesometmlsolutionml-mqtt/IoTData.txt'

        file1 = open(inputfile, 'r')
        print("Read Start:",datetime.now())
        
        while True:
           line = file1.readline()
           try:
            if not line or line == "":
                #break
               file1.seek(0)
               print("Reached End of File - Restarting")
               print("Read End:",datetime.now())
               continue
            publishtomqttbroker(client,line)

            time.sleep(.1)
         
           except Exception as e:
              print("Warn:",e)
              pass
          
           time.sleep(.1)

        file1.close()


