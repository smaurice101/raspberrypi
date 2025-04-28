import os
import requests
import json
import maadstml

# NOTE: You need the Docker container maadsdocker/privategpt running for this API to work:
# 1. docker pull: docker pull maadsdocker/tml-privategpt-no-gpu-amd64
# 2. Docker Run: docker run -d -p 8001:8001 --env PORT=8001 maadsdocker/tml-privategpt-no-gpu-amd64:latest


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
  print(response) 
  
# Ingest or load this file into privateGPT
def ingestfile(docname,doctype,pgptip,pgptport,pgptendpoint):
  
  maadstml.pgptingestdocs(docname,doctype,pgptip,pgptport,pgptendpoint)
  
  
############################################# CONTEXT
# Ingest file for context
# Choose file to ingest to set context: PDF, CSV, etc.. 
docname="c:/maads/privategpt/ar2022-eng.pdf"

# Doctype can be: binary, text
doctype = 'binary'

# mainport and mainip are the IP and PORT that PrivateGPT is listening on
mainport = "8001"
mainip = "http://127.0.0.1"

######################################################## pgpthealth ######################################################
# This will get the the running state of privateGPT: if it is running it will return 'ok'
pgptendpoint="/health"
pgpthealth(mainip,mainport,pgptendpoint)

######################################################## ingestfile ######################################################
# This will ingest documents and generate embeddings from the document - this is needed to set CONTEXT for privateGPT
pgptendpoint="/v1/ingest"
ingestfile(docname,doctype,mainip,mainport,pgptendpoint)

####################################################### getingested #######################################################
# This will get the embeddings from documents ingested into privateGPT
# It will return document ids for the embeddings - this can be used to "FILTER" documents and use specific documents for CONTEXT
pgptendpoint="/v1/ingest/list"
docids,docstr,docidsstr=getingested(docname,mainip,mainport,pgptendpoint)
print(docids)
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
pgptchat("Can you give a full summary of this document?",True,docidsstr,mainport,False,mainip,pgptendpoint)

###################################################### pgptdeleteembeddings ########################################################
pgptendpoint="/v1/ingest/"
#pgptdeleteembeddings(docids, mainip,mainport,pgptendpoint)
