from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timezone
from airflow.decorators import dag, task
from langgraph_supervisor import create_supervisor
from llama_index.core.indices.vector_store.base import VectorStoreIndex
from llama_index.core.schema import Document  # Document is often found here
from langgraph.prebuilt import create_react_agent
from llama_index.embeddings.ollama import OllamaEmbedding
from langchain_ollama import ChatOllama
import importlib
import json
import pprint
from llama_index.core.settings import Settings
from datetime import datetime, timezone
import os
import tsslogging
import sys
import time
import maadstml
import subprocess
import random
import json
import threading
import re
from binaryornot.check import is_binary
import base64
import requests
from json_repair import repair_json

sys.dont_write_bytecode = True

######################################################USER CHOSEN PARAMETERS ###########################################################
SMTP_SERVER=''
SMTP_PORT=0
SMTP_USERNAME=''
SMTP_PASSWORD='' # this should be base64 encoded 
recipient=''

if 'SMTP_SERVER' in os.environ:
   SMTP_SERVER=os.environ['SMTP_SERVER']
if 'SMTP_PORT' in os.environ:
   SMTP_PORT=int(os.environ['SMTP_PORT'])
if 'SMTP_USERNAME' in os.environ:
   SMTP_USERNAME=os.environ['SMTP_USERNAME']
if 'SMTP_PASSWORD' in os.environ:
   SMTP_PASSWORD=os.environ['SMTP_PASSWORD']
   SMTP_PASSWORD=base64.b64decode(SMTP_PASSWORD)
   SMTP_PASSWORD = SMTP_PASSWORD.decode('utf-8')
if 'recipient' in os.environ:
   recipient=os.environ['recipient']

default_args = {
 'owner': 'Sebastian Maurice',   # <<< *** Change as needed
 'ollamacontainername' : 'maadsdocker/tml-privategpt-with-gpu-nvidia-amd64-llama3-tools', #'maadsdocker/tml-privategpt-no-gpu-amd64',  # enter a valid container https://hub.docker.com/r/maadsdocker/tml-privategpt-no-gpu-amd64
 'rollbackoffset' : '5',  # <<< *** Change as needed
 'offset' : '-1', # leave as is
 'enabletls' : '1', # change as needed
 'brokerhost' : '', # <<< *** Leave as is
 'brokerport' : '-999', # <<< *** Leave as is
 'microserviceid' : '',  # change as needed
 'topicid' : '-999', # leave as is
 'delay' : '100', # change as needed
 'companyname' : 'otics',  # <<< *** Change as needed
 'consumerid' : 'streamtopic',  # <<< *** Leave as is
 'agenttopic' : '', # this topic contains the individual agent responses
 'agents_topic_prompt' : """
<consumefrom - topic agent will monitor:prompt you want for the agent to answer->>consumefrom - topic2 agent will monitor<<-prompt you want for the agent to answer>
""", # <topic agent will monitor:prompt you want for the agent>, separate multiple topic agents with ->>
 'teamlead_topic' : '', # Enter the team lead topic - all team lead responses will be written to this topic
 'teamleadprompt' : """
Enter the prompt for the Team lead agent
""", # Enter the team lead prompt 
 'supervisor_topic' : '', # Enter the supervisor topic - all supervisor responses will be written to this topic
 'supervisorprompt' : '', # Enter the supervisor prompt 
 'agenttoolfunctions' : """
tool_function:agent_name:system_prompt;tool_function2:agent_name2:sysemt_prompt2;....
""",  # enter the tools : tool_function is the name of the funtions in the agenttools python file
 'agent_team_supervisor_topic': '', # this topic will hold the responses from agents, team lead and supervisor
 'producerid' : 'agentic-ai',   # <<< *** Leave as is
 'identifier' : 'This is analysing TML output with Agentic AI',
 'mainip': 'http://127.0.0.1', # Ollama server container listening on this host
 'mainport' : '11434', # Ollama listening on this port
 'embedding': 'nomic-embed-text', # Embedding model
 'preprocesstype' : '', # Leave as is 
 'partition' : '-1', # Leave as is 
 'vectordbcollectionname' : 'tml-llm-model-v2', # change as needed
 'concurrency' : '2', # change as needed Leave at 1
 'CUDA_VISIBLE_DEVICES' : '0', # change as needed
 'temperature' : '0.1', # This value ranges between 0 and 1, it controls how conservative LLM model will be, if 0 very very, if 1 it will hallucinate
 #--------------------
 'ollama-model': 'llama3.1',
 'deletevectordbcount': '10',
 'vectordbpath': '/rawdata/vectordb',
 'contextwindow': '10000',
 'localmodelsfolder': '/mnt/c/maads/tml-airflow/rawdata/ollama'  
}

############################################################### DO NOT MODIFY BELOW ####################################################

VIPERTOKEN=""
VIPERHOST=""
VIPERPORT=""
HTTPADDR=""
mainproducerid = default_args['producerid']

def setollama(model):
    ###############  Ollama Model #################################
#    model=default_args['ollama-model']
    temperature=float(default_args['temperature'])
    embeddingmodel=default_args['embedding'] #"nomic-embed-text"
    mainip=default_args['mainip']
    mainport=int(default_args['mainport'])
    contextwindow=default_args['contextwindow']

#    mainmodels = model.split(",") # agent,teamlead,supervisor

    if 'KUBE' in os.environ:
      if os.environ['KUBE'] == "1":
         default_args['mainip']="ollama-service"
         mainip=default_args['mainip']

    print("model====",model)
    gotllm=0
    for i in range(30):
      print("Checking if LLM loaded..wait")
      try:
        llm = ChatOllama(model=model, base_url=mainip+":"+str(mainport), temperature=temperature, num_ctx=int(contextwindow))
        gotllm=1
        print("LLM loaded")
        break
      except Exception as e:
        print("Error=",e)
        time.sleep(5)
    
    if gotllm==0: 
        print("ERROR STEP 9b: Cannot load Ollama LLM model '{}' not found.".format(model))
        tsslogging.locallogs("ERROR", "STEP 9b: Cannot load Ollama LLM model '{}' not found.".format(model))      
        return "","" 

    try:
      ollama_emb = OllamaEmbedding(
        base_url=mainip+":"+str(mainport),
        model_name=embeddingmodel
      )
    except Exception as e:
      print("ERROR STEP 9b: Cannot load Ollama embedding '{}' not found.".format(embeddingmodel))
      tsslogging.locallogs("ERROR", "STEP 9b: Cannot load Ollama embedding '{}' not found.".format(embeddingmodel))
      return "",""

    Settings.embed_model = ollama_emb
    Settings.llm = llm

    return llm,ollama_emb


