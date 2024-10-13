import paho.mqtt.client as paho
from paho import mqtt
import time
import sys
from datetime import datetime

default_args = {
  'mqtt_broker' : 'b526253c5560459da5337e561c142369.s1.eu.hivemq.cloud', # <<<****** Enter MQTT broker i.e. test.mosquitto.org
  'mqtt_port' : '8883', # <<<******** Enter MQTT port i.e. 1883    
  'mqtt_subscribe_topic' : 'tml/iot', # <<<******** enter name of MQTT to subscribe to i.e. encyclopedia/#
  'mqtt_enabletls' : '1', # << Enable TLS if connecting to a cloud cluster like HiveMQ
}


sys.dont_write_bytecode = True
##################################################  MQTT SERVER #####################################
# This is a MQTT server that will handle connections from a client.  It will handle connections
# from an MQTT client for on_message, on_connect, and on_subscribe

######################################## USER CHOOSEN PARAMETERS ########################################


def mqttconnection():
     username="<Enter MQTT username>"
     password="<Enter MQTT password>"

     client = paho.Client(paho.CallbackAPIVersion.VERSION2)
     mqttBroker = default_args['mqtt_broker'] 
     mqttport = int(default_args['mqtt_port'])
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
      publishtomqttbroker(client,line)
      # change time to speed up or slow down data   
      time.sleep(.15)
    except Exception as e:
      print(e)
      time.sleep(.15)
      pass

client=mqttconnection()
inputfile = "IoTDatasample.txt"
readdatafile(client,inputfile)
