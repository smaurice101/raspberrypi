import paho.mqtt.client as paho
from paho import mqtt
import sys
import maadstml
#import tsslogging
import os
import subprocess
import time
import random
from datetime import datetime

default_args = {
  'mqtt_broker' : 'test.mosquitto.org', # <<<****** Enter MQTT broker i.e. test.mosquitto.org
  'mqtt_port' : '1883', # <<<******** Enter MQTT port i.e. 1883    
  'mqtt_subscribe_topic' : 'tmliot/#', # <<<******** enter name of MQTT to subscribe to i.e. encyclopedia/#  
}

sys.dont_write_bytecode = True
##################################################  MQTT SERVER #####################################
# This is a MQTT server that will handle connections from a client.  It will handle connections
# from an MQTT client for on_message, on_connect, and on_subscribe

######################################## USER CHOOSEN PARAMETERS ########################################


def mqttconnection():
     client = paho.Client(paho.CallbackAPIVersion.VERSION2)
     mqttBroker = default_args['mqtt_broker'] 
     mqttport = int(default_args['mqtt_port'])
     client.connect(mqttBroker,mqttport)

     client.subscribe(default_args['mqtt_subscribe_topic'], qos=1)
     return client

def publishtomqttbroker(client,line):

     client.publish(topic="tml/", payload=line, qos=1, retain=False)

def readdatafile(client,inputfile):

  ##############################################################
  # NOTE: You can send any "EXTERNAL" data through this API
  # It is reading a localfile as an example
  ############################################################
  
  try:
    file1 = open(inputfile, 'r')
    print("Data Producing to Kafka Started:",datetime.now())
  except Exception as e:
    print("ERROR: Something went wrong ",e)  
    return
  k = 0
  while True:
    line = file1.readline()
    line = line.replace(";", " ")
    print("line=",line)
    # add lat/long/identifier
    k = k + 1
    try:
      if line == "":
        #break
        file1.seek(0)
        k=0
        print("Reached End of File - Restarting")
        print("Read End:",datetime.now())
        continue
      ret = publishtomqttbroker(client,line)
      print(ret)
      # change time to speed up or slow down data   
      time.sleep(.5)
    except Exception as e:
      print(e)
      time.sleep(.5)
      pass

client=mqttconnection()
inputfile = "IoTDatasample.txt"
readdatafile(client,inputfile)