def checkforloadedmodels(mainmodel):

    if 'KUBE' in os.environ:
      if os.environ['KUBE'] == "1":
         default_args['mainip']="ollama-service"
         mainip=default_args['mainip']

    mainip=default_args['mainip']   
    mainport=int(default_args['mainport'])

    OLLAMA_URL = f"{mainip}:{mainport}/api/tags"
    count = 0

    while True:
      try:
        response = requests.get(OLLAMA_URL)
        response.raise_for_status()
        data = response.json()
        # Assume 'models' key contains the list of available/loaded models
        loaded_models = [model for model in data.get("models", [])]
        print("loaded_models=",loaded_models)
        if mainmodel in json.dumps(loaded_models) or mainmodel+":latest" in json.dumps(loaded_models):
          print(f"Model {mainmodel} found")
          return 1
        else:
          pull_ollama_model(mainmodel) # pull the model
          time.sleep(5)
          count += 1
          if count > 600:
           break
          else:
            continue
      except Exception as e:
        print(f"Error querying Ollama server: {e} Will keep trying")
        time.sleep(5)
        count += 1
        if count > 20:
          break
        continue

    return 0


def get_loaded_models():

    if 'KUBE' in os.environ:
      if os.environ['KUBE'] == "1":
         default_args['mainip']="ollama-service"
         mainip=default_args['mainip']

    mainip=default_args['mainip']
    mainport=int(default_args['mainport'])
    mainmodel=default_args['ollama-model']
    mainmodel = mainmodel.split(",")[0] #check if one model is there
    OLLAMA_URL = f"{mainip}:{mainport}/api/tags"
    count = 0

    while True:
      try:
        response = requests.get(OLLAMA_URL)
        response.raise_for_status()
        data = response.json()
        # Assume 'models' key contains the list of available/loaded models
        loaded_models = [model for model in data.get("models", [])]
        print("loaded_models=",loaded_models)
        if mainmodel in json.dumps(loaded_models) or mainmodel+":latest" in json.dumps(loaded_models):
          print(f"Model {mainmodel} found")
          return 1
        else:
          time.sleep(5)
          count += 1
          if count > 600:
           break 
          else:
            continue                   
      except Exception as e:
        print(f"Error querying Ollama server: {e} Will keep trying")
        time.sleep(5)
        count += 1
        if count > 20:
          break
        continue

    return 0

def remove_escape_sequences(string):
    return string.encode('utf-8').decode('unicode_escape')

def cleanstringjson(mainstr):

    mainstr = mainstr.replace("'","").replace('`',"").replace("\n","").replace("\\n","").replace("\t","").replace("\\t","").replace("\r","").replace("\\r","").replace("\\*","").replace("\\ ","").replace("\\\\","\\")


    a = list(mainstr.lower())
    b = "abcdefghijklmnopqrstuvwxyz-*123456789'{}`"
    i=0
    for char in a:
        if char == "\\" and a[i+1] in b:
          a[i]=''
        if char == "\\" and a[i+1] == "\\" and a[i+2] == '"':
          a[i]=''

        i=i+1

    mainstr=''.join(a)
    mainstr=re.sub(r'[\n\r]+', '', mainstr)

    mainstr = mainstr.translate({ord('\n'): None, ord('\r'): None})
    mainstr = " ".join(mainstr.splitlines())

    return mainstr

def cleanstring(mainstr):

    mainstr = mainstr.replace('"',"").replace("'","").replace('`',"").replace("\n","").replace("\\n","").replace("\t","").replace("\\t","").replace("\r","").replace("\\r","").replace("\\*","").replace("\\ ","").replace("\\\\","\\").replace("\\1","1").replace("\\2","2").replace("\\3","3").replace("\\4","4").replace("\\5","5").replace("\\6","6").replace("\\7","7").replace("\\8","8").replace("\\9","9")
    mainstr = mainstr.splitlines()
    mainstr = " ".join(mainstr)

    a = list(mainstr.lower())
    b = "abcdefghijklmnopqrstuvwxyz-*123456789'{}`"
    i=0
    for char in a:
        if char == "\\" and a[i+1] in b:
          a[i]=''
        if char == "\\" and a[i+1] == "\\" and a[i+2] == '"':
          a[i]=''
          
        i=i+1

    mainstr=''.join(a)    
    mainstr=re.sub(r'[\n\r]+', '', mainstr)

    mainstr = mainstr.translate({ord('\n'): None, ord('\r'): None})
    return mainstr

############## Delete folder content ########################
def deletefoldercontents(dirpath,deletevectordbcnt):
    if deletevectordbcnt < int(default_args['deletevectordbcount']):
        deletevectordbcnt += 1   
        return deletevectordbcnt
    else:
        deletevectordbcn=0
    
    folder = dirpath
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
    return deletevectordbcnt
########################### Vector DB for Team Lead: Agent Responses ###############
# this is for the team lead agent to consolidate information from individual agents
###################################################################################
def loadtextdataintovectordb(responses,deletevectordbcnt,llm):

    vectordbpath = default_args['vectordbpath']
    
    directory_path="{}/tmlvectortextindex".format(vectordbpath)    

    if not os.path.exists(directory_path):         
       os.makedirs(directory_path)
       
    # delete previous folder content
    deletevectordbcnt=deletefoldercontents(directory_path,deletevectordbcnt)

    documents = [Document(text=t) for t in responses]

    #build index
    tml_index = VectorStoreIndex.from_documents(
        documents,
        embedding="local"
    )
    #persist index

    # persist index
    tml_index.storage_context.persist(persist_dir=directory_path)
    
    tml_text_engine = tml_index.as_query_engine(llm=llm,similarity_top_k=3)

    return tml_text_engine,deletevectordbcnt

