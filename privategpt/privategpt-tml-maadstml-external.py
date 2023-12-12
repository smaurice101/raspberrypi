import os
import requests
import json
import maadstml
import datetime
import glob
import mimetypes

# NOTE: You need the Docker container maadsdocker/privategpt running for this API to work:
# 1. docker pull: docker pull maadsdocker/tml-privategpt-no-gpu-amd64
# 2. Docker Run: docker run -d -p 8001:8001 --env PORT=8001 maadsdocker/tml-privategpt-no-gpu-amd64:latest
mainpreprocesstopic = os.environ['KAFKAPREPROCESSTOPIC'] 
pgptrollback = os.environ['PGPTROLLBACK'] 
createkafkaembeddings = os.environ['KAFKAEMBEDDINGS']
keepfiles = os.environ['KEEPKAFKAFILES']
loaddocs = os.environ['LOADDOCS']
docfolder = os.environ['DOCFOLDER']

if docfolder == "":
     docfolder = "" # i.e. /subfolder/path_to_files
if createkafkaembeddings == "":
     createkafkaembeddings=0
if keepfiles == "":
     keepfiles=0
if loaddocs == "":
     loaddocs=0

if pgptrollback == "":
     pgptrollback=3
        
if mainpreprocesstopic == "":
      mainpreprocesstopic = 'cisco-network-preprocess'
        
pgptip = os.environ['PGPTIP'] 
pgptport = os.environ['PGPTPORT'] 
if pgptip == "":
     pgptip="http://127.0.0.1"
if pgptport == "":
     pgptport=8001

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
     with open(basedir + "/Viper-preprocess-pgpt/admin.tok", "r") as f:
        VIPERTOKEN=f.read()

     if VIPERHOST=="":
        with open(basedir + "/Viper-preprocess-pgpt/viper.txt", 'r') as f:
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


def Average(ni,th): 
    r=round(sum(ni) / len(ni),0) 
    m='' 
    if r >= th:
        m='The average value is ' + str(r) + ', and it is outside normal limits because it exceeds: ' + str(th)
    else:     
        m='The average value is ' + str(r) + ', and it is within normal limits because it does not exceed: ' + str(th)
 
    return m
     
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
 # response = html.escape(response)
   
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

   thresholdoutbound=1000000
   thresholdinbound=1000000

   for r in res['StreamTopicDetails']['TopicReads']:
        identarr=r['Identifier'].split("~")
        message = ""
        messagedetails = ""
        if 'outboundpackets' in r['Identifier']:
             message = 'Here is a list of numbers separated by a comma, each number represents bytes it is not one number, they are separate numbers: <br> '
             for d in r['RawData']:
               message = message  + str(d) + ',<br>'
             #message = message[:-1]     
             message = message  + ' <br> ' + Average(r['RawData'],thresholdoutbound) + '<br>\
Answer these questions:<br>\
<br>Question 1: Are there any drastic changes in the values of these data? \
<br>Question 2: Based on your knowledge of network security should this machine be investigated?   \
<br>Keep your response short.'
             messagedetails = "Outbound packets - Host: " + identarr[0]
        if 'inboundpackets' in r['Identifier']:
             message = 'Here is a list of numbers separated by a comma, each number represents bytes it is not one number, they are separate numbers: <br>'
             for d in r['RawData']:
               message = message  + str(d) + ',<br>'
             #message = message[:-1]                       
             message = message  + ' <br> ' + Average(r['RawData'],thresholdinbound) + '<br>\
Answer these questions:<br>\
<br>Question 1: Are there any drastic changes in the values of these data? \
<br>Question 2: Based on your knowledge of network security should this machine be investigated?  \
<br>Keep your response short.'
             messagedetails = "Inbound packets - Host: " + identarr[0]             
        if message != "":
          privategptmessage.append([message,messagedetails])
                 

   #print("message=",privategptmessage)
   return privategptmessage

      
