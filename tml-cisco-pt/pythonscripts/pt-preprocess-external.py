# Developed by: Sebastian Maurice, PhD
# Date: 2021-01-18 
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

mainkafkatopic = os.environ['KAFKAPRODUCETOPIC'] 

###################################################### START TML TOPIC PROCESS #######################################
# Set Global variables for VIPER and HPDE - You can change IP and Port for your setup of 
# VIPER and HPDE
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
     global VIPERHOST, VIPERPORT, HTTPADDR, basedir
     with open(basedir + "/Viper-preprocess/admin.tok", "r") as f:
        VIPERTOKEN=f.read()

     if VIPERHOST=="":
        with open(basedir + "/Viper-preprocess/viper.txt", 'r') as f:
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
     maxrows=500
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

     # look for the json where Inspection_Details.0.checklist.0.response=No, then output that json, equal,greaterthan,lessthan
#     preprocessconditions='custom:Inspection_Details.0.checklist.0.response~condition:equal No~toplevelarray:Inspection_Details~\
#returnarray:General_Information,Plant_Name,Location,Inspection_Date,Inspector_Name,Inspection_workdays,Entry_Time,Exit_Time,Phone_Number,\
#Fax_Number,Additional_Notes~customattrs:area~customarray:checklist'

########with chatgpt
     # equalor
     # equaland
     # containsor
     # containsand
     ######## TBD
     # greaterthan
     # lessthan
     # equal
     # dataage_[UTC offset]_[timetype], millisecond, second, minute, hour, day
     # dataage_1_second
     #fieldcontainsor,[name of field],[values]
     #fieldcontainsand,[name of field],[values]
     #fieldcontainsnot,[name of field],[values]

     #fieldequalor,[name of field],[values]
     #fieldequaland,[name of field],[values]
     #fieldlessthanor,[name of field],[values]
     #fieldlessthanand,[name of field],[values]
     #fieldgreaterthanor,[name of field],[values]
     #fieldgreaterthanand,[name of field],[values]

     #sum,[logictype],[values],[name of field],[values]
     #sum,[logictype],[values],[name of field],[values]
     #sum,[logictype],[values],[name of field],[values]

     #sumif,[logictype],[values],[name of field],[values]
     #sumif,[logictype],[values],[name of field],[values]
     #sumif,[logictype],[values],[name of field],[values]

     #avg,[logictype],[values],[name of field],[values]
     #avg,[logictype],[values],[name of field],[values]
     #avg,[logictype],[values],[name of field],[values]

     #avgif,[logictype],[values],[name of field],[values]
     #avgif,[logictype],[values],[name of field],[values]
     #avgif,[logictype],[values],[name of field],[values]

     # timediff_[UTC offset]_[timetype] - returns difference in average timetype between messages:t1-t2=dt1,t2-t3=dt2,t3-t4=dt3 -- return=(dt1+dt2+dt3)/3,count
     # count
     preprocessconditions=""
#     preprocessconditions='custom:datapoint.value~condition:sum,greaterthan,0~toplevelarray:~\
#returnarray:_all~customattrs:~customarray:~chatgpt:'

#     preprocessconditions='custom:datapoint.value~condition:avg,greaterthan,0~toplevelarray:~\
#returnarray:_all~customattrs:~customarray:~chatgpt:'

#     preprocessconditions='custom:datapoint.value~condition:avgif,greaterthan,0,fieldcontainsor,metadata.oem_model,SQR226U1XXW,SQR141U1XXW~toplevelarray:~\
#returnarray:_all~customattrs:~customarray:~chatgpt:'

#     preprocessconditions='custom:datapoint.value~condition:sumif,greaterthan,0,fieldcontainsor,metadata.oem_model,SQR226U1XXW,SQR141U1XXW~toplevelarray:~\
#returnarray:_all~customattrs:~customarray:~chatgpt:'

#     preprocessconditions='custom:datapoint.created_at~condition:timediff_-5_hour,greaterthan,30,fieldcontainsnot,metadata.oem_model,SQR226U1XXW,SQR141U1XXW~toplevelarray:~\
#returnarray:_all~customattrs:~customarray:~chatgpt:'

#     preprocessconditions='custom:datapoint.created_at~condition:timediff_-5_hour,greaterthan,30,count,greaterthan,10~toplevelarray:~\
#returnarray:_all~customattrs:~customarray:~chatgpt:'


#     preprocessconditions='custom:datapoint.created_at~condition:dataage_-5_hour,greaterthan,30~toplevelarray:~\
#returnarray:_all~customattrs:~customarray:~chatgpt:'

#     preprocessconditions='custom:metadata.display_name~condition:dataage_1_second,greaterthan,10~toplevelarray:~\
#returnarray:_all~customattrs:~customarray:~chatgpt:'

#     preprocessconditions='custom:metadata.display_name~condition:timediff,greaterthan,10~toplevelarray:~\
#returnarray:_all~customattrs:~customarray:~chatgpt:'
     
     # in custom keys that last element is an array
    
     # Add a 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic 
     delay=10000
     # USE TLS encryption when sending to Kafka Cloud (GCP/AWS/Azure)
     enabletls=1
     array=0
     saveasarray=0
     topicid=-999
    
     rawdataoutput=1
     asynctimeout=120
     timedelay=0


#{"connectedAPMacAddress": "", "connectedAPName": "", "connectedInterfaceName": "FastEthernet0/6",
#"connectedNetworkDeviceIpAddress": "", "connectedNetworkDeviceName": "S2", "hostIp": "192.168.6.12",
#"hostMac": "000D.BDC5.727A", "hostName": "6.12", "hostType": "Pc", "id": "PTT0810R254-uuid",
#"lastUpdated": "2023-09-24 22:50:01", "pingStatus": "SUCCESS", "vlanId": "1",
#"inboundpackets": 1048536,"outboundpackets": 1046332}

     jsoncriteria='uid=hostName,filter:allrecords~\
subtopics=hostName,hostName,hostName~\
values=inboundpackets,outboundpackets,pingStatus~\
identifiers=inboundpackets,outboundpackets,pingStatus~\
datetime=lastUpdated~\
msgid=~\
latlong='     

#     jsoncriteria='uid=hostName,filter:allrecords~\
#subtopics=pingStatus~\
#values=pingStatus~\
#identifiers=pingStatus~\
#datetime=lastUpdated~\
#msgid=~\
#latlong='     


     tmlfilepath=''
     
     usemysql=1

     streamstojoin=""
 
     identifier = "Detect potential cyber attacks and monitor network"

     preprocesslogic='min,max,trend,anomprob,variance,avg' # millisecond,second,minute,hour,day

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
#                                     SETUP THE TOPIC DATA STREAMS

if len(mainkafkatopic)==0:
  maintopic='cisco-network-mainstream'
else:
  maintopic=mainkafkatopic
     
preprocesstopic='cisco-network-preprocess'


maintopic,producerid=datasetup(maintopic,preprocesstopic)
print(maintopic,producerid)

async def startviper():

        print("Start Request:",datetime.datetime.now())
        while True:
          try:   
            sendtransactiondata(maintopic,producerid,VIPERPORT,-1,preprocesstopic)            
           # time.sleep(1)
          except Exception as e:
            print("ERROR:",e)
            continue
   
async def spawnvipers():

    loop.run_until_complete(startviper())
  
loop = asyncio.new_event_loop()
loop.create_task(spawnvipers())
asyncio.set_event_loop(loop)

loop.run_forever()