def pull_ollama_model(model_name):
    """
    Initiates an Ollama model pull using the Ollama API.

    Args:
        model_name (str): The name of the model to pull (e.g., "llama3").
    """
    mainip=default_args['mainip']
    mainport=int(default_args['mainport'])

    url = f"{mainip}:{mainport}/api/pull"  # Default Ollama API endpoint
    headers = {"Content-Type": "application/json"}
    payload = {"name": model_name}

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), stream=True)
        response.raise_for_status()  # Raise an exception for HTTP errors

        print(f"Initiating pull for model: {model_name}")
        for chunk in response.iter_content(chunk_size=None):
            if chunk:
                # Process the streaming response, e.g., print progress
                try:
                    data = json.loads(chunk.decode('utf-8'))
                    if 'status' in data:
                        print(f"Status: {data['status']}", end='\r')
                except json.JSONDecodeError:
                    pass # Handle incomplete JSON chunks if necessary

        print(f"\nPull for model '{model_name}' completed.")

    except requests.exceptions.RequestException as e:
        print(f"Error pulling model '{model_name}': {e}")

            
def stopcontainers():


   ollamacontainername = default_args['ollamacontainername']
   cfound=0
   subprocess.call("docker image ls > gptfiles.txt", shell=True)
   with open('gptfiles.txt', 'r', encoding='utf-8') as file:
        data = file.readlines()
        r=0
        for d in data:
          darr = d.split(" ")
          if '-privategpt-' in darr[0]:
            buf="docker stop $(docker ps -q --filter ancestor={} )".format(darr[0])
            if ollamacontainername in darr[0]:
                cfound=1  
                # if ollama container found check if model is already loaded - if not  stop container
                if get_loaded_models()==0:
                  print(buf)
                  subprocess.call(buf, shell=True)
                  return 0
                break
   if cfound==0:
      print("INFO STEP 9b: Ollama container {} not found.  It may need to be pulled.".format(ollamacontainername))
      tsslogging.locallogs("WARN", "STEP 9b: Ollama container not found. It may need to be pulled if it does not start: docker pull {}".format(ollamacontainername))
      return 0

   return 1

def startpgptcontainer():
      print("Starting Ollama container: {}".format(default_args['ollamacontainername'])) 
      collection = default_args['vectordbcollectionname']
      concurrency = default_args['concurrency']
      ollamacontainername = default_args['ollamacontainername']
      mainport = int(default_args['mainport'])
      cuda = int(default_args['CUDA_VISIBLE_DEVICES'])
      temp = default_args['temperature']
      mainmodel=default_args['ollama-model']
      mainembedding=default_args['embedding']
      mainhost = default_args['mainip']

      mainmodels = mainmodel.split(",")
      mainmodel = " && ".join(mainmodels)

      ollamaserver = mainhost + ":" + str(mainport)
      localmodels=''
      if default_args['localmodelsfolder'] != '':
          localmodels = "-v " + default_args['localmodelsfolder'] + ":/root/.ollama:z"

      time.sleep(10)
      if os.environ['TSS'] == "1":       
          buf = "docker run -d -p {}:{} --net=host --gpus all -v /var/run/docker.sock:/var/run/docker.sock:z {} --env OLLAMA_LOAD_TIMEOUT=30m0s --env PORT={} --env TSS=1 --env GPU=1 --env COLLECTION={} --env WEB_CONCURRENCY={} --env CUDA_VISIBLE_DEVICES={} --env TOKENIZERS_PARALLELISM=false --env temperature={} --env LLAMAMODEL=\"{}\" --env mainembedding=\"{}\" --env OLLAMASERVERPORT=\"{}\" {}".format(mainport,mainport,localmodels,mainport,collection,concurrency,cuda,temperature,mainmodel,mainembedding,ollamaserver,ollamacontainername)
      else:
          buf = "docker run -d -p {}:{} --net=host --gpus all -v /var/run/docker.sock:/var/run/docker.sock:z {} --env OLLAMA_LOAD_TIMEOUT=30m0s --env PORT={} --env TSS=0 --env GPU=1 --env COLLECTION={} --env WEB_CONCURRENCY={} --env CUDA_VISIBLE_DEVICES={} --env TOKENIZERS_PARALLELISM=false --env temperature={} --env LLAMAMODEL=\"{}\" --env mainembedding=\"{}\" --env OLLAMASERVERPORT=\"{}\" {}".format(mainport,mainport,localmodels,mainport,collection,concurrency,cuda,temperature,mainmodel,mainembedding,ollamaserver,ollamacontainername)


      if stopcontainers() == 1:
        return 1,buf,mainmodel,mainembedding
         
      v=subprocess.call(buf, shell=True)
      print("INFO STEP 9b: Ollama container.  Here is the run command: {}, v={}".format(buf,v))
      tsslogging.locallogs("INFO", "STEP 9b: Ollama container.  Here is the run command: {}, v={}".format(buf,v))

      return v,buf,mainmodel,mainembedding
 

def producegpttokafka(value,maintopic):
     inputbuf=value.strip()
     topicid=int(default_args['topicid'])
     producerid=default_args['producerid']
     identifier = default_args['identifier']

     # Add a 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic
     delay=default_args['delay']
     enabletls=default_args['enabletls']

     inputbuf=cleanstringjson(inputbuf)
     

     try:
        result=maadstml.viperproducetotopic(VIPERTOKEN,VIPERHOST,VIPERPORT,maintopic,producerid,enabletls,delay,'','', '',0,inputbuf,'',
                                            topicid,identifier)
        print(result)
     except Exception as e:
        print("ERROR:",e)

