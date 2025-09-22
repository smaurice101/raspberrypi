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
docidstrarr = []

sys.dont_write_bytecode = True

######################################################USER CHOSEN PARAMETERS ###########################################################
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
 'agents_topic_prompt' : """
<consumefrom - topic agent will monitor:prompt you want for the agent to answer>
""", # <topic agent will monitor:prompt you want for the agent>
 'teamlead_topic' : '', # Enter the team lead topic - all team lead responses will be written to this topic
 'teamleadprompt' : """
Enter the prompt for the Team lead agent
""", # Enter the team lead prompt 
 'supervisor_topic' : '', # Enter the supervisor topic - all supervisor responses will be written to this topic
 'supervisorprompt' : '', # Enter the supervisor prompt 
 'agenttoolfunctions' : """
tool_function:agent_name:system_prompt,tool_function2:agent_name2:sysemt_prompt2,....
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
 'ollama-model': 'llama3.2',
 'deletevectordbcount': '10',
 'vectordbpath': '/rawdata/vectordb'
}

############################################################### DO NOT MODIFY BELOW ####################################################

VIPERTOKEN=""
VIPERHOST=""
VIPERPORT=""
HTTPADDR=""
mainproducerid = default_args['producerid']

def setollama():
    ###############  Ollama Model #################################
    model=default_args['ollama-model']
    temperature=int(default_args['temperature'])
    embeddingmodel=default_args['embedding'] #"nomic-embed-text"
    mainip=default_args['mainip']
    mainport=default_args['mainport']

    if 'KUBE' in os.environ:
      if os.environ['KUBE'] == "1":
         default_args['mainip']="ollama-service"
         mainip=default_args['mainip']

    try:
      llm = ChatOllama(model=model, base_url=mainip+":"+mainport, temperature=temperature)
    except Exception as e:
      print("ERROR STEP 9b: Cannot load Ollama LLM model '{}' not found.".format(model))
      tsslogging.locallogs("ERROR", "STEP 9b: Cannot load Ollama LLM model '{}' not found.".format(model))
      return "" 

    try:
      ollama_emb = OllamaEmbedding(
        base_url=mainip+":"+str(mainport),
        model_name=embeddingmodel
      )
    except Exception as e:
      print("ERROR STEP 9b: Cannot load Ollama embedding '{}' not found.".format(embeddingmodel))
      tsslogging.locallogs("ERROR", "STEP 9b: Cannot load Ollama embedding '{}' not found.".format(embeddingmodel))
      return "" 

    Settings.embed_model = ollama_emb
    Settings.llm = llm

    return llm,ollama_emb

def remove_escape_sequences(string):
    return string.encode('utf-8').decode('unicode_escape')

def cleanstring(mainstr):

    mainstr = mainstr.replace('"',"").replace('`',"").replace("\n","").replace("\\n","").replace("\t","").replace("\\t","").replace("\r","").replace("\\r","").replace("\\*","").replace("\\ ","").replace("\\\\","\\").replace("\\1","1").replace("\\2","2").replace("\\3","3").replace("\\4","4").replace("\\5","5").replace("\\6","6").replace("\\7","7").replace("\\8","8").replace("\\9","9")

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
def loadtextdataintovectordb(responses,deletevectordbcnt):

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
    
    tml_text_engine = tml_index.as_query_engine(similarity_top_k=3)

    return tml_text_engine,deletevectordbcnt
            
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
            print(buf)
            subprocess.call(buf, shell=True)
   if cfound==0:
      print("INFO STEP 9b: Ollama container {} not found.  It may need to be pulled.".format(ollamacontainername))
      tsslogging.locallogs("WARN", "STEP 9b: Ollama container not found. It may need to be pulled if it does not start: docker pull {}".format(ollamacontainername))



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
      mainhost = default_args['mainhost']

      ollamaserver = mainhost + ":" + str(mainport)
      stopcontainers()
      time.sleep(10)
      if os.environ['TSS'] == "1":       
          buf = "docker run -d -p {}:{} --net=host --gpus all -v /var/run/docker.sock:/var/run/docker.sock:z --env PORT={} --env TSS=1 --env GPU=1 --env COLLECTION={} --env WEB_CONCURRENCY={} --env CUDA_VISIBLE_DEVICES={} --env TOKENIZERS_PARALLELISM=false --env temperature={} --env vectorsearchtype=\"{}\" --env contextwindowsize={} --env vectordimension={} --env LLAMAMODEL=\"{}\" --env mainembedding=\"{}\" --env OLLAMASERVERPORT=\"{}\" {}".format(pgptport,pgptport,pgptport,collection,concurrency,cuda,temperature,vectorsearchtype,cw,vectordimension,mainmodel,mainembedding,ollamaserver,ollamacontainername)
      else:
          buf = "docker run -d -p {}:{} --net=host --gpus all -v /var/run/docker.sock:/var/run/docker.sock:z --env PORT={} --env TSS=0 --env GPU=1 --env COLLECTION={} --env WEB_CONCURRENCY={} --env CUDA_VISIBLE_DEVICES={} --env TOKENIZERS_PARALLELISM=false --env temperature={} --env vectorsearchtype=\"{}\" --env contextwindowsize={} --env vectordimension={}  --env LLAMAMODEL=\"{}\" --env mainembedding=\"{}\" --env OLLAMASERVERPORT=\"{}\" {}".format(pgptport,pgptport,pgptport,collection,concurrency,cuda,temperature,vectorsearchtype,cw,vectordimension,mainmodel,mainembedding,ollamaserver,ollamacontainername)
         
      v=subprocess.call(buf, shell=True)
      print("INFO STEP 9b: Ollama container.  Here is the run command: {}, v={}".format(buf,v))
      tsslogging.locallogs("INFO", "STEP 9b: Ollama container.  Here is the run command: {}, v={}".format(buf,v))

      return v,buf,mainmodel,mainembedding
 

def producegpttokafka(value,maintopic):
     inputbuf=value
     topicid=int(default_args['topicid'])
     producerid=default_args['producerid']
     identifier = default_args['identifier']

     # Add a 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic
     delay=default_args['delay']
     enabletls=default_args['enabletls']

     try:
        result=maadstml.viperproducetotopic(VIPERTOKEN,VIPERHOST,VIPERPORT,maintopic,producerid,enabletls,delay,'','', '',0,inputbuf,'',
                                            topicid,identifier)
        print(result)
     except Exception as e:
        print("ERROR:",e)

def consumefromtopic(maintopic):
      #maintopic = default_args['consumefrom']
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

    topicsarr = topics.split(",")
    topicjsons = []
    
    for t in topicsarr:
      t2 = t.split(":")[0]
      jsonvalue=consumefromtopic(t2)
      topicjsons.append(jsonvalue)

    return topicjsons


def agentquerytopics(usertopics,topicjsons,llm):
    topicsarr = usertopics.split(",")
    bufresponse = ""
    bufarr = []
    
    if len(topicsarr) == 0:
        print("No topics data")
        return ""
        
    responses = []
    for t,mainjson in zip(topicsarr,topicjsons):
      t2  = t.split(":")
      #print("q========",q)
      query_str=t2[1]+ f". here is the JSON: {mainjson}"
      #print("query_string====",query_str)


    # Invoking with a string
      response = llm.invoke(query_str)
      response=response.content    
      prompt=cleanstring(t2[1].strip())
      response=cleanstring(response)
      bufresponse  = '{"Date": "' + str(datetime.now(timezone.utc)) + '","Topic_Agent": "'+t2[0].strip()+'","Prompt":"' + prompt + '","Response": "' + response.strip() + '","Model": "' + model + '","Embedding":"' + embeddingmodel + '", "Temperature":"' + str(temperature) +'"}'
      print(bufresponse)
      bufarr.append(bufresponse)
            
      producegpttokafka(bufresponse,t2[0].strip())
      
      responses.append(response)      
    
    return responses,bufarr

def teamleadqueryengine(tml_text_engine):
    bufresponse = ""

    response = tml_text_engine.query(teamleadprompt )
    response=str(response)
#    print("team repsose = ", response)
    prompt=cleanstring(teamleadprompt.strip())
    response=cleanstring(response.strip())
    bufresponse  = '{"Date": "' + str(datetime.now(timezone.utc)) + '","Team_Lead_Agent": "'+default_args['teamlead_topic'] +'","Prompt":"' + prompt + '","Response": "' + response.strip() + '","Model": "' + model + '","Embedding":"' + embeddingmodel + '", "Temperature":"' + str(temperature) +'"}'

    producegpttokafka(bufresponse,default_args['teamlead_topic'])

    return response,bufresponse

################ Create Supervisor

def createactionagents(llm):
    agents=[]
    dynamic_module = importlib.import_module("agenttools")

    for f in funcname:
      # print("f=====",f) 
       if len(f)>2:
         fname=f.split(":")[0]         
         fnamearr=fname.split(",")
         func_objects = []
         
         for fo in fnamearr:
          #print("fo----",fo)   
          func_object = getattr(dynamic_module, fo)                
          func_objects.append(func_object)
         
         aname=f.split(":")[1]
         aprompt=f.split(":")[2]
         
         print("info---:",fname,aname,aprompt)
     #    print("Tools===",func_object.name)
         
         agent = create_react_agent(
            model=llm,
            tools=func_objects,
            name=aname,
            prompt=aprompt
            
         )
         agents.append(agent)
    return agents


def createasupervisor(agents,supervisorprompt,llm):

    workflow = create_supervisor(
      agents,
      model=llm,
      prompt=supervisorprompt
    )
# Compile and run
    app = workflow.compile()
    return app

def invokesupervisor(app,maincontent):


    try:    
        supervisormaincontent ="""
          Here is the team lead's response: {}.  Generate an approprate action using one of the tools.
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
        
    lastmessage=cleanstring(lastmessage.strip())
    bufresponse  = '{"Date": "' + str(datetime.now(timezone.utc)) + '","Supervisor_Agent": "' + default_args['supervisor_topic'] + '","Prompt":"' + supervisormaincontent + '","Response": "' + lastmessage.strip() + '","Model": "' + model + '","Embedding":"' + embeddingmodel + '", "Temperature":"' + str(temperature) +'"}'
        
    
    mainjson=[]
    mainstr=""
    for m in result["messages"]:
      mainjson.append(pprint.pformat(m))
     # mainstr = mainstr + json.dumps(str(m.json)) + ","
            
    mainjson=json.dumps({"supervisor_workflow_invocation": mainjson})
    mainjson=mainjson[:-1] + ",\"funcname\":" + json.dumps(funcname)+",\"supervisorprompt\":\""+supervisormaincontent+"\"}"
    mainjson=cleanstring(mainjson)
    try:
      #print(mainjson)
      producegpttokafka(mainjson,default_args['supervisor_topic'])
        
      return mainjson,bufresponse
    except Exception as e:
      print("ERROR: invald json")  
      return "error","error"

