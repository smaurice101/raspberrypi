# Developed by Sebastian Maurice
# Date: Sept 2023

import requests
import json
import maadstml
import time
import os
import random

###################################################### START TML TOPIC PROCESS #######################################
# Set Global variables for VIPER and HPDE - You can change IP and Port for your setup of 
# VIPER and HPDE
VIPERHOST="https://127.0.0.1"
VIPERPORT=8000

#VIPERHOST="https://10.0.0.144"
#VIPERPORT=62049

# Set Global variable for Viper confifuration file - change the folder path for your computer
viperconfigfile="c:/maads/golang/go/bin/viper.env"

#                                      STORE VIPER TOKEN
# Get the VIPERTOKEN from the file admin.tok - change folder location to admin.tok
# to your location of admin.tok
def getparams():
        
     with open("c:/maads/golang/go/bin/admin.tok", "r") as f:
        VIPERTOKEN=f.read()
  
     return VIPERTOKEN

VIPERTOKEN=getparams()

def setupkafkatopic(topicname):
          # Set personal data
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

###################################################### START PACKET TRACER #######################################
# Login to Packet tracer SDN on port 58000
def login(session):
      headers = {
      'Content-Type': 'application/json',
      }

      json_data = {
      'username': 'cisco',
      'password': 'cisco123!',
      }

      try:
        response = session.post('http://localhost:58000/api/v1/ticket', headers=headers, json=json_data)
      except Exception as e:
        print("ERROR: Make sure packet tracer is running:", e)
        return ""
      
      if str(response) == "<Response [401]>":
        print("Error: cannot connect:", response)
        return ""
      
      return response.json()['response']['serviceTicket']
      #NC-5-d3023664a1fd4b6fa04b-nbi

#Get the seriveticket or token from Packet tracer - this is needed for all of the calls to get network data
def getpackettracerticket():
  session = requests.session()
  #token=login(session)
  #token='NC-5-d3023664a1fd4b6fa04b-nbi'

  #resp = json.loads(str(resp),strict='False')
  #print(resp)
  token = login(session)
  if token == "":
    return "",""
  
  print(token)
  return token,session

# Get network data from packet tracer
def getnetworkinfo(session,token,mtype):
     
     headers = {
       'X-Auth-Token': token,
     }

     baseurl='http://localhost:58000/api/v1/' + mtype
     print(baseurl)

     response = session.get(baseurl, headers=headers)
     return response.json()


def getdatafrompackettracer(session,token):

#  mtype='network-device'
 # mtype='host/ip-address/192.168.5.21'
  #mtype='assurance/health'
  #mtype='assurance/health-issues'
  #mtype='assurance/health/10'
  #mtype='network-health'

  #hosts
  mtype="host?limit=&offset=&sortBy=&order=&hostName=&hostMac=&hostType=&connectedInterfaceName=&hostIp=&connectedNetworkDeviceIpAddress=&subType=&filterOperation="

  #host count
  #mtype="host/count?hostName=&hostMac=&hostType=&connectedInterfaceName=&hostIp=&connectedNetworkDeviceIpAddress=&subType=&filterOperation="
  res=getnetworkinfo(session,token,mtype)

#  print(res)
  
  return res

###################################################### END PACKET TRACER #######################################



def producetokafka(value, tmlid, identifier,producerid,maintopic,substream):
     
     
     inputbuf=value     
     topicid=-999

     print("value=",value)
       
     # Add a 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic 
     delay=7000
     enabletls=1

     try:
        result=maadstml.viperproducetotopic(VIPERTOKEN,VIPERHOST,VIPERPORT,maintopic,producerid,enabletls,delay,'','', '',0,inputbuf,substream,
                                            topicid,identifier)
        print(result)
     except Exception as e:
        print("WARN:",e)


##############################################################
# global variable:
# 1. hackedips (subnet-[i or d],hostid): 5.11,6.12,5.21, i=increase,d=decrease
# 2. dynamically turn off ports on machine - students should detect which machine cannot be pinged - meaning it is down
hackedid="5.11-i,6.12-i,5.21-d"
lastinboundpacketi=0
lastoutboundpacketi=0

lastinboundpacketd=1000000
lastoutboundpacketd=1000000

def formatdataandstream(mainjson,producerid,maintopic):
       global hackedid,lastinboundpacketi,lastoutboundpacketi,lastinboundpacketd,lastoutboundpacketd
       harr = hackedid.split(",")
       #print(harr)
       #print(mainjson)
       for i in mainjson['response']:
          jbuf = str(i)
          jbuf='"'.join(jbuf.split("'"))
          
          inside=0
          for h in harr:
            hidarr = h.split("-")            
            if i['hostName'] == hidarr[0]: # hacked machines
              inside=1    
              vali=random.randint(5096,10000)
              valo=random.randint(5096,10000)
              if i['pingStatus'] == "FAILURE":
                 jbuf=jbuf[:-1] + ',"inboundpackets": 0,"outboundpackets": 0}'                                                     
              elif hidarr[0]=="i":
                 lastinboundpacketi=lastinboundpacketi + vali
                 lastoutboundpacketi=lastoutboundpacketi + valo                  
                 jbuf=jbuf[:-1] + ',"inboundpackets": ' + str(lastinboundpacketi) + "," + '"outboundpackets": ' + str(lastoutboundpacketi) + "}"
              else:
                 vali=random.randint(10,1000)
                 valo=random.randint(10,1000)
                 lastinboundpacketd=lastinboundpacketd + vali
                 lastoutboundpacketd=lastoutboundpacketd + valo
                 if lastinboundpacketd <= 0:
                       lastinboundpacketd=1000000
                 if lastoutboundpacketd <= 0:
                       lastoutboundpacketd=1000000
                       
                 jbuf=jbuf[:-1] + ',"inboundpackets": ' + str(lastinboundpacketd) + "," + '"outboundpackets": ' + str(lastoutboundpacketd) + "}"                                  
          if inside==0: # normal machines  
              vali=random.randint(64,524)
              valo=random.randint(64,524)
              if i['pingStatus'] == "FAILURE":
                 jbuf=jbuf[:-1] + ',"inboundpackets": 0,"outboundpackets": 0}'                                                     
              else:
                 jbuf=jbuf[:-1] + ',"inboundpackets": ' + str(vali) + "," + '"outboundpackets": ' + str(valo) + "}"

          #print(jbuf)
    #      writedata(jbuf)
          ############################### Stream to Kafka
          senddata(jbuf,producerid,maintopic)

def senddata(json,producerid,maintopic):

      producetokafka(json, "", "",producerid,maintopic,"")
      return

def writedata(resp):
  file1 = open("cisco_network_data.txt", "a")  # append mode
  fbuf = resp + "\n"
  file1.write(fbuf)
  file1.close()
      
###################################################### END TML PROCESS #######################################


###################################################### START MAIN PROCESS #######################################

maintopic='cisco-network-mainstream'
producerid=''
try:
  topic,producerid=setupkafkatopic(maintopic)
except Exception as e:
  pass


token,session = getpackettracerticket()
if token=="":
     print("ERROR: Cannot get ticket from packet tracer SDN") 
else:
 i=0
 while True:
   resp=getdatafrompackettracer(session,token)
   if resp == "":
      print("Cannot get data from packet tracer. Make sure PT is running and listening on port 58000.")
      continue
#  print(resp)
  
   formatdataandstream(resp,producerid,maintopic)
#  break
   time.sleep(.2)
  #i = i + 1
  #if i > 100000:
   #   break  