def consumefromtopic(maintopic):

      rollbackoffsets = int(default_args['rollbackoffset'])
      enabletls = int(default_args['enabletls'])
      consumerid=default_args['consumerid']
      companyname=default_args['companyname']
      offset = int(default_args['offset'])
      brokerhost = default_args['brokerhost']
      brokerport = int(default_args['brokerport'])
      microserviceid = default_args['microserviceid']
      topicid = default_args['topicid']
      preprocesstype = default_args['preprocesstype']
      delay = int(default_args['delay'])
      partition = int(default_args['partition'])

      print("before viperconsume",VIPERHOST,VIPERPORT,maintopic)
      result=maadstml.viperconsumefromtopic(VIPERTOKEN,VIPERHOST,VIPERPORT,maintopic,
                  consumerid,companyname,partition,enabletls,delay,
                  offset, brokerhost,brokerport,microserviceid,
                  topicid,rollbackoffsets,preprocesstype)
      return result
                

def windowname(wtype,sname,dagname):
    randomNumber = random.randrange(10, 9999)
    wn = "python-{}-{}-{},{}".format(wtype,randomNumber,sname,dagname)
    with open("/tmux/pythonwindows_{}.txt".format(sname), 'a', encoding='utf-8') as file:
      file.writelines("{}\n".format(wn))

    return wn

############# Get the real-time data from the data streams #########################
def getjsonsfromtopics(topics):

    print("in getjsonsfromtopics==",topics)

    topicsarr = topics.split("->>")
    topicjsons = []
           
    for t in topicsarr:
      t=t.strip()
      t2 = t.split("<<-")[0].strip()
      try:
        jsonvalue=consumefromtopic(t2)
      except Exception as e:
        print("error=",e)
      topicjsons.append(jsonvalue)

    return topicjsons


def extract_hyperpredictiondata(hjson):

    print("in extract")

    hyper_json = json.loads(hjson)
    hnum=0
    pt=""
    pv=""
    mainuid=""
    jbufs = ""

    if len(hyper_json['streamtopicdetails']['topicreads']) == 0:
     return ""

    for item in hyper_json['streamtopicdetails']['topicreads']:
        jbuf = ""

        if "preprocesstype" in item:
           ptypes = item['preprocesstype']
           pt = ptypes
           iden = item['identifier']
           idenarr = iden.split("~")
           pv = idenarr[0]
           hyperprediction = str(item['hyperprediction'])
           hnum=round(float(hyperprediction))

        if "islogistic" in item:
           pv="machine learning"
           if item['islogistic'] == "1":
              pt = "probability prediction" 
              hyperprediction = str(item['hyperprediction'])
              hnum = round(float(hyperprediction)*100)             
           else:
              hyperprediction = str(item['hyperprediction'])
              hnum = round(float(hyperprediction))
              pt = "prediction"


        if "identifier" in item:
            iden = item['identifier']
            idenarr = iden.split("~")
            mainuid = idenarr[-1]
            mainuid = mainuid.split("=")[1]
 

        jbuf = '{"hp":' + str(hnum) + ',"pt":"' + pt + '", "pv":"' + pv + '", "uid":"' + mainuid + '"}'
        jbufs = jbufs + jbuf +","
 

    hliststr = "[" + jbufs[:-1] + "]"
    hliststr=re.sub(r'[\n\r]+', '', hliststr)
    hliststr = hliststr.translate({ord('\n'): None, ord('\r'): None})
    print("hliststr==",hliststr)
    return hliststr

def checkjson(cjson):

    model = default_args['ollama-model']
    temperature = float(default_args['temperature'])
    embeddingmodel = default_args['embedding']

    cjson = cjson.strip()
    try:
     checkedjson = json.loads(cjson)  # check to see if json loads - if not its bad
    except Exception as e:
     print("Json error=",e)
     if cjson[-1] != '}':
        if "Model" not in cjson and "Embedding" not in cjson and "Temperature" not in cjson: 
          cjson = cjson +'","Model": "' + model + '","Embedding":"' + embeddingmodel + '", "Temperature":"' + str(temperature) +'"}'
        else:
          cjson = cjson + '"}'
              
     elif cjson[-2] != '"':
        if "Model" not in cjson and "Embedding" not in cjson and "Temperature" not in cjson:
          cjson = cjson[:-1] +'","Model": "' + model + '","Embedding":"' + embeddingmodel + '", "Temperature":"' + str(temperature) +'"}'
        else:
          cjson = cjson[:-1] + '"}'

     cjson = repair_json(cjson, skip_json_loads=True )
     pass
     # bad json

    return cjson


def agentquerytopics(usertopics,topicjsons,llm):
    topicsarr = usertopics.split("->>")
    bufresponse = ""
    bufarr = []
    agenttopic = default_args['agenttopic']

    model = default_args['ollama-model']  
    temperature = float(default_args['temperature'])
    embeddingmodel = default_args['embedding']

    md = model.split(",")
    model=md[0]
     
    if len(topicsarr) == 0:
        print("No topics data")
        return "",""
        
    responses = []
    for t,mainjson in zip(topicsarr,topicjsons):
      t=t.strip()
      t2  = t.split("<<-")
      mainjson=mainjson.lower()
      if "hyperprediction" in mainjson:
         mainjson=extract_hyperpredictiondata(mainjson)
         if mainjson == "":
           continue
  
      if "<<data>>" in t2[1]:
         query_str=t2[1]
         query_str = query_str.replace("<<data>>", f"{mainjson}")
         print("query_string====",query_str)


    # Invoking with a string
      print("------before llm invoke===")
      response = llm.invoke(query_str)
      response=str(response.content)
      
      prompt=cleanstring(t2[1].strip())

      response=cleanstring(response)
      response=response.replace(";",",").replace(":","").replace("'","").replace('"',"")
      
      bufresponse  = '{"Date": "' + str(datetime.now(timezone.utc)) + '","Agent_Name": "Topic_Agent", "Topic": "'+t2[0].strip()+'","Prompt":"' + prompt + '","Response": "' + response.strip() + '","Model": "' + model + '","Embedding":"' + embeddingmodel + '", "Temperature":"' + str(temperature) +'"}'
      bufresponse=checkjson(bufresponse)
      print("======bufresponse====",bufresponse)
      bufarr.append(bufresponse)
            
      producegpttokafka(bufresponse,agenttopic)
      
      responses.append(response)      
    
    return responses,bufarr

