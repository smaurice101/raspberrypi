# Developed by: Sebastian Maurice, PhD
# Date: 2023-05-18 
# Toronto, Ontario Canada

# TML python library
import maadstml

# Uncomment IF using Jupyter notebook 
import nest_asyncio

import json
import random
from joblib import Parallel, delayed
#from joblib import parallel_backend
import sys
import multiprocessing
import pandas as pd
#import concurrent.futures
import asyncio
# Uncomment IF using Jupyter notebook
nest_asyncio.apply()
import datetime
import time
import os

# Set Global Host/Port for VIPER - You may change this to fit your configuration
VIPERHOST="https://127.0.0.1"
VIPERPORT=8000


#############################################################################################################
#                                      STORE VIPER TOKEN
# Get the VIPERTOKEN from the file admin.tok - change folder location to admin.tok
# to your location of admin.tok
def getparams():
        
     with open("c:/maads/golang/go/bin/admin.tok", "r") as f:
        VIPERTOKEN=f.read()
  
     return VIPERTOKEN

VIPERTOKEN=getparams()

#############################################################################################################
#                                     CREATE TOPICS IN KAFKA

# Set personal data
def datasetup(maintopic,preprocesstopic):
     companyname="OTICS"
     myname="Sebastian"
     myemail="Sebastian.Maurice"
     mylocation="Toronto"

     # Replication factor for Kafka redundancy
     replication=3
     # Number of partitions for joined topic
     numpartitions=3
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
     maxrows=2000
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

  
      # You can preprocess with the following functions: MAX, MIN, SUM, AVG, COUNT, DIFF,OUTLIERS
      # here we will take max values of the arcturus-humidity, we will Diff arcturus-temperature, and average arcturus-Light_Intensity
      # NOTE: The number of process logic functions MUST match the streams - the operations will be applied in the same order
#
#     preprocesslogic='min,max,avg,diff,outliers,variance,anomprob,varied,outliers2-5,anomprob2-5,anomprob3,gm,hm,trend,IQR,trimean,spikedetect,cv,skewness,kurtosis'
#     preprocesslogic='anomprob,outliers,consistency,variance,max,avg,diff,diffmargin,trend,min'

     preprocessconditions=''
     
      # You can access these new preprocessed topics as:
      #   arcturus-humidity_preprocessed_Max
      #   arcturus-temperature_preprocessed_Diff
      #   arcturus-Light_Intensity_preprocessed_Avg      
    
     # Add a 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic 
     delay=70
     # USE TLS encryption when sending to Kafka Cloud (GCP/AWS/Azure)
     enabletls=1
     array=0
     saveasarray=1
     topicid=-999
    
     rawdataoutput=1
     asynctimeout=120
     timedelay=0

     #jsoncriteria='uid=subject.reference,filter:resourceType=Observation~\
#subtopics=code.coding.0.code,component.0.code.coding.0.code,component.1.code.coding.0.code~\
#values=valueQuantity.value,component.0.valueQuantity.value,component.1.valueQuantity.value~\
#identifiers=code.coding.0.display,component.0.code.coding.0.display,component.1.code.coding.0.display~\
#datetime=effectiveDateTime~\
#msgid=id~\
#latlong='

 # This is type Collections
 
#	  // check for payload  'uid=subject.reference,filter:resourceType=MedicationAdministration,payload=payload.payload~\

     jsoncriteria='uid=metadata.dsn,filter:allrecords~\
subtopics=metadata.property_name~\
values=datapoint.value~\
identifiers=metadata.display_name~\
datetime=datapoint.updated_at~\
msgid=datapoint.id~\
latlong=lat:long'     

#     jsoncriteria='uid=entry.0.resource.id,filter:allrecords~\
#subtopics=entry.1.resource.type.0.coding.0.code~\
#values=entry.1.resource.name~\
#identifiers=entry.0.resource.id~\
#datetime=timestamp~\
#msgid=entry.2.resource.code.coding.0.display:entry.1.resource.name~\
#latlong=entry.1.resource.position.latitude:entry.1.resource.position.longitude'     # use : to join multiple fields


     tmlfilepath=''
     
     usemysql=1

#     streamstojoin="Current,Voltage,Power"
     streamstojoin=""
 
     identifier = "IoT device performance and failures"

     preprocesslogic='anomprob,trend,avg'

     
#     pathtotmlattrs='oem=id,lat=subject.reference,long=component.0.code.coding.0.display,location=component.1.valueQuantity.value'     
     pathtotmlattrs='oem=n/a,lat=n/a,long=n/a,location=n/a,identifier=n/a'     
     
     try:
        result=maadstml.viperpreprocesscustomjson(VIPERTOKEN,VIPERHOST,VIPERPORT,topic,producerid,offset,jsoncriteria,rawdataoutput,maxrows,enabletls,delay,brokerhost,
                                          brokerport,microserviceid,topicid,streamstojoin,preprocesslogic,preprocessconditions,identifier,
                                          preprocesstopic,array,saveasarray,timedelay,asynctimeout,usemysql,tmlfilepath,pathtotmlattrs)
#        time.sleep(.5)
        print(result)
        return result
     except Exception as e:
        print("ERROR:",e)
        return e
     

#############################################################################################################
#                                     SETUP THE TOPIC DATA STREAMS FOR WALMART EXAMPLE

maintopic='iot-mainstream'
preprocesstopic='iot-preprocess'

maintopic,producerid=datasetup(maintopic,preprocesstopic)
print(maintopic,producerid)

async def startviper():

        print("Start Request:",datetime.datetime.now())
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
