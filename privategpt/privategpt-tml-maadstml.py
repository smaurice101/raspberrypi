import os
import requests
import json
import maadstml

# NOTE: You need the Docker container maadsdocker/privategpt running for this API to work:
# 1. docker pull: docker pull maadsdocker/tml-privategpt-no-gpu-amd64
# 2. Docker Run: docker run -d -p 8001:8001 --env PORT=8001 maadsdocker/tml-privategpt-no-gpu-amd64:latest


###################################################### START TML TOPIC PROCESS #######################################
# Set Global variables for VIPER and HPDE - You can change IP and Port for your setup of 
# VIPER and HPDE
VIPERHOST="https://127.0.0.1"
VIPERPORT=8000

#VIPERHOST="https://10.0.0.144"
#VIPERPORT=62049

################################################################################
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



############### REST API Client

def getingested(docname,ip,port,endpoint):

  docids,docstr,docidsstr=maadstml.pgptgetingestedembeddings(docname,ip,port,endpoint)
  return docids,docstr,docidsstr

def pgptdeleteembeddings(docids, ip, port, endpoint):

  maadstml.pgptdeleteembeddings(docids, ip,port,endpoint)   

def pgpthealth(ip, port, endpoint):
   response=maadstml.pgpthealth(ip,port,endpoint)
   print(response)

def pgptchat(prompt,context,docfilter,port,includesources,ip,endpoint):
  
  response=maadstml.pgptchat(prompt,context,docfilter,port,includesources,ip,endpoint)
  return response
  
# Ingest or load this file into privateGPT
def ingestfile(docname,doctype,pgptip,pgptport,pgptendpoint):
  
  maadstml.pgptingestdocs(docname,doctype,pgptip,pgptport,pgptendpoint)
  
############################ Get data from Kafka Topic

def consumetopicdata(maintopic,rollback):
      consumerid="streamtopic"
      companyname="otics"
  
      result=maadstml.viperconsumefromtopic(VIPERTOKEN,VIPERHOST,VIPERPORT,maintopic,
                  consumerid,companyname,partition=-1,enabletls=1,delay=100,
                  offset=-1, brokerhost='',brokerport=-999,microserviceid='',
                  topicid='-999',rollbackoffsets=rollback,preprocesstype='')

#      print(result)
      return result

def gatherdataforprivategpt(result):
     
   res=json.loads(result,strict='False')
   rawdataoutbound = []
   rawdatainbound = []
   privategptmessage = []

   thresholdoutbound='1000000'
   thresholdinbound='1000000'

   for r in res['StreamTopicDetails']['TopicReads']:
        identarr=r['Identifier'].split("~")
        if 'outboundpackets' in r['Identifier']:
             message = 'Answer the following question about the outbound network traffic data using the context.<br><br>Context: Normally, \
outbound network traffic data size should not exceed ' + thresholdoutbound + ' bytes.<br><br>Outbound network traffic data size:<br>'
             for d in r['RawData']:
               message = message  + str(d) + '<br>'
             message = message + "<br>Question: Does any value or size in the outbound network traffic data size, from host machine " + identarr[0] + ", exceed " + thresholdoutbound + \
" bytes or show unusual patterns?  Should this machine be investigated? Keep your answer short and to the point."
             
        if 'inboundpackets' in r['Identifier']:
             message = 'Answer the following question about the inbound network traffic data using the context.<br><br>Context: Normally, \
inbound network traffic data size should not exceed ' + thresholdinbound + ' bytes.<br><br>Inbound network traffic data size:<br>'
             for d in r['RawData']:
               message = message  + str(d) + '<br>'
             message = message + "<br>Question: Does any value or size in the inbound network traffic data size, from host machine " + identarr[0] + ", exceed " + thresholdinbound + \
" bytes or show unusual patterns?  Should this machine be investigated? Keep your answer short and to the point."

        privategptmessage.append(message)
                 

   #print("message=",privategptmessage)
   return privategptmessage

#def sendtoprivategpt():
##Here are the outbound packets for host machine 5.30 in bytes, are any bytes greater than 1000000 bytes?
##384 bytes
##92 bytes
##259 bytes
##404 bytes
##291 bytes
##385 bytes
##458 bytes
##160 bytes
##153 bytes
##318 bytes
##275 bytes
##487 bytes
##185 bytes
##129 bytes
##
##If so, the host machine should be investigated. Should this machine be investigated based on the individual packets?

      
def producegpttokafka(value,maintopic):
     inputbuf=value     
     topicid=-999
     producerid="private-gpt"
     identifier = "This is analysing TML output with privategpt"
     substream=""

     print("value=",value)
       
     # Add a 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic 
     delay=7000
     enabletls=1

     try:
        result=maadstml.viperproducetotopic(VIPERTOKEN,VIPERHOST,VIPERPORT,maintopic,producerid,enabletls,delay,'','', '',0,inputbuf,substream,
                                            topicid,identifier)
        print(result)
     except Exception as e:
        print("ERROR:",e)