def teamleadqueryengine(tml_text_engine):
    bufresponse = ""

    model = default_args['ollama-model']
    md = model.split(",")
    if len(md)>1:
      model=md[1]

    temperature = float(default_args['temperature'])
    embeddingmodel = default_args['embedding']

    teamleadprompt = teamleadprompt.replace(";"," ")
    response = tml_text_engine.query(teamleadprompt )
    response=str(response)
#    print("team repsose = ", response)
    prompt=cleanstring(teamleadprompt.strip())
    response=cleanstring(response.strip())
    response=response.replace(";",",").replace(":","").replace('"',"").replace("'","")
    bufresponse  = '{"Date": "' + str(datetime.now(timezone.utc)) + '","Agent_Name": "Team_Lead_Agent", "Topic": "'+default_args['teamlead_topic'] +'","Prompt":"' + prompt + '","Response": "' + response.strip() + '","Model": "' + model + '","Embedding":"' + embeddingmodel + '", "Temperature":"' + str(temperature) +'"}'
    bufresponse=checkjson(bufresponse)

    producegpttokafka(bufresponse,default_args['teamlead_topic'])

    return response,bufresponse

################ Create Supervisor

def createactionagents(llm,sname):
    print("in createactionagents")
    repo=tsslogging.getrepo()
    
    agents=[]
    filepath=f"/{repo}/tml-airflow/dags/tml-solutions/{sname}/agenttools.py"
    print("filepath===",filepath)
    module_name = "agenttools"
    
    spec = importlib.util.spec_from_file_location(module_name, filepath)    
    dynamic_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dynamic_module)
  
    maintools=default_args['agenttoolfunctions'].strip()
    funcname=maintools.split("->>")
 
    for f in funcname:
       if len(f)>2:
         f=f.strip()
         fname=f.split("<<-")[0]         
         print(fname)
         func_objects = []
         func_object = getattr(dynamic_module, fname)                
         func_objects.append(func_object)
                  
         aname=f.split("<<-")[1]
         aprompt=f.split("<<-")[2]
                  
         agent = create_react_agent(
            model=llm,
            tools=func_objects,
            name=aname,
            prompt=aprompt
            
         )
         agents.append(agent)
    return agents


def createasupervisor(agents,supervisorprompt,llm):
    print("in createasupervisor==",supervisorprompt)

    supervisorprompt = supervisorprompt.replace(";"," ")
 
    workflow = create_supervisor(
      agents,
      model=llm,
      prompt=supervisorprompt
    )
# Compile and run
    app = workflow.compile()
    return app

def invokesupervisor(app,maincontent):
   
    model = default_args['ollama-model']
    md = model.split(",")
    if len(md)>2:
      model=md[2]

    temperature = float(default_args['temperature'])
    embeddingmodel = default_args['embedding']
    funcname = default_args['agenttoolfunctions']
    funcname = funcname.replace(";","==")
    maincontent=maincontent.replace(";",",")
 
    try:    
        supervisormaincontent ="""
          Here is the team lead's assessment: {}.  Based on the Team Lead's assessment what is the appropriate action.
        """.format(maincontent) 
        
        result = app.invoke({
          "messages": [
              {
                  "role": "user",
                  "content": supervisormaincontent
              }
          ]
        })
    except Exception as e:
      print("WARN STEP 9b: Agentic AI: unable to create supervisor agent")
      tsslogging.locallogs("WARN", "STEP 9b: Agentic AI: unable to create supervisor agent")
      return "error","error"

    lastmessage=""
    for chunk in app.stream(
        input=result,
        stream_mode="values",):
        if chunk["messages"][-1].content != "":
          lastmessage=chunk["messages"][-1].content
    
    lastmessage=str(lastmessage)    
    lastmessage=cleanstring(lastmessage.strip())
    lastmessage=lastmessage.replace(";",",").replace("'","").replace('"',"").replace(":","")
    bufresponse  = '{"Date": "' + str(datetime.now(timezone.utc)) + '","Agent_Name": "Supervisor_Agent", "Topic": "' + default_args['supervisor_topic'] + '","Prompt":"' + supervisormaincontent + '","Response": "' + lastmessage.strip() + '","Model": "' + model + '","Embedding":"' + embeddingmodel + '", "Temperature":"' + str(temperature) +'"}'
        
    
    mainjson=[]
    mainstr=""
    for m in result["messages"]:
      mainjson.append(pprint.pformat(m))
     # mainstr = mainstr + json.dumps(str(m.json)) + ","
            
    mainjson=json.dumps({"supervisor_workflow_invocation": mainjson})
    mainjson=mainjson[:-1] + ",\"funcname\":" + json.dumps(funcname)+",\"supervisorprompt\":\""+supervisormaincontent+"\"}"
    mainjson=cleanstring(mainjson)
    mainjson=checkjson(mainjson)
   
    try:
      #print(mainjson)
      producegpttokafka(mainjson,default_args['supervisor_topic'])
        
      return mainjson,bufresponse
    except Exception as e:
      print("ERROR: invalid json")  
      return "error","error"

