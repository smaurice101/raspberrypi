
# Developed by: Sebastian Maurice, PhD
# Toronto, Ontario Canada
# OTICS Advanced Analytics

#######################################################################################################################################
#  This file will create the mapping for DSN id to TML id
#########################################################################################################################################

# TML python library
import maadstml

# Uncomment IF using Jupyter notebook 
#import nest_asyncio

import json
import numpy as np
import pandas as pd
from collections import OrderedDict
import random
import csv
import gc
import os
from itertools import chain
from random import randrange
import math
#import imp
import time
import datetime


# Set Global variables for VIPER and HPDE - You can change IP and Port for your setup of 
# VIPER and HPDE
#VIPERHOST="https://127.0.0.1"
#VIPERPORT=8000

#VIPERHOST="https://10.0.0.144"
#VIPERPORT=62049

# Set Global variable for Viper confifuration file - change the folder path for your computer
basedir = os.environ['userbasedir']
viperconfigfile=basedir + "/Viper-produce/viper.env"


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
     with open(basedir + "/Viper-produce/admin.tok", "r") as f:
        VIPERTOKEN=f.read()

     if VIPERHOST=="":
        with open(basedir + '/Viper-produce/viper.txt', 'r') as f:
          output = f.read()
          VIPERHOST = HTTPADDR + output.split(",")[0]
          VIPERPORT = output.split(",")[1]
          
     return VIPERTOKEN

VIPERTOKEN=getparams()
if VIPERHOST=="":
    print("ERROR: Cannot read viper.txt: VIPERHOST is empty or HPDEHOST is empty")


def setupkafkatopic(topicname):
     # Set personal data
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


      #############################################################################################################
      #                         CREATE TOPIC TO STORE TRAINED PARAMS FROM ALGORITHM  
      
      producetotopic=topicname

      description="Topic to store the trained machine learning parameters"
      result=maadstml.vipercreatetopic(VIPERTOKEN,VIPERHOST,VIPERPORT,producetotopic,companyname,
                                     myname,myemail,mylocation,description,enabletls,
                                     brokerhost,brokerport,numpartitions,replication,
                                     microserviceid='')
      # Load the JSON array in variable y
      print("Result=",result)
      try:
         y = json.loads(result,strict='False')
      except Exception as e:
         y = json.loads(result)


      for p in y:  # Loop through the JSON ang grab the topic and producerids
         pid=p['ProducerId']
         tn=p['Topic']
         
      return tn,pid

# This sets the lat/longs for the IoT devices so it can be map
def csvlatlong(filename):
  csvfile = open(filename, 'r')

  fieldnames = ("dsn","oem","identifier","index","lat","long")
  lookup_dict = {}

  reader = csv.DictReader( csvfile, fieldnames)
  for row in reader:
        lookup_dict[(row['dsn'], row['lat'].lower(),
                    row['long'].lower(),row['identifier'])] = row

  return lookup_dict

def getlatlong(reader,search,key):
  i=0
  locations = [i for i, t in enumerate(reader) if t[0]==search]
  value_at_index = list(reader.values())[locations[0]]
  
  return value_at_index['lat'],value_at_index['long'],value_at_index['identifier']

def getlatlong2(reader):
  random_lines=random.choice(list(reader))
  return random_lines[1],random_lines[2],random_lines[0]

def producetokafka(value, tmlid, identifier,producerid,maintopic,substream):
     inputbuf=value     
     topicid=-999
  
     # Add a 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic 
     delay=7000
     enabletls=1

     try:
        result=maadstml.viperproducetotopic(VIPERTOKEN,VIPERHOST,VIPERPORT,maintopic,producerid,enabletls,delay,'','', '',0,inputbuf,substream,
                                            topicid,identifier)
     except Exception as e:
        print("ERROR:",e)
 

inputfile=basedir + '/IotSolution/IoTData.txt'

# MAin Kafka topic to store the real-time data
maintopic='iot-mainstream'

# Setup Kafka topic
producerid=''
try:
  topic,producerid=setupkafkatopic(maintopic)
except Exception as e:
  pass

reader=csvlatlong(basedir + '/IotSolution/dsntmlidmain.csv')

k=0

file1 = open(inputfile, 'r')
print("Data Producing to Kafka Started:",datetime.datetime.now())

while True:
  line = file1.readline()
  line = line.replace(";", " ")
  # add lat/long/identifier
  k = k + 1
  try:
    if not line or line == "":
        #break
       file1.seek(0)
       k=0
       print("Reached End of File - Restarting")
       print("Read End:",datetime.datetime.now())
       continue

    jsonline = json.loads(line)
    lat,long,ident=getlatlong(reader,jsonline['metadata']['dsn'],'dsn')
    line = line[:-2] + "," + '"lat":' + lat + ',"long":'+long + ',"identifier":"' + ident + '"}'

    producetokafka(line.strip(), "", "",producerid,maintopic,"")
    # change time to speed up or slow down data   
    time.sleep(0.15)
  except Exception as e:
     print(e)  
     pass  
  
file1.close()

