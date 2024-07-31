# Developed by: Sebastian Maurice, PhD
# Date: 2023-05-18 
# Toronto, Ontario Canada

# TML python library
import maadstml

# Uncomment IF using Jupyter notebook 
import nest_asyncio

import json
import random
import sys
import pandas as pd
import asyncio
import datetime
import time
import os

# Uncomment IF using Jupyter notebook
nest_asyncio.apply()

basedir = os.environ['userbasedir'] 

# Set Global Host/Port for VIPER - You may change this to fit your configuration
VIPERHOST=''
VIPERPORT=''
HTTPADDR='https://'


#############################################################################################################
#                                      STORE VIPER TOKEN
# Get the VIPERTOKEN from the file admin.tok - change folder location to admin.tok
# to your location of admin.tok
def getparams():
     global VIPERHOST, VIPERPORT, HTTPADDR
     with open(basedir + "/Viper-preprocess2/admin.tok", "r") as f:
        VIPERTOKEN=f.read()

     if VIPERHOST=="":
        with open(basedir + '/Viper-preprocess2/viper.txt', 'r') as f:
          output = f.read()
          VIPERHOST = HTTPADDR + output.split(",")[0]
          VIPERPORT = output.split(",")[1]
          
     return VIPERTOKEN

VIPERTOKEN=getparams()
if VIPERHOST=="":
    print("ERROR: Cannot read viper.txt: VIPERHOST is empty or HPDEHOST is empty")

#############################################################################################################
#                                     CREATE TOPICS IN KAFKA

# Set personal data
def datasetup(maintopic,preprocesstopic):
     companyname="OTICS"
     myname="Sebastian"
     myemail="Sebastian.Maurice"
     mylocation="Toronto"

     # Replication factor for Kafka redundancy
     replication=1
     # Number of partitions for joined topic
     numpartitions=1
     # Enable SSL/TLS communication with Kafka
     enabletls=1
     # If brokerhost is empty then this function will use the brokerhost address in your
     # VIPER.ENV in the field 'KAFKA_CONNECT_BOOTSTRAP_SERVERS'
     brokerhost=''
     # If this is -999 then this function uses the port address for Kafka in VIPER.ENV in the
     # field 'KAFKA_CONNECT_BOOTSTRAP_SERVERS'
     brokerport=-999
     # If you are using a reverse proxy to reach VIPER then you can put it here - otherwise if
     # empty then no reverse proxy is being used
     microserviceid=''


     # Create a main topic that will hold data for several streams i.e. if you have 1000 IoT devices, and each device has 10 fields,
     # rather than creating 10,000 streams you create ONE main stream to hold 10000 streams, this will drastically reduce Kafka partition
     # costs


     description="TML Use Case"

     # Create the 4 topics in Kafka concurrently - it will return a JSON array
     result=maadstml.vipercreatetopic(VIPERTOKEN,VIPERHOST,VIPERPORT,maintopic,companyname,
                                    myname,myemail,mylocation,description,enabletls,
                                    brokerhost,brokerport,numpartitions,replication,
                                    microserviceid)
      
     # Load the JSON array in variable y
     try:
         y = json.loads(result,strict='False')
     except Exception as e:
         y = json.loads(result)


     for p in y:  # Loop through the JSON ang grab the topic and producerids
         pid=p['ProducerId']
         tn=p['Topic']

     # Create the 4 topics in Kafka concurrently - it will return a JSON array
     result=maadstml.vipercreatetopic(VIPERTOKEN,VIPERHOST,VIPERPORT,preprocesstopic,companyname,
                                    myname,myemail,mylocation,description,enabletls,
                                    brokerhost,brokerport,numpartitions,replication,
                                    microserviceid)
         
     return tn,pid


def sendtransactiondata(maintopic,mainproducerid,VIPERPORT,index,preprocesstopic):

 #############################################################################################################
      #                                    PREPROCESS DATA STREAMS

      # Roll back each data stream by 10 percent - change this to a larger number if you want more data
      # For supervised machine learning you need a minimum of 30 data points in each stream
     maxrows=3000
      # Go to the last offset of each stream: If lastoffset=500, then this function will rollback the 
      # streams to offset=500-50=450
     offset=-1
      # Max wait time for Kafka to response on milliseconds - you can increase this number if
      #maintopic to produce the preprocess data to
     topic=maintopic
      # producerid of the topic
     producerid=mainproducerid
      # use the host in Viper.env file
     brokerhost=''
      # use the port in Viper.env file
     brokerport=-999
      #if load balancing enter the microsericeid to route the HTTP to a specific machine
     microserviceid=''
      #These are the streams to preprocess
     #streamstojoin=substream + "," + substream + "," + substream
     streamstojoin="Voltage_preprocessed_AnomProb,Current_preprocessed_AnomProb"

      # You can preprocess with the following functions: MAX, MIN, SUM, AVG, COUNT, DIFF
      # here we will take max values of the arcturus-humidity, we will Diff arcturus-temperature, and average arcturus-Light_Intensity
      # NOTE: The number of process logic functions MUST match the streams - the operations will be applied in the same order
     preprocesslogic='avg,avg'
     #preprocesslogic='diff'
     preprocessconditions=''
    
     # This is the topic id representing the device data or entity data you want to preprocess
     topicid=-1
     # Add a 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic 
     delay=7000
     # USE TLS encryption when sending to Kafka Cloud (GCP/AWS/Azure)
     enabletls=1
     identifier = "IoT Data preprocess"
      
     try:
        result=maadstml.viperpreprocessproducetotopicstream(VIPERTOKEN,VIPERHOST,VIPERPORT,topic,producerid,offset,maxrows,enabletls,delay,brokerhost,
                                          brokerport,microserviceid,topicid,streamstojoin,preprocesslogic,preprocessconditions,identifier,preprocesstopic)
        #print(result)
     except Exception as e:
        print("ERROR:",e)
     


#############################################################################################################
#                                     SEND DATA TO DATA STREAMS IN PARALLEL USING SSL/TLS FOR WALMART EXAMPLE
maintopic='iot-preprocess'
preprocesstopic='iot-preprocess2'

maintopic,producerid=datasetup(maintopic,preprocesstopic)
print(maintopic,producerid)


async def startviper():

        print("Start Preprocess2-iot-monitor-customdata Request:",datetime.datetime.now())
        while True:
          try:   
            sendtransactiondata(maintopic,producerid,VIPERPORT,-1,preprocesstopic)            
            time.sleep(1)
          except Exception as e:
            print("ERROR:",e)
            continue
   
async def spawnvipers():

    loop.run_until_complete(startviper())
  
loop = asyncio.new_event_loop()
loop.create_task(spawnvipers())
asyncio.set_event_loop(loop)

loop.run_forever()