def formatcompletejson(bufresponses,teamlead_response,lastmessage):

    bufresponses = " ".join(str(bufresponses).splitlines())
    teamlead_response = " ".join(str(teamlead_response).splitlines())
    lastmessage = " ".join(str(lastmessage).splitlines())
   
    bufresponses = " ".join(bufresponses.split(" "))
    teamlead_response = " ".join(teamlead_response.split(" "))
    lastmessage = " ".join(lastmessage.split(" "))

    bufresponses = bufresponses.replace("'","").replace("\n"," ").replace("\\n"," ").replace("\t", " ").replace("\r"," ").replace("#","").strip()
    teamlead_response = teamlead_response.replace("'","").replace("\n"," ").replace("\\n"," ").replace("\t", " ").replace("\r", " ").replace("#","").strip()
    lastmessage = lastmessage.replace("'","").replace("\n"," ").replace("\t", " ").replace("\\n"," ").replace("\r"," ").replace("#","").strip()

    print("bufresponses===",bufresponses)
    print("teambuf===",teambuf)
    print("supbuf===",supbuf)
  
    # check if valid 
    try:
      jvalid=json.loads(bufresponses)
    except Exception as e:
      bufresponses = '[{"Status": "no data found", "Model": "na", "Embedding": "na", "Temperature": "na", "Prompt": "na", "Response": "no data found", "Date": "' + str(datetime.now(timezone.utc)) + '", "Agent_Name": "", "Topic": "na"}]'
      
    try:
      jvalid=json.loads(teamlead_response)
    except Exception as e:
      teamlead_response =  '{"Status": "no data found", "Model": "na", "Embedding": "na", "Temperature": "na", "Prompt": "na", "Response": "no data found", "Date": "' + str(datetime.now(timezone.utc)) + '", "Agent_Name": "Team Lead agent", "Topic": "na"}'

    try:
      jvalid=json.loads(lastmessage)
    except Exception as e:
      lastmessage = '{"Status": "no data found", "Model": "na", "Embedding": "na", "Temperature": "na", "Prompt": "na", "Response": "Error - likely a Tool could not be run. Check your tools.", "Date": "' + str(datetime.now(timezone.utc)) + '", "Agent_Name": "Supervisor agent", "Topic": "na"}'


    mainjson = bufresponses[:-1] + "," + teamlead_response + "," + lastmessage + "]"
    mainjson = " ".join(mainjson.split())
    mainjson = " ".join(mainjson.splitlines())

    mainjson=re.sub(r'[\n\r]+', '', mainjson)

    mainjson = mainjson.replace("'","").replace("\n"," ").replace("\\n"," ").replace("\t", " ").replace("\r"," ").replace("\\r"," ").strip()

    mainjson = mainjson.translate({ord('\n'): None, ord('\r'): None})
    print("mainjson======",mainjson)

    return mainjson    