def formatcompletejson(bufresponses,teamlead_response,lastmessage):

    mjson = '['

    for k in bufresponses:
        mjson = mjson + k + ","
    
    mjson = mjson + teamlead_response + ","
    mjson = mjson + str(lastmessage) + "]"

    return mjson    

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
       if 'CUDA_VISIBLE_DEVICES' in os.environ:
          if os.environ['CUDA_VISIBLE_DEVICES'] != '':
            default_args['CUDA_VISIBLE_DEVICES'] = os.environ['CUDA_VISIBLE_DEVICES']
           
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

       VIPERTOKEN = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERTOKEN".format(sname))
       VIPERHOST = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERHOSTPREPROCESSPGPT".format(sname))
       VIPERPORT = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERPORTPREPROCESSPGPT".format(sname))
       HTTPADDR = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_HTTPADDR".format(sname))


       ti = context['task_instance']
       ti.xcom_push(key="{}_rollbackoffset".format(sname), value=default_args['rollbackoffset'])
       ti.xcom_push(key="{}_ollama-model".format(sname), value=default_args['ollama-model'])
       ti.xcom_push(key="{}_deletevectordbcount".format(sname), value=default_args['deletevectordbcount'])
       ti.xcom_push(key="{}_vectordbpath".format(sname), value="_{}".format(default_args['vectordbpath']))
       ti.xcom_push(key="{}_temperature".format(sname), value="_{}".format(default_args['temperature']))
       ti.xcom_push(key="{}_topicid".format(sname), value="_{}".format(default_args['topicid']))
       ti.xcom_push(key="{}_enabletls".format(sname), value="_{}".format(default_args['enabletls']))
       ti.xcom_push(key="{}_partition".format(sname), value="_{}".format(default_args['partition']))
       ti.xcom_push(key="{}_vectordbcollectionname".format(sname), value=default_args['vectordbcollectionname'])
       ti.xcom_push(key="{}_ollamacontainername".format(sname), value=default_args['ollamacontainername'])
       ti.xcom_push(key="{}_mainip".format(sname), value=default_args['mainip'])
       ti.xcom_push(key="{}_mainport".format(sname), value=default_args['mainport'])
       ti.xcom_push(key="{}_embedding".format(sname), value=default_args['embedding'])
       ti.xcom_push(key="{}_agents_topic_prompt".format(sname), value=default_args['agents_topic_prompt'])
       ti.xcom_push(key="{}_teamlead_topic".format(sname), value=default_args['teamlead_topic'])
       ti.xcom_push(key="{}_teamleadprompt".format(sname), value=default_args['teamleadprompt'])
       ti.xcom_push(key="{}_supervisor_topic".format(sname), value=default_args['supervisor_topic'])
       ti.xcom_push(key="{}_supervisorprompt".format(sname), value=default_args['supervisorprompt'])
       ti.xcom_push(key="{}_agenttoolfunctions".format(sname), value=default_args['agenttoolfunctions'])
       ti.xcom_push(key="{}_agent_team_supervisor_topic".format(sname), value=default_args['agent_team_supervisor_topic'])        
       ti.xcom_push(key="{}_concurrency".format(sname), value="_{}".format(default_args['concurrency']))
       ti.xcom_push(key="{}_cuda".format(sname), value="_{}".format(default_args['CUDA_VISIBLE_DEVICES']))

       repo=tsslogging.getrepo()
       if sname != '_mysolution_':
        fullpath="/{}/tml-airflow/dags/tml-solutions/{}/{}".format(repo,pname,os.path.basename(__file__))
       else:
         fullpath="/{}/tml-airflow/dags/{}".format(repo,os.path.basename(__file__))
 
       wn = windowname('agenticai',sname,sd)
       subprocess.run(["tmux", "new", "-d", "-s", "{}".format(wn)])
       subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "cd /Viper-preprocess-agenticai", "ENTER"])
       subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "python {} 1 {} {}{} {} \"{}\" \"{}\" \"{}\" \"{}\" \"{}\" {} {} {} {} \"{}\" \"{}\" {} {} \"{}\" \"{}\" \"{}\" \"{}\" \"{}\" \"{}\" \"{}\" \"{}\" \"{}\"".format(fullpath,
                       VIPERTOKEN, HTTPADDR, VIPERHOST, VIPERPORT[1:],
                       default_args['rollbackoffset'],default_args['ollama-model'],default_args['deletevectordbcount'],default_args['vectordbpath'],
                       default_args['temperature'],default_args['topicid'],default_args['enabletls'],
                       default_args['partition'], default_args['vectordbcollectionname'], default_args['ollamacontainername'], 
                       default_args['mainip'],default_args['mainport'],default_args['embedding'],
                       default_args['agents_topic_prompt'],default_args['teamlead_topic'],default_args['teamleadprompt'],
                       default_args['supervisor_topic'],default_args['supervisorprompt'],default_args['agenttoolfunctions'],
                       default_args['agent_team_supervisor_topic'],default_args['concurrency'],default_args['CUDA_VISIBLE_DEVICES']),"ENTER"])

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
    llm,embedding=setollama()
    actionagents=createactionagents(llm)
    supervisorprompt = default_args['supervisorprompt']
    app=createasupervisor(actionagents,supervisorprompt,llm)

    deletevectordbcnt=0
 
    while True:
         deletevectordbcnt +=1   
         try:
            agent_topics = default_args['agents_topic_prompt'] 
            topicjsons=getjsonsfromtopics(agent_topics)

            responses,bufresponses=agentquerytopics(agent_topics,topicjsons,llm)

            tml_text_engine,deletevectordbcnt=loadtextdataintovectordb(responses,deletevectordbcnt)

            teamlead_response,teambuf=teamleadqueryengine(tml_text_engine)
                  
            mainjson,supbuf=invokesupervisor(app,teamlead_response)

            complete=formatcompletejson(bufresponses,teambuf,supbuf)

            if default_args['agent_team_supervisor_topic']!='':
              producegpttokafka(complete,default_args['agent_team_supervisor_topic'])


            time.sleep(1)
         except Exception as e:
          print("Error=",e)              
          tsslogging.locallogs("ERROR", "STEP 9b: Agentic AI Step 9b DAG in {} {}  Aborting after 10 consecutive errors.".format(os.path.basename(__file__),e))
          tsslogging.tsslogit("PrivateGPT Step 9b DAG in {} {} Aborting after 10 consecutive errors.".format(os.path.basename(__file__),e), "ERROR" )
          tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")
          time.sleep(5)
          count = count + 1
          if count > 10:
            break 
          
#main()





