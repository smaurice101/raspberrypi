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

default_args = {
  'mqtt_broker' : 'b526253c5560459da5337e561c142369.s1.eu.hivemq.cloud', # <<<****** Enter MQTT broker i.e. test.mosquitto.org
  'mqtt_port' : '8883', # <<<******** Enter MQTT port i.e. 1883    
  'mqtt_subscribe_topic' : 'tml/cybersecurity', # <<<******** enter name of MQTT to subscribe to i.e. encyclopedia/#
  'mqtt_enabletls' : '1', # << Enable TLS if connecting to a cloud cluster like HiveMQ
}

##############################################################
# global variable:
# 1. hackedips (subnet-[i or d],hostid): 5.11,6.12,5.21, i=increase,d=decrease
# 2. dynamically turn off ports on machine - students should detect which machine cannot be pinged - meaning it is down

lastinboundpacketi=0
lastoutboundpacketi=0

lastinboundpacketd=1000000
lastoutboundpacketd=1000000

##################################################  MQTT SERVER #####################################
# This is a MQTT server that will handle connections from a client.  It will handle connections
# from an MQTT client for on_message, on_connect, and on_subscribe

######################################## USER CHOOSEN PARAMETERS ########################################

def mqttconnection():
     username="<enter username>"
     password="<enter password>"

     client = paho.Client(paho.CallbackAPIVersion.VERSION2)
     mqttBroker = default_args['mqtt_broker'] 
     mqttport = int(default_args['mqtt_port'])
     client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
     client.username_pw_set(username, password)     
     client.connect(mqttBroker,mqttport)

     client.subscribe(default_args['mqtt_subscribe_topic'], qos=1)
     return client

def publishtomqttbroker(client,line):
     print(line)
     client.publish(topic=default_args['mqtt_subscribe_topic'], payload=line, qos=1, retain=False)
     client.loop()
     
def formatdataandstream(mainjson,hackedid,client,noping):
     global lastinboundpacketi,lastoutboundpacketi,lastinboundpacketd,lastoutboundpacketd

     harr = hackedid.split(",")
     if noping == '':
       nopingarr = []
     else:  
       nopingarr = noping.split(",")
          
     jbuf = json.loads(mainjson)
     
     inside=0
     for h in harr:
       hidarr = h.split("-")
       print(hidarr[0],jbuf["hostName"])
       if jbuf["hostName"] == hidarr[0]: # hacked machines
         print("host=name=",h)  
         inside=1    
         vali=random.randint(5096,10000)
         valo=random.randint(5096,10000)
         if jbuf["pingStatus"] == "FAILURE":              
            jbuf["inboundpackets"]=0
            jbuf["outboundpackets"]=0
         elif hidarr[1]=="i":
            lastinboundpacketi=lastinboundpacketi + vali
            lastoutboundpacketi=lastoutboundpacketi + valo                  
            jbuf["inboundpackets"]=lastinboundpacketi
            jbuf["outboundpackets"]=lastoutboundpacketi
            if lastinboundpacketi > 1000000000:
                lastinboundpacketi=0 
            if lastoutboundpacketi > 1000000000:
                lastoutboundpacketi=0 
         else:
            vali=random.randint(10,1000)
            valo=random.randint(10,1000)
            lastinboundpacketd=lastinboundpacketd - vali
            lastoutboundpacketd=lastoutboundpacketd - valo
            if lastinboundpacketd <= 0:
                  lastinboundpacketd=1000000
            if lastoutboundpacketd <= 0:
                  lastoutboundpacketd=1000000

            jbuf["inboundpackets"]=lastinboundpacketd
            jbuf["outboundpackets"]=lastoutboundpacketd

       if len(nopingarr) > 0: 
          if jbuf["hostName"] in nopingarr:
            jbuf["pingStatus"] = "FAILURE"
            jbuf["inboundpackets"]=0
            jbuf["outboundpackets"]=0
       else:
            jbuf["pingStatus"] = "SUCCESS"
              
     if inside==0: # normal machines  
         vali=random.randint(64,524)
         valo=random.randint(64,524)
         if jbuf["pingStatus"] == "FAILURE":
            jbuf["inboundpackets"]=0
            jbuf["outboundpackets"]=0
         else:
            jbuf["inboundpackets"]=vali
            jbuf["outboundpackets"]=valo

     jbuf = json.dumps(jbuf)              
     jbuf='"'.join(jbuf.split("'"))
#      writedata(jbuf)

     ############################### Stream to MQTT BROKER HIVEMQ
     publishtomqttbroker(client,jbuf)
      
###################################################### END TML PROCESS #######################################


###################################################### START MAIN PROCESS #######################################

if __name__ == '__main__':
    hackedid=""
    noping=""
    print(sys.argv)
    if len(sys.argv) > 1:
        hackedid = sys.argv[1]
        noping = sys.argv[2]
    if hackedid == "": 
      hackedid="6.25-i,6.26-i,6.101-i"
      noping=""

    # Connect to MQTT broker:
    client=mqttconnection()

    if client:
        
        inputfile='cisco_network_data.txt'

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
        #    senddata(line,producerid,maintopic)
            formatdataandstream(line,hackedid,client,noping)
            time.sleep(.1)
         
           except Exception as e:
              print("Warn:",e)
              pass
          
           time.sleep(.1)

        file1.close()