def startagenticai(**context):
       sd = context['dag'].dag_id
       sname=context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_solutionname".format(sd))
       pname=context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_projectname".format(sd))

       if 'step9brollbackoffset' in os.environ:
          if os.environ['step9brollbackoffset'] != '':
            default_args['rollbackoffset'] = os.environ['step9brollbackoffset']
 
       if 'step9bollama-model' in os.environ:
          if os.environ['step9bollama-model'] != '':
            default_args['ollama-model'] = os.environ['step9bollama-model']
       if 'step9bdeletevectordbcount' in os.environ:
          if os.environ['step9bdeletevectordbcount'] != '':
            default_args['deletevectordbcount'] = os.environ['step9bdeletevectordbcount']

       if 'step9bvectordbpath' in os.environ:
          if os.environ['step9bvectordbpath'] != '':
            default_args['vectordbpath'] = os.environ['step9bvectordbpath']

       if 'step9btemperature' in os.environ:
          if os.environ['step9btemperature'] != '':
            default_args['temperature'] = os.environ['step9btemperature']

       if 'step9bvectordbcollectionname' in os.environ:
          if os.environ['step9bvectordbcollectionname'] != '':
            default_args['vectordbcollectionname'] = os.environ['step9bvectordbcollectionname']
       if 'step9bollamacontainername' in os.environ:
          if os.environ['step9bollamacontainername'] != '':
            default_args['ollamacontainername'] = os.environ['step9bollamacontainername']
       if 'step9bCUDA_VISIBLE_DEVICES' in os.environ:
          if os.environ['step9bCUDA_VISIBLE_DEVICES'] != '':
            default_args['CUDA_VISIBLE_DEVICES'] = os.environ['step9bCUDA_VISIBLE_DEVICES']
           
       if 'step9bmainip' in os.environ:
          if os.environ['step9bmainip'] != '':
            default_args['mainip'] = os.environ['step9bmainip']
       if 'step9bmainport' in os.environ:
          if os.environ['step9bmainport'] != '':
            default_args['mainport'] = os.environ['step9bmainport']

       if 'step9bembedding' in os.environ:
          if os.environ['step9bembedding'] != '':
            default_args['embedding'] = os.environ['step9bembedding']
       if 'step9bagents_topic_prompt' in os.environ:
          if os.environ['step9bagents_topic_prompt'] != '':
            default_args['agents_topic_prompt'] = os.environ['step9bagents_topic_prompt']

       if 'step9bagenttopic' in os.environ:
          if os.environ['step9bagenttopic'] != '':
            default_args['agenttopic'] = os.environ['step9bagenttopic']

       if 'step9bteamlead_topic' in os.environ:
          if os.environ['step9bteamlead_topic'] != '':
            default_args['teamlead_topic'] = os.environ['step9bteamlead_topic']
       if 'step9bteamleadprompt' in os.environ:
          if os.environ['step9bteamleadprompt'] != '':
            default_args['teamleadprompt'] = os.environ['step9bteamleadprompt']
       if 'step9bsupervisor_topic' in os.environ:
          if os.environ['step9bsupervisor_topic'] != '':
            default_args['supervisor_topic'] = os.environ['step9bsupervisor_topic']
       if 'step9bagenttoolfunctions' in os.environ:
          if os.environ['step9bagenttoolfunctions'] != '':
            default_args['agenttoolfunctions'] = os.environ['step9bagenttoolfunctions']
       if 'step9bagent_team_supervisor_topic' in os.environ:
          if os.environ['step9bagent_team_supervisor_topic'] != '':
            default_args['agent_team_supervisor_topic'] = os.environ['step9bagent_team_supervisor_topic']
       if 'step9bcontextwindow' in os.environ:
          if os.environ['step9bcontextwindow'] != '':
            default_args['contextwindow'] = os.environ['step9bcontextwindow']

       if 'step9blocalmodelsfolder' in os.environ:
          if os.environ['step9blocalmodelsfolder'] != '':
            default_args['localmodelsfolder'] = os.environ['step9blocalmodelsfolder']

       VIPERTOKEN = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERTOKEN".format(sname))
       VIPERHOST = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERHOSTPREPROCESSAGENTICAI".format(sname))
       VIPERPORT = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERPORTPREPROCESSAGENTICAI".format(sname))
       HTTPADDR = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_HTTPADDR".format(sname))


       ti = context['task_instance']
       ti.xcom_push(key="{}_rollbackoffset".format(sname), value="_{}".format(default_args['rollbackoffset']))
       ti.xcom_push(key="{}_ollama-model".format(sname), value=default_args['ollama-model'])
       ti.xcom_push(key="{}_deletevectordbcount".format(sname), value="_{}".format(default_args['deletevectordbcount']))
       ti.xcom_push(key="{}_vectordbpath".format(sname), value="{}".format(default_args['vectordbpath']))
       ti.xcom_push(key="{}_temperature".format(sname), value="_{}".format(default_args['temperature']))
       ti.xcom_push(key="{}_topicid".format(sname), value="_{}".format(default_args['topicid']))
       ti.xcom_push(key="{}_enabletls".format(sname), value="_{}".format(default_args['enabletls']))
       ti.xcom_push(key="{}_partition".format(sname), value="_{}".format(default_args['partition']))
       ti.xcom_push(key="{}_vectordbcollectionname".format(sname), value=default_args['vectordbcollectionname'])
       ti.xcom_push(key="{}_ollamacontainername".format(sname), value=default_args['ollamacontainername'])
       ti.xcom_push(key="{}_mainip".format(sname), value=default_args['mainip'])
       ti.xcom_push(key="{}_mainport".format(sname), value="_{}".format(default_args['mainport']))
       ti.xcom_push(key="{}_embedding".format(sname), value=default_args['embedding'])
       ti.xcom_push(key="{}_agents_topic_prompt".format(sname), value=default_args['agents_topic_prompt'])
       ti.xcom_push(key="{}_teamlead_topic".format(sname), value=default_args['teamlead_topic'])
       ti.xcom_push(key="{}_teamleadprompt".format(sname), value=default_args['teamleadprompt'])
       ti.xcom_push(key="{}_supervisor_topic".format(sname), value=default_args['supervisor_topic'])
       ti.xcom_push(key="{}_supervisorprompt".format(sname), value=default_args['supervisorprompt'])

       at=default_args['agenttoolfunctions']
       at=at.replace(SMTP_PASSWORD,'')

       ti.xcom_push(key="{}_agenttoolfunctions".format(sname), value=at)
  
       ti.xcom_push(key="{}_agent_team_supervisor_topic".format(sname), value=default_args['agent_team_supervisor_topic'])        
       ti.xcom_push(key="{}_concurrency".format(sname), value="_{}".format(default_args['concurrency']))
       ti.xcom_push(key="{}_cuda".format(sname), value="_{}".format(default_args['CUDA_VISIBLE_DEVICES']))
       ti.xcom_push(key="{}_agenttopic".format(sname), value="{}".format(default_args['agenttopic']))

       ti.xcom_push(key="{}_contextwindow".format(sname), value="_{}".format(default_args['contextwindow']))

       ti.xcom_push(key="{}_localmodelsfolder".format(sname), value="{}".format(default_args['localmodelsfolder']))

       repo=tsslogging.getrepo()
       if sname != '_mysolution_':
        fullpath="/{}/tml-airflow/dags/tml-solutions/{}/{}".format(repo,pname,os.path.basename(__file__))
       else:
         fullpath="/{}/tml-airflow/dags/{}".format(repo,os.path.basename(__file__))
 
       wn = windowname('agenticai',sname,sd)
       subprocess.run(["tmux", "new", "-d", "-s", "{}".format(wn)])
       subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "cd /Viper-preprocess-agenticai", "ENTER"])
       subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "python {} 1 {} {}{} {} \"{}\" \"{}\" \"{}\" \"{}\" \"{}\" {} {} {} {} \"{}\" \"{}\" {} {} \"{}\" \"{}\" \"{}\" \"{}\" \"{}\" \"{}\" \"{}\" \"{}\" \"{}\" \"{}\" {} \"{}\" \"{}\"".format(fullpath,
                       VIPERTOKEN, HTTPADDR, VIPERHOST, VIPERPORT[1:],
                       default_args['rollbackoffset'],default_args['ollama-model'],default_args['deletevectordbcount'],default_args['vectordbpath'],
                       default_args['temperature'],default_args['topicid'],default_args['enabletls'],
                       default_args['partition'], default_args['vectordbcollectionname'], default_args['ollamacontainername'], 
                       default_args['mainip'],default_args['mainport'],default_args['embedding'],
                       default_args['agents_topic_prompt'],default_args['teamlead_topic'],default_args['teamleadprompt'],
                       default_args['supervisor_topic'],default_args['supervisorprompt'],default_args['agenttoolfunctions'],
                       default_args['agent_team_supervisor_topic'],default_args['concurrency'],default_args['CUDA_VISIBLE_DEVICES'],
                       pname,default_args['contextwindow'],default_args['localmodelsfolder'],default_args['agenttopic']),"ENTER"])