def producegpttokafka(value,maintopic):
     inputbuf=value     
     topicid=-999
     producerid="private-gpt"
     identifier = "This is analysing TML output with privategpt"
     substream=""

     try:
          check=json.loads(value) 
          print("value=",value)
     except Exception as e:
          print("Not a valid JSON=",value)
          return
     
       
     # Add a 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic 
     delay=7000
     enabletls=1

     try:
        result=maadstml.viperproducetotopic(VIPERTOKEN,VIPERHOST,VIPERPORT,maintopic,producerid,enabletls,delay,'','', '',0,inputbuf,substream,
                                            topicid,identifier)
        print(result)
     except Exception as e:
        print("ERROR:",e)

def randomfile():
     basename = "TML-privategpt"
     suffix = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
     filename = "_".join([basename, suffix]) # e.g. 'mylogfile_120508_171442'
     filename = filename + ".txt"
     return filename

def gatherdataforembeddings(result):
   res=json.loads(result,strict='False')
   mainmessage = ''
   
   for r in res['StreamTopicDetails']['TopicReads']:
        identarr=r['Identifier'].split("~")
        if 'outboundpackets' in r['Identifier']:
             message = 'Here are the outbound network traffic data for host machine ' + identarr[0] + '.\n\nOutbound network traffic data size:\n'
             for d in r['RawData']:
               message = message  + str(d) + '\n'
             mainmessage = mainmessage + message + "\n\n"  
        if 'inboundpackets' in r['Identifier']:
             message = 'Here are the inbound network traffic data for host machine ' + identarr[0] + '.\n\nInbound network traffic data size:\n'
             for d in r['RawData']:
               message = message  + str(d) + '\n'
             mainmessage = mainmessage + message + "\n\n"  
               
   return mainmessage

def createkafkaembeddings(result,pgptip,pgptport,keepfile=0):
   filename = randomfile()

   maintext=gatherdataforembeddings(result)
   if maintext != "":  
     f = open(filename, "w")
     f.write(maintext)
     f.close()

   # create the embedding in privateGPT 
     ingestfile(filename,'text',pgptip,pgptport,"")
     if keepfile == 0:
        os.remove(filename)

def sendtoprivategpt(maindata,maintopic):

   pgptendpoint="/v1/completions"

   for m in maindata:
        #print(m)
        response=pgptchat(m[0],False,"",mainport,False,mainip,pgptendpoint)
        # Produce data to Kafka
        response = response[:-1] + "," + "\"prompt\":\"" + m[0] + "\",\"responsedetails\":\"" + m[1] + "\"}"
        if 'ERROR:' not in response:
          producegpttokafka(response,maintopic)
        print("response=",response)


# Private GPT Container IP and Port
mainport = pgptport
mainip = pgptip

maintopic=mainpreprocesstopic
setupkafkatopic(maintopic)
pgpttopic='cisco-network-privategpt'
setupkafkatopic(pgpttopic)

# Rollback Kafka stream - you can increase these offsets
rollback=pgptrollback

# This While loop continuously processes kafka real-time data
while True:
 # Get preprocessed data from Kafka
 result = consumetopicdata(maintopic,rollback)
 if createkafkaembeddings == 1:
      createkafkaembeddings(result,mainip,mainport,keepfiles)
      
 #print("result=",result)
# check if any data
 rs = json.loads(result)
 if len(rs['StreamTopicDetails']['TopicReads'])==0:
   print("No data found=[]")
 # Format the preprocessed data for PrivateGPT
 else:
   maindata = gatherdataforprivategpt(result)
 # Send the data to PrivateGPT and produce to Kafka
   sendtoprivategpt(maindata,pgpttopic)
      
############################################# CONTEXT
# Ingest file for context
# Choose file to ingest to set context: PDF, CSV, etc.. 
#docname="c:/maads/privategpt/ar2022-eng.pdf"

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
