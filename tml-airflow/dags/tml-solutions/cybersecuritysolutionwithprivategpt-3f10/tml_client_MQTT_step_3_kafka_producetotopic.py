import paho.mqtt.client as paho
from paho import mqtt
import sys
import maadstml
import os
import subprocess
import time
import random
from datetime import datetime

default_args = {
  'mqtt_broker' : 'test.mosquitto.org', # <<<****** Enter MQTT broker i.e. test.mosquitto.org or HiveMQ cluster
  'mqtt_port' : '1883', # <<<******** Enter MQTT port i.e. 1883    
  'mqtt_subscribe_topic' : 'tml/iot', # <<<******** enter name of MQTT to subscribe to i.e. encyclopedia/#  
  'mqtt_enabletls' : '0'
}

sys.dont_write_bytecode = True
##################################################  MQTT SERVER #####################################
# This is a MQTT server that will handle connections from a client.  It will handle connections
# from an MQTT client for on_message, on_connect, and on_subscribe

# If Connecting to HiveMQ cluster you will need USERNAME/PASSWORD and mqtt_enabletls = 1
# USERNAME/PASSWORD should be set in your DOCKER RUN command of the TSS container

######################################## USER CHOOSEN PARAMETERS ########################################


def mqttconnection():
     username = ""    
     password = ""   
     if 'MQTTUSERNAME' in os.environ:
       username = os.environ['MQTTUSERNAME']  
     if 'MQTTPASSWORD' in os.environ:
       password = os.environ['MQTTPASSWORD']  
        
     client = paho.Client(paho.CallbackAPIVersion.VERSION2)
     mqttBroker = default_args['mqtt_broker'] 
     mqttport = int(default_args['mqtt_port'])
     if default_args['mqtt_enabletls'] == "1":
        client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
        client.username_pw_set(username, password)     

     client.connect(mqttBroker,mqttport)

     client.subscribe(default_args['mqtt_subscribe_topic'], qos=1)
     return client

def publishtomqttbroker(client,line):

     client.publish(topic=default_args['mqtt_subscribe_topic'], payload=line, qos=1, retain=False)
     client.loop()

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