if __name__ == '__main__':
    if len(sys.argv) > 1:
       if sys.argv[1] == "1":
        repo=tsslogging.getrepo()      

        VIPERTOKEN = sys.argv[2]
        VIPERHOST = sys.argv[3]
        VIPERPORT = sys.argv[4]
        
        rollbackoffset =  sys.argv[5]
        ollamamodel =  sys.argv[6]
        deletevectordb =  sys.argv[7]
        vectordbpath=sys.argv[8]
        temperature=sys.argv[9]
        
        topicid=sys.argv[10]
        enabletls=sys.argv[11]
        
        partition=sys.argv[12]
        vectordbcollectionname=sys.argv[13]
        ollamacontainername=sys.argv[14]
        mainip=sys.argv[15]
        mainport=sys.argv[16]
        embedding=sys.argv[17]
        agents_topic_prompt=sys.argv[18]
        teamlead_topic=sys.argv[19]
        teamleadprompt=sys.argv[20]
        supervisor_topic=sys.argv[21]
        supervisorprompt=sys.argv[22]
        agenttoolfunctions=sys.argv[23]

        agent_team_supervisor_topic=sys.argv[24]
        concurrency=sys.argv[25]        
        cuda =  sys.argv[26]
        pname = sys.argv[27]
        contextwindow = sys.argv[28]
        localmodelsfolder = sys.argv[29]

        agenttopic = sys.argv[30]

       default_args['rollbackoffset']=rollbackoffset
       default_args['ollama-model']=ollamamodel
       default_args['deletevectordbcount']=deletevectordb
       default_args['vectordbpath']=vectordbpath
       default_args['temperature']=temperature
       default_args['topicid']=topicid
       default_args['enabletls']=enabletls
       default_args['partition']=partition
       default_args['vectordbcollectionname']=vectordbcollectionname
       default_args['ollamacontainername']=ollamacontainername
       default_args['mainip']=mainip
       default_args['mainport']=mainport
       default_args['embedding']=embedding
       default_args['agents_topic_prompt']=agents_topic_prompt
       default_args['teamlead_topic']=teamlead_topic
       default_args['teamleadprompt']=teamleadprompt
       default_args['supervisor_topic']=supervisor_topic
       default_args['supervisorprompt']=supervisorprompt
       default_args['agenttoolfunctions']=agenttoolfunctions
       default_args['agent_team_supervisor_topic']=agent_team_supervisor_topic
       default_args['concurrency']=concurrency
       default_args['CUDA_VISIBLE_DEVICES']=cuda
       default_args['contextwindow']=contextwindow
       default_args['localmodelsfolder']=localmodelsfolder
       default_args['agenttopic']=agenttopic

    if "KUBE" not in os.environ:          
         
          tsslogging.locallogs("INFO", "STEP 9b: Starting Ollama container")
          v,buf,mainmodel,mainembedding=startpgptcontainer()
          if v==1:
            tsslogging.locallogs("WARN", "STEP 9b: There seems to be an issue starting the Ollama container.  Here is the run command - try to run it nanually for testing: {}".format(buf))
          else:
            tsslogging.locallogs("INFO", "STEP 9b: Success starting Ollama container.  Here is the run command: {}".format(buf))

          time.sleep(10)  # wait for containers to start
    elif  os.environ["KUBE"] == "0":
         
          tsslogging.locallogs("INFO", "STEP 9b: Starting ollama server")
          v,buf,mainmodel,mainembedding=startpgptcontainer()
          if v==1:
            tsslogging.locallogs("WARN", "STEP 9b: There seems to be an issue starting the Ollama container.  Here is the run command - try to run it nanually for testing: {}".format(buf))
          else:
            tsslogging.locallogs("INFO", "STEP 9b: Success starting Agentic AI.  Here is the run command: {}".format(buf))

          time.sleep(10)  # wait for containers to start         
    else:  
          tsslogging.locallogs("INFO", "STEP 9b: [KUBERNETES] Starting Agentic AI - LOOKS LIKE THIS IS RUNNING IN KUBERNETES")
          tsslogging.locallogs("INFO", "STEP 9b: [KUBERNETES] Make sure you have applied the Agentic AI YAML files and have the agentic AI Pod running")

    count=0

        # create the Supervisor and kick off action
   
#    llmstatus = get_loaded_models()
 #   print("llmstatus==",llmstatus,pname)
   
    mainmodels=default_args['ollama-model']
   
    models = mainmodels.split(",")  #models must be agent,teamlead,supervisor
    embedding=None

    modelsarr = []
    for m in models:
       llmstatus = get_loaded_models()
       checkforloadedmodels(m)
       print("llmstatus==",llmstatus,pname)
       llm,embedding=setollama(m.strip())
       modelsarr.append(llm)


    if len(modelsarr) >2:
      #try:
      actionagents=createactionagents(modelsarr[2],pname)
      supervisorprompt = default_args['supervisorprompt']
      try:
        app=createasupervisor(actionagents,supervisorprompt,modelsarr[2])
      except Exception as e:
        print("Error=",e)
        tsslogging.locallogs("WARN", "STEP 9b unable to create agents {}".format(e))
    else:
       tsslogging.locallogs("WARN","STEP 9b unable to load LLM - Aborting") 
       print("WARN", "STEP 9b unable to load LLM - Aborting")
       exit(0)

    deletevectordbcnt=0
    while True:
         deletevectordbcnt +=1   
         try:
            agent_topics = default_args['agents_topic_prompt'] 
            topicjsons=getjsonsfromtopics(agent_topics)
            responses,bufresponses=agentquerytopics(agent_topics,topicjsons,modelsarr[0])
         #try:        
            tml_text_engine,deletevectordbcnt=loadtextdataintovectordb(responses,deletevectordbcnt,modelsarr[1])
            teamlead_response,teambuf=teamleadqueryengine(tml_text_engine)                  
            mainjson,supbuf=invokesupervisor(app,teamlead_response)
            complete=formatcompletejson(bufresponses,teambuf,supbuf)

            if default_args['agent_team_supervisor_topic']!='':
              producegpttokafka(complete,default_args['agent_team_supervisor_topic'])

            time.sleep(1)
         except Exception as e:
          print("Error=",e)              
          if count == 0:
            tsslogging.locallogs("ERROR", "STEP 9b: Agentic AI Step 9b DAG in {} {}  Aborting after 10 consecutive errors.".format(os.path.basename(__file__),e))
            tsslogging.tsslogit("PrivateGPT Step 9b DAG in {} {} Aborting after 10 consecutive errors.".format(os.path.basename(__file__),e), "ERROR" )
            tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")
          time.sleep(5)
          count = count + 1
          if count > 600:
            break