def sendtoprivategpt(maindata,maintopic):

   pgptendpoint="/v1/completions"

   for m in maindata:
        print(m)
        response=pgptchat(m,False,"",mainport,False,mainip,pgptendpoint)
        # Produce data to Kafka
        response = response[:-1] + "," + "\"prompt\":\"" + m + "\"}"
        if 'ERROR:' not in response:
          producegpttokafka(response,maintopic)
          print("response=",response)


# Private GPT Container IP and Port
mainport = "8001"
mainip = "http://127.0.0.1"

#maintopic='cisco-network-mainstream'
maintopic='cisco-network-preprocess'
setupkafkatopic(maintopic)
pgpttopic='cisco-network-privategpt'
setupkafkatopic(pgpttopic)

# Rollback Kafka stream - you can increase these offsets
rollback=2

# This While loop continuously processes kafka real-time data
while True:
 # Get preprocessed data from Kafka
 result = consumetopicdata(maintopic,rollback)

 # Format the preprocessed data for PrivateGPT
 maindata = gatherdataforprivategpt(result)

 # Send the data to PrivateGPT and produce to Kafka
 sendtoprivategpt(maindata,pgpttopic)



############################################# CONTEXT
# Ingest file for context
# Choose file to ingest to set context: PDF, CSV, etc.. 
docname="c:/maads/privategpt/ar2022-eng.pdf"

# Doctype can be: binary, text
doctype = 'binary'

# mainport and mainip are the IP and PORT that PrivateGPT is listening on

######################################################## pgpthealth ######################################################
# This will get the the running state of privateGPT: if it is running it will return 'ok'
pgptendpoint="/health"
#pgpthealth(mainip,mainport,pgptendpoint)

######################################################## ingestfile ######################################################
# This will ingest documents and generate embeddings from the document - this is needed to set CONTEXT for privateGPT
pgptendpoint="/v1/ingest"
#ingestfile(docname,doctype,mainip,mainport,pgptendpoint)

####################################################### getingested #######################################################
# This will get the embeddings from documents ingested into privateGPT
# It will return document ids for the embeddings - this can be used to "FILTER" documents and use specific documents for CONTEXT
pgptendpoint="/v1/ingest/list"
#docids,docstr,docidsstr=getingested(docname,mainip,mainport,pgptendpoint)
#print(docids)
###################################################### pgptchat ########################################################
# This will send a prompt to privateGPT and get a response based on context, or no context.
# It accepts 7 parameters:
# 1. prompt= Your prompt
# 2. context= This is True if you want privateGPT to use context, False if no
# 3. docfilter= This is the docidsstr variable and used for filtering documents for context, if this is empty, privateGPT will use ALL ingested documents for context
# 4. port = port for privateGpt
# 5. includesources = If this is True privateGPT will return the sources of the document used for response, if False no source are returned
# 6. ip= IP for privateGPT
# 7  endpoint= endpoint to use

pgptendpoint="/v1/completions"
#pgptchat("Where is Seneca College located?",False,"",mainport,False,mainip,pgptendpoint)
#pgptchat("Who is prime minister of Canada?",False,"",mainport,False,mainip,pgptendpoint)
#pgptchat("if a fire extinguher is not charged, and it is not in a critical area, is this high, medium, or low priority? Choose one priority.",False,"",mainport,False,mainip,pgptendpoint)
#pgptchat("What is Fintrac's main conclusions?",True,"",mainport,False,mainip,pgptendpoint)
#pgptchat("What is Sara's message?",True,"",mainport,False,mainip,pgptendpoint)
#pgptchat("What are the main challenges that Fintrac faces? And, how is it addressing these challenges?",True,"",mainport,False,mainip,pgptendpoint)
#pgptchat("What is Fintrac's goals? How much money are speding to acheive the goals?",True,"",mainport,False,mainip,pgptendpoint)
#pgptchat("Can you give a full summary of this document?",True,docidsstr,mainport,False,mainip,pgptendpoint)

###################################################### pgptdeleteembeddings ########################################################
pgptendpoint="/v1/ingest/"
#pgptdeleteembeddings(docids, mainip,mainport,pgptendpoint)
