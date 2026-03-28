import maadstml
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import json
from datetime import datetime, timezone
from airflow.decorators import dag, task
from flask import Flask, request, jsonify
from gevent.pywsgi import WSGIServer
import sys
import tsslogging
import os
import subprocess
import time
import random
import shlex
from typing import Dict, Any
import re
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import List
import requests
#import nest_asyncio
#nest_asyncio.apply()

lock = threading.Lock()
mqtt_lock = threading.Lock()


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scadaglobals as sg
import scada_modbus as cv
import mqtt_loop as mq

VIPERTOKEN = "" #os.environ['VIPERTOKEN']
VIPERHOST = "" #os.environ['VIPERHOST']
VIPERPORT = "" #os.environ['VIPERPORT']
HTTPADDR = ""
sys.dont_write_bytecode = True
##################################################  REST API SERVER #####################################
# This is a REST API server that will handle connections from a client
# There are two endpoints you can use to stream data to this server:
# 1. jsondataline -  You can POST a single JSONs from your client app. Your json will be streamed to Kafka topic.
# 2. jsondataarray -  You can POST JSON arrays from your client app. Your json will be streamed to Kafka topic.


######################################## USER CHOOSEN PARAMETERS ########################################
default_args = {
  'owner' : 'Sebastian Maurice',    
  'enabletls': '1',
  'microserviceid' : '',
  'producerid' : 'iotsolution',  
  'topics' : 'iot-raw-data', # *************** This is one of the topic you created in SYSTEM STEP 2
  'identifier' : 'TML solution',  
  'tss_rest_port' : '9001',  # <<< ***** replace replace with port number i.e. this is listening on port 9000 
  'rest_port' : '9002',  # <<< ***** replace replace with port number i.e. this is listening on port 9000     
  'delay' : '7000', # << ******* 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic
  'topicid' : '-999', # <<< ********* do not modify              
}

######################################## DO NOT MODIFY BELOW #############################################

def writeviperlogs(errortype,message,VIPERTOKEN, VIPERHOST, VIPERPORT):

  args = default_args    
  dt = datetime.now(timezone.utc)
  timestamp = dt.strftime("[%a, %d %b %Y %H:%M:%S UTC]")
  
  vmsg=f"{timestamp} {errortype.upper()} [{message}]"
  Logjson = json.dumps({
      "MESSAGE": str(vmsg),
      "SERVICE": "TML-Plugin",
      "HOST": VIPERHOST,
      "PORT": str(VIPERPORT),
      "KAFKA_CONNECT_BOOTSTRAP_SERVERS": "Kafka Broker"
  })

  #Logjson=f'{"MESSAGE":"{vmsg}","SERVICE": "TML-Plugin", "HOST": "{VIPERHOST}","PORT": "{str(VIPERPORT)}","KAFKA_CONNECT_BOOTSTRAP_SERVERS": "Kafka Broker"}'         

#  print("Logjson=",Logjson)
  producetokafka(Logjson, "", "","plugin-producer","viperlogs","",args,VIPERTOKEN, VIPERHOST, VIPERPORT)

def producetokafka(value, tmlid, identifier,producerid,maintopic,substream,args,VIPERTOKEN, VIPERHOST, VIPERPORT):
     inputbuf=value     
     topicid=int(args['topicid'])
  
     # Add a 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic 
     delay=int(args['delay'])
     enabletls = int(args['enabletls'])
     identifier = args['identifier']
        
     try:
        result=maadstml.viperproducetotopic(VIPERTOKEN,VIPERHOST,VIPERPORT,maintopic,producerid,enabletls,delay,'','', '',0,inputbuf,substream,
                                            topicid,identifier)
        print("produce result========",result)
     except Exception as e:
        print("ERROR:",e)


# Check if tmux window exists BEFORE creating
def tmuxsession(windowinstance,steps):
    
    chip='amd64'
    mainos='linux'
    cdir=''
    isnew1=0
    isnew2=0
    viperrun=''
    viperport=-1
  
    if 'CHIP' in os.environ:
      chip=os.environ['CHIP']
    
    chip=chip.lower()  
    windowinstance=windowinstance.replace("_","-")
     
    # start the binary
    if steps=="4":      
       cdir="/Viper-preprocess"
       viperrun=f"/Viper-preprocess/viper-{mainos}-{chip}"
    if steps=="5":      
       cdir="/Viper-ml"      
       viperrun=f"/Viper-ml/viper-{mainos}-{chip}"
    if steps=="6":      
       cdir="/Viper-predict"            
       viperrun=f"/Viper-predict/viper-{mainos}-{chip}"
    if steps=="9":      
       cdir="/Viper-preprocess-pgpt"                 
       viperrun=f"/Viper-preprocess-pgpt/viper-{mainos}-{chip}"      
    if steps=="9b":      
       cdir="/Viper-preprocess-agenticai"                 
       viperrun=f"/Viper-preprocess-agenticai/viper-{mainos}-{chip}"

    if windowinstance != 'default':
      check_result = subprocess.run(
          ["tmux", "has-session", "-t", f"plugin_{windowinstance}"], 
          capture_output=True
      )
      check_result2 = subprocess.run(
          ["tmux", "has-session", "-t", f"plugin_{windowinstance}_{steps}"], 
          capture_output=True
      )
    
      if check_result.returncode != 0:
          # Window doesn't exist - create it
          subprocess.run(["tmux", "new-session", "-d", "-s", f"plugin_{windowinstance}"])
          subprocess.run(["tmux", "send-keys", "-t", f"plugin_{windowinstance}", f"cd /{cdir}", "ENTER"], capture_output=True, text=True)        
          isnew1=1
      else:
         subprocess.run(["tmux", "send-keys", "-t", f"plugin_{windowinstance}", "C-c"])
  
      if check_result2.returncode != 0:
          # Window doesn't exist - create it
          subprocess.run(["tmux", "new-session", "-d", "-s", f"plugin_{windowinstance}_{steps}"])
          isnew2=1
      else:
          subprocess.run(["tmux", "send-keys", "-t", f"plugin_{windowinstance}_{steps}", "C-c"])
  
    with open(f"{cdir}/viper.txt", 'r', encoding='utf-8') as file:
        line = file.readline()
        oldviperport=line.split(",")[1]

    if windowinstance!='default':      
      subprocess.run(["tmux", "send-keys", "-t", f"plugin_{windowinstance}_{steps}", f"cd /{cdir}", "ENTER"], capture_output=True, text=True)
      subprocess.run(["tmux", "send-keys", "-t", f"plugin_{windowinstance}_{steps}", viperrun, "ENTER"], capture_output=True, text=True)

    time.sleep(3)
    #if isnew2:
     # time.sleep(5)

    with open(f"{cdir}/viper.txt", 'r', encoding='utf-8') as file:
        line = file.readline()
        viperport=line.split(",")[1]

    
    return oldviperport,viperport,f"plugin_{windowinstance}_{steps}",f"plugin_{windowinstance}"
    #start the script
  #  subprocess.run(["tmux", "send-keys", "-t", f"plugin_{windowinstance}", new_pythonrun, "ENTER"], capture_output=True, text=True)


def flatten_for_shell(arg_list):
    """Flatten lists and remove newlines from strings"""
    flat_args = []
    for arg in arg_list:
        if isinstance(arg, list):
            # Strip newlines/spaces from each list item before joining
            cleaned_items = [str(x).replace('\n', '').replace('\r', '').strip() for x in arg]
            joined = ' '.join(cleaned_items)
            flat_args.append(f'"{joined}"')
        else:
            # Strip newlines from single args too
            arg_str = str(arg).replace('\n', '').replace('\r', '').strip()
            if ' ' in arg_str or ',' in arg_str:
                flat_args.append(f'"{arg_str}"')
            else:
                if arg_str.isdigit():
                  flat_args.append(arg_str)
                else:  
                  flat_args.append(f'"{arg_str}"')
                  
    return ' '.join(flat_args)
  
def stopstart(step,stepsarr,windowinstance='default'):

  print("Stopstart")
  pythonrun=''

  print("windowinstance==",windowinstance)
  print("step==",isinstance(step,str),step)
  step=str(step)
  
  if step=="4":
    oldviperport,viperport,vwn,swn=tmuxsession(windowinstance,step)    
    if windowinstance=='default':
      viperport=oldviperport
      
    with open("/tmux/step4_preprocess.txt", 'r', encoding='utf-8') as file:
        lines = file.readlines()
        pythonrun = lines[2].strip()  # Index 2 = 3rd line     
        wn = lines[1].strip()
        args = shlex.split(pythonrun)      
        args[-4] = stepsarr[-5]    # raw_data_topic
        args[-3] = stepsarr[-4]    # preprocesstypes  
        args[-2] = stepsarr[-3]    # jsoncriteria
        args[-1] = stepsarr[-2]    # preprocess_data_topic

        args[-6] = viperport    # rollbackoffset
        args[-5] = stepsarr[-1]    # rollbackoffset
      
        new_pythonrun = flatten_for_shell(args) #shlex.join(flatten_for_shell(args))
        print(f"new_pythonrun: {new_pythonrun}")      
  elif step=="5":
    
    oldviperport,viperport,vwn,swn=tmuxsession(windowinstance,step)    

    if windowinstance=='default':
      viperport=oldviperport


    with open("/tmux/step5_ml.txt", 'r', encoding='utf-8') as file:
        lines = file.readlines()
        pythonrun = lines[2].strip()  # Index 2 = 3rd line     
        wn = lines[1].strip()
        args = shlex.split(pythonrun)      
        args[-11] = viperport  # viper port                 
        args[-8] = stepsarr[-8]           
        args[-7] = stepsarr[-7]    
        args[-6] = stepsarr[-6]       
        args[-5] = stepsarr[-5]    
        args[-4] = stepsarr[-4]           
        args[-3] = stepsarr[-3]    
        args[-2] = stepsarr[-2]       
        args[-1] = stepsarr[-1]    
        new_pythonrun = flatten_for_shell(args) #shlex.join(flatten_for_shell(args))
        print(f"STEP 5 new_pythonrun: {new_pythonrun}")
      
  elif step=="6":
    oldviperport,viperport,vwn,swn=tmuxsession(windowinstance,step)    
    if windowinstance=='default':
      viperport=oldviperport
    
    with open("/tmux/step6_predictions.txt", 'r', encoding='utf-8') as file:
        lines = file.readlines()
        pythonrun = lines[2].strip()  # Index 2 = 3rd line     
        wn = lines[1].strip()
        args = shlex.split(pythonrun)      
        args[-10] = viperport  # viper port      
        args[-7] = stepsarr[-7]    
        args[-6] = stepsarr[-6]       
        args[-5] = stepsarr[-5]    
        args[-4] = stepsarr[-4]           
        args[-3] = stepsarr[-3]    
        args[-2] = stepsarr[-2]       
        args[-1] = stepsarr[-1]    
        new_pythonrun = flatten_for_shell(args) #shlex.join(flatten_for_shell(args))
        print(f"new_pythonrun: {new_pythonrun}")
  elif step=="9":
    oldviperport,viperport,vwn,swn=tmuxsession(windowinstance,step)    
    if windowinstance=='default':
      viperport=oldviperport
    
    with open("/tmux/step9_ai.txt", 'r', encoding='utf-8') as file:
        lines = file.readlines()
        pythonrun = lines[2].strip()  # Index 2 = 3rd line     
        wn = lines[1].strip()
        args = shlex.split(pythonrun)      
      
        args[-24] = viperport  # viper port     
        args[-23] = stepsarr[-18]   #vectorcollectionname      
        args[-22] = stepsarr[-17]   #consumefrom 
        args[-21] = stepsarr[-16]   #pgpt data topic
        args[-18] = stepsarr[-15]    #rollback
        args[-17] = stepsarr[-14]    #prompt      
        args[-16] = stepsarr[-13]    #context   
        args[-15] = stepsarr[-12]   #keyattribute       
        args[-14] = stepsarr[-11]   #keyprocess 
      
        args[-13] = stepsarr[-10]    #hyperbatch      
        args[-12] = stepsarr[-9]     #docfolder  
        args[-11] = stepsarr[-8]    #docingestinterval
      
        args[-7] = stepsarr[-7]    #temp
        args[-6] = stepsarr[-6]    #vectorsearch         
        args[-5] = stepsarr[-5]    ##context window
        args[-4] = stepsarr[-4]    #pgptcontainername       
        args[-3] = stepsarr[-3]    #pgpthost
        args[-2] = stepsarr[-2]    #pgptport   
        args[-1] = stepsarr[-1]    #vectordimension
        new_pythonrun = flatten_for_shell(args) #shlex.join(flatten_for_shell(args))
        print(f"new_pythonrun: {new_pythonrun}")      
  elif step=="9b":
    oldviperport,viperport,vwn,swn=tmuxsession(windowinstance,step)    
    if windowinstance=='default':
      viperport=oldviperport
    
    with open("/tmux/step9b_agenticai.txt", 'r', encoding='utf-8') as file:
        lines = file.readlines()
        pythonrun = lines[2].strip()  # Index 2 = 3rd line     
        wn = lines[1].strip()
        args = shlex.split(pythonrun)      

        args[-27] = viperport  # viper port              
        args[-26] = stepsarr[-17]    
        args[-25] = stepsarr[-16]    
        args[-23] = stepsarr[-15]    
        args[-22] = stepsarr[-14]          
        args[-18] = stepsarr[-13]       
        args[-17] = stepsarr[-12]          
        args[-14] = stepsarr[-11]           
        args[-13] = stepsarr[-10]    
        args[-12] = stepsarr[-9]       
        args[-11] = stepsarr[-8]    
        args[-10] = stepsarr[-7]    
        args[-9] = stepsarr[-6]       
        args[-8] = stepsarr[-5]    
        args[-7] = stepsarr[-4]           
        args[-3] = stepsarr[-3]    
        args[-2] = stepsarr[-2]       
        args[-1] = stepsarr[-1]    
        new_pythonrun = flatten_for_shell(args) #shlex.join(flatten_for_shell(args))
        print(f"new_pythonrun: {new_pythonrun}")

  new_pythonrun=new_pythonrun.replace("<<n>>",'\n')
  if windowinstance=='default':
    subprocess.run(["tmux", "send-keys", "-t", wn, "C-c"])
    subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "{}".format(new_pythonrun), "ENTER"],capture_output=True, text=True)        
  else:  
    subprocess.run(["tmux", "send-keys", "-t", "{}".format(swn), "C-c"])
    subprocess.run(["tmux", "send-keys", "-t", "{}".format(swn), "{}".format(new_pythonrun), "ENTER"],capture_output=True, text=True)        
    
    #subprocess.run(["tmux", "new", "-d", "-s", "{}".format(windowinstance)])
    #subprocess.run(["tmux", "send-keys", "-t", "{}".format(windowinstance), "{}".format(new_pythonrun), "ENTER"],capture_output=True, text=True)        
    
def terminatetmuxwindows(step,wn):
  # Get all tmux sessions
  wt=""
  if wn == 'all':
    result = subprocess.run(['tmux', 'list-sessions'], capture_output=True, text=True)
    sessions = result.stdout.strip().split('\n')
    
    for session in sessions:
        if session.startswith('plugin_'):
            session_name = session.split(':')[0]
            subprocess.run(['tmux', 'kill-session', '-t', session_name])
              
            print(f"Killed tmux session: {session_name}")
            
            mw=session_name.split("_")[1]#session_name.replace("plugin_", "", 1)
            mw=session_name
            wt = wt + mw + ","
    wt = wt[:-1]      
    with open("/tmux/step4_preprocess.txt", 'r', encoding='utf-8') as file:
        lines = file.readlines()
        wn = lines[1].strip()
        subprocess.run(["tmux", "send-keys", "-t", wn, "C-c"])        
        wt = wt + wn + ","        
    with open("/tmux/step5_ml.txt", 'r', encoding='utf-8') as file:
        lines = file.readlines()
        wn = lines[1].strip()
        subprocess.run(["tmux", "send-keys", "-t", wn, "C-c"])      
        wt = wt + wn + ","           
    with open("/tmux/step6_predictions.txt", 'r', encoding='utf-8') as file:
        lines = file.readlines()
        wn = lines[1].strip()
        subprocess.run(["tmux", "send-keys", "-t", wn, "C-c"])
        wt = wt + wn + ","
    with open("/tmux/step9_ai.txt", 'r', encoding='utf-8') as file:
        lines = file.readlines()
        wn = lines[1].strip()
        subprocess.run(["tmux", "send-keys", "-t", wn, "C-c"])
        wt = wt + wn            
    with open("/tmux/step9b_agenticai.txt", 'r', encoding='utf-8') as file:
        lines = file.readlines()
        wn = lines[1].strip()
        subprocess.run(["tmux", "send-keys", "-t", wn, "C-c"])
        wt = wt + wn      
  elif wn=='default':
    if step=="4":
      with open("/tmux/step4_preprocess.txt", 'r', encoding='utf-8') as file:
        lines = file.readlines()
        wn = lines[1].strip()
        subprocess.run(["tmux", "send-keys", "-t", wn, "C-c"])        
        wt=wn
    if step=="5":
      with open("/tmux/step5_ml.txt", 'r', encoding='utf-8') as file:
        lines = file.readlines()
        wn = lines[1].strip()
        subprocess.run(["tmux", "send-keys", "-t", wn, "C-c"])      
        wt=wn        
    if step=="6":
      with open("/tmux/step6_predictions.txt", 'r', encoding='utf-8') as file:
        lines = file.readlines()
        wn = lines[1].strip()
        subprocess.run(["tmux", "send-keys", "-t", wn, "C-c"])
        wt=wn
    if step=="9b":
      with open("/tmux/step9b_agenticai.txt", 'r', encoding='utf-8') as file:
        lines = file.readlines()
        wn = lines[1].strip()
        subprocess.run(["tmux", "send-keys", "-t", wn, "C-c"])
        wt=wn        
    if step=="9":
      with open("/tmux/step9_ai.txt", 'r', encoding='utf-8') as file:
        lines = file.readlines()
        wn = lines[1].strip()
        subprocess.run(["tmux", "send-keys", "-t", wn, "C-c"])
        wt=wn                
    if step=="0":
      with open("/tmux/step4_preprocess.txt", 'r', encoding='utf-8') as file:
        lines = file.readlines()
        wn = lines[1].strip()
        subprocess.run(["tmux", "send-keys", "-t", wn, "C-c"])        
        wt = wt + wn + ","        
      with open("/tmux/step5_ml.txt", 'r', encoding='utf-8') as file:
        lines = file.readlines()
        wn = lines[1].strip()
        subprocess.run(["tmux", "send-keys", "-t", wn, "C-c"])      
        wt = wt + wn + ","           
      with open("/tmux/step6_predictions.txt", 'r', encoding='utf-8') as file:
        lines = file.readlines()
        wn = lines[1].strip()
        subprocess.run(["tmux", "send-keys", "-t", wn, "C-c"])
        wt = wt + wn + ","             
      with open("/tmux/step9_ai.txt", 'r', encoding='utf-8') as file:
        lines = file.readlines()
        wn = lines[1].strip()
        subprocess.run(["tmux", "send-keys", "-t", wn, "C-c"])
        wt = wt + wn                              
      with open("/tmux/step9b_agenticai.txt", 'r', encoding='utf-8') as file:
        lines = file.readlines()
        wn = lines[1].strip()
        subprocess.run(["tmux", "send-keys", "-t", wn, "C-c"])
        wt = wt + wn                      
  else: 
       subprocess.run(['tmux', 'kill-session', '-t', f"plugin_{wn}_{step}"])
       subprocess.run(['tmux', 'kill-session', '-t', f"plugin_{wn}"])    
       wt = wn
  return wt    

def gettmlsystemsparams():
    repo=tsslogging.getrepo()  

  ############################################### API Routes ########################################      

    if VIPERHOST != "":
        #app = Flask(__name__)
        app = FastAPI()
                 
        app.add_middleware(
              CORSMiddleware,
              allow_origins=["*"],  # Allow all for dev
              allow_credentials=True,
              allow_methods=["*"],
              allow_headers=["*"],
        )

#-------------------------------- TERMINATE WINDOW -----------------------------------------------------      
        @app.post('/api/v1/terminatewindow')
        def windowterminate(jdata: dict): 
#          jdata = request.get_json()          
          if not jdata:
            return "Missing windows", 400
          
          step = jdata.get('step','')            
          windowname = jdata.get('windowname','')
          
          if windowname != '':
               wd=terminatetmuxwindows(step,windowname)
               return {
                    'status': f"success: windows terminated: {wd}",
               }

          return {
              'status': 'success: no windows terminated',
          }

#-------------------------------- CREATETOPIC -----------------------------------------------------      
        @app.post('/api/v1/createtopic')
        def storecreatetopic(jdata: dict):
#          jdata = request.get_json()          
          if not jdata or not jdata.get('topics'):
            return "Missing topics", 400
          
          topics = jdata.get('topics')  
          numpartitions = int(jdata.get('numpartitions',3))
          replication = int(jdata.get('replication',1))
          description = jdata.get('description','user topic')  
          
          enabletls = int(jdata.get('enabletls',1))          
          ptarr = [t.strip() for t in topics.split(",") if t.strip()]          
          brokerhost=''
          brokerport=''
          try:
            for pt in ptarr:
              if len(pt)>0:
                result=maadstml.vipercreatetopic(VIPERTOKEN,VIPERHOST,VIPERPORT,pt,'companyname',
                                 'myname','myemail','mylocation',description,enabletls,
                                 brokerhost,brokerport,numpartitions,replication,'')
                print(result)
                writeviperlogs("INFO",f"Creating Topic: {pt}",VIPERTOKEN,VIPERHOST,VIPERPORT)                                        
            return {
              'status': 'success',
              'topics': topics,
              'partitions': numpartitions,
              'replication': replication,
              'description': description
            }
          except Exception as e:
            writeviperlogs("ERROR",f"Creating Topic failed: {pt}: {e}",VIPERTOKEN,VIPERHOST,VIPERPORT)                            
            return {
              'status': f"error: {e}",
              'topics': topics,
              'partitions': numpartitions,
              'replication': replication,
              'description': description
            }
            
        
#-------------------------------- PREPROCESS -----------------------------------------------------            
        @app.post('/api/v1/preprocess')
        def storepreprocess(jdata: dict):
#          jdata = request.get_json()          
          if not jdata or not jdata.get('rawdatatopic'):
            return "Missing preprocess or invalid preprocess", 400

          step = str(jdata.get('step','') )
          try:
           if step=='4':
            step4raw_data_topic = jdata.get('rawdatatopic','')  
            step4preprocess_data_topic = jdata.get('preprocessdatatopic','')
            step4preprocesstypes = jdata.get('preprocesstypes','')
            step4jsoncriteria = jdata.get('jsoncriteria','')  
            rollbackoffset = jdata.get('rollbackoffsets',200)  
            
            windowinstance = jdata.get("windowinstance","default")                        
            step4arr = [step4raw_data_topic,step4preprocesstypes,step4jsoncriteria,step4preprocess_data_topic,rollbackoffset]
            stopstart(step,step4arr,windowinstance)
            
           elif step=='4c':
             maxrows = jdata.get('maxrows',10)  
             searchterms = jdata.get('searchterms','')  
             rememberpastwindows = jdata.get('rememberpastwindows',5)  
             patternwindowthreshold = jdata.get('patternwindowthreshold',30)  
             raw_data_topic = jdata.get('raw_data_topic','')  
             rtmsstream = jdata.get('rtmsstream','')  
             rtmsscorethreshold = jdata.get('rtmsscorethreshold',0.6)  
             attackscorethreshold = jdata.get('attackscorethreshold',0.6)  
             patternscorethreshold = jdata.get('patternscorethreshold',0.6)  
             localsearchtermfolder = jdata.get('localsearchtermfolder','')  
             localsearchtermfolderinterval = jdata.get('localsearchtermfolderinterval','')  
             rtmsfoldername = jdata.get('rtmsfoldername','')  
             rtmsmaxwindows = jdata.get('rtmsmaxwindows',10000)  
             windowinstance = jdata.get("windowinstance","default")            
             step4carr = [maxrows,searchterms,rememberpastwindows,patternwindowthreshold,raw_data_topic,rtmsstream,rtmsscorethreshold,attackscorethreshold,patternscorethreshold,
                         localsearchtermfolder,localsearchtermfolderinterval,rtmsfoldername,rtmsmaxwindows]
             stopstart(step,step4carr,windowinstance)

           return {
              'status': 'success',
              'step4raw_data_topic': jdata.get('rawdatatopic',''),
              'step4preprocess_data_topic': jdata.get('preprocessdatatopic',''),
              'step4preprocesstypes': jdata.get('preprocesstypes',''),
              'step4jsoncriteria': jdata.get('jsoncriteria',''),
              'rollbackoffset': jdata.get('rollbackoffset',400),            
              'windowinstance': jdata.get("windowinstance","default")                 
              }
          except Exception as e:
           writeviperlogs("ERROR",f"Preprocessing failed: {e}",VIPERTOKEN,VIPERHOST,VIPERPORT)                            
           return {
              'status': f"error:{e}",
              'step4raw_data_topic': jdata.get('rawdatatopic',''),
              'step4preprocess_data_topic': jdata.get('preprocessdatatopic',''),
              'step4preprocesstypes': jdata.get('preprocesstypes',''),
              'step4jsoncriteria': jdata.get('jsoncriteria',''),
              'rollbackoffset': jdata.get('rollbackoffset',400),            
              'windowinstance': jdata.get("windowinstance","default")                 
              }
            
          
#-------------------------------- MACHINE LEARNING -----------------------------------------------------                  
        @app.post('/api/v1/ml')
        def storeml(jdata: dict):
#          jdata = request.get_json()          
          if not jdata:
            return "Missing ml or invalid ml", 400

          step = str(jdata.get('step','') )
          try:
            if step=="5":
             trainingdatafolder = jdata.get('trainingdatafolder','')  
             ml_data_topic = jdata.get('ml_data_topic','')  
             preprocess_data_topic = jdata.get('preprocess_data_topic','')  
             islogistic = jdata.get('islogistic',0)  
             dependentvariable = jdata.get('dependentvariable','failure')  
             independentvariables = jdata.get('independentvariables','')  
             processlogic = jdata.get('processlogic','')  
             rollbackoffsets = jdata.get('rollbackoffsets',50)  
             windowinstance = jdata.get('windowinstance','default')            
             step5arr = [rollbackoffsets,processlogic,independentvariables,dependentvariable,
                         islogistic,preprocess_data_topic,ml_data_topic,trainingdatafolder]
             stopstart(step,step5arr,windowinstance)
             return {
              'status': "success",
              'trainingdatafolder': jdata.get('trainingdatafolder',''),
              'ml_data_topic': jdata.get('ml_data_topic',''),  
              'preprocess_data_topic': jdata.get('preprocess_data_topic',''),
              'islogistic': jdata.get('islogistic',0),
              'dependentvariable': jdata.get('dependentvariable','failure'),
              'independentvariables': jdata.get('independentvariables',''),
              'processlogic': jdata.get('processlogic',''),
              'rollbackoffsets': jdata.get('rollbackoffsets',50),
              'windowinstance': jdata.get('windowinstance','default')                          
              }    
          except Exception as e:
             writeviperlogs("ERROR",f"Machine learning failed: {e}",VIPERTOKEN,VIPERHOST,VIPERPORT)                            
             return {
              'status': f"error:{e}",
              'trainingdatafolder': jdata.get('trainingdatafolder',''),
              'ml_data_topic': jdata.get('ml_data_topic',''),  
              'preprocess_data_topic': jdata.get('preprocess_data_topic',''),
              'islogistic': jdata.get('islogistic',0),
              'dependentvariable': jdata.get('dependentvariable','failure'),
              'independentvariables': jdata.get('independentvariables',''),
              'processlogic': jdata.get('processlogic',''),
              'rollbackoffsets': jdata.get('rollbackoffsets',50),
              'windowinstance': jdata.get("windowinstance","default")            
              }
              
#-------------------------------- PREDICTIONS -----------------------------------------------------                        
        @app.post('/api/v1/predict')
        def predictdata(jdata: dict):
#          jdata = request.get_json()          
          if not jdata:
            return "Missing ml or invalid prediction", 400
          
          step = str(jdata.get('step','') )

          try:
            if step=="6":
             pathtoalgos = jdata.get('pathtoalgos','')  
             maxrows = jdata.get('rollbackoffsets',50)  
             consumefrom = jdata.get('consumefrom','')  
             inputdata = jdata.get('inputdata','')  
             streamstojoin = jdata.get('streamstojoin','')  
             ml_prediction_topic = jdata.get('ml_prediction_topic','')  
             preprocess_data_topic = jdata.get('preprocess_data_topic','')  
             windowinstance = jdata.get('windowinstance','default')            
             step6arr = [maxrows,preprocess_data_topic,ml_prediction_topic,streamstojoin,inputdata,consumefrom,pathtoalgos]
             stopstart(step,step6arr,windowinstance)
             return {
              'status': "success",
               'pathtoalgos': jdata.get('pathtoalgos',''),
               'maxrows': jdata.get('rollbackoffsets',50), 
               'consumefrom': jdata.get('consumefrom',''), 
               'inputdata': jdata.get('inputdata',''),
               'streamstojoin': jdata.get('streamstojoin',''),  
               'ml_prediction_topic': jdata.get('ml_prediction_topic',''),  
               'preprocess_data_topic': jdata.get('preprocess_data_topic',''),  
               'windowinstance': jdata.get('windowinstance','default')    
              }         
          except Exception as e:
             writeviperlogs("ERROR",f"Predictions failed: {e}",VIPERTOKEN,VIPERHOST,VIPERPORT)                            
             return {
              'status': f"error:{e}",
               'pathtoalgos': jdata.get('pathtoalgos',''),
               'maxrows': jdata.get('rollbackoffsets',50), 
               'consumefrom': jdata.get('consumefrom',''), 
               'inputdata': jdata.get('inputdata',''),
               'streamstojoin': jdata.get('streamstojoin',''),  
               'ml_prediction_topic': jdata.get('ml_prediction_topic',''),  
               'preprocess_data_topic': jdata.get('preprocess_data_topic',''),  
               'windowinstance': jdata.get('windowinstance','default')    
              }

#-------------------------------- AI -----------------------------------------------------                        
        @app.post('/api/v1/ai')
        def aidata(jdata: dict):
#          jdata = request.get_json()          
          if not jdata:
            return "Missing ai or invalid ai", 400
          
          step = str(jdata.get('step','') )
          try:
            if step=="9":
             vectordimension = jdata.get('vectordimension','768')  
             contextwindowsize= jdata.get('contextwindowsize','8192') #agent - team lead - supervisor
             vectorsearchtype= jdata.get('vectorsearchtype','Manhattan')
             temperature= float(jdata.get('temperature','0.1'))
             docfolderingestinterval= jdata.get('docfolderingestinterval','900')
             docfolder= jdata.get('docfolder','')
             vectordbcollectionname= jdata.get('vectordbcollectionname','tml-pgpt')
             hyperbatch= jdata.get('hyperbatch','0')
             keyprocesstype= jdata.get('keyprocesstype','')
             keyattribute= jdata.get('keyattribute','hyperprediction')
             context= jdata.get('context','')
             prompt= jdata.get('prompt','')
             pgptport= jdata.get('pgptport','8001')
             pgpthost= jdata.get('pgpthost','http://127.0.0.1')              
             pgpt_data_topic = jdata.get('pgpt_data_topic','')  
             consumefrom = jdata.get('consumefrom','')  
             rollbackoffset = jdata.get('rollbackoffset','5')  
             pgptcontainername = jdata.get('pgptcontainername','maadsdocker/tml-privategpt-with-gpu-nvidia-amd64-v2') 
             windowinstance = jdata.get('windowinstance','default')            
              
             step9arr = [vectordbcollectionname,consumefrom,pgpt_data_topic, rollbackoffset, prompt,context,keyattribute,keyprocesstype,
                         hyperbatch,docfolder,docfolderingestinterval, temperature,vectorsearchtype,contextwindowsize,pgptcontainername, pgpthost,pgptport,vectordimension]
              
             stopstart(step,step9arr,windowinstance)
      
             return {               
              'status': "success",
               'vectordimension': jdata.get('vectordimension','768'),
               'contextwindowsize': jdata.get('contextwindowsize','8192'), #agent - team lead - supervisor
               'vectorsearchtype': jdata.get('vectorsearchtype','Manhattan'),
               'temperature': jdata.get('temperature','0.1'),
               'docfolderingestinterval': jdata.get('docfolderingestinterval','900'),
               'docfolder': jdata.get('docfolder',''),
               'vectordbcollectionname': jdata.get('vectordbcollectionname','tml-pgpt'),
               'hyperbatch': jdata.get('hyperbatch','0'),
               'keyprocesstype': jdata.get('keyprocesstype',''),
               'keyattribute': jdata.get('keyattribute','hyperprediction'),
               'context': jdata.get('context',''),
               'prompt': jdata.get('prompt',''),
               'pgptport': jdata.get('pgptport','8001'),
               'pgpthost': jdata.get('pgpthost','http://127.0.0.1'),
               'pgpt_data_topic': jdata.get('pgpt_data_topic',''),
               'consumefrom': jdata.get('consumefrom',''),
               'rollbackoffset': jdata.get('rollbackoffset','5'),
               'pgptcontainername': jdata.get('pgptcontainername','maadsdocker/tml-privategpt-with-gpu-nvidia-amd64-v2'),
               'windowinstance': jdata.get('windowinstance','default')                                         
              }          
          except Exception as e:
             writeviperlogs("ERROR",f"AI failed: {e}",VIPERTOKEN,VIPERHOST,VIPERPORT)                            
             return {
              'status': f"error:{e}",
               'vectordimension': jdata.get('vectordimension','768'),
               'contextwindowsize': jdata.get('contextwindowsize','8192'), #agent - team lead - supervisor
               'vectorsearchtype': jdata.get('vectorsearchtype','Manhattan'),
               'temperature': jdata.get('temperature','0.1'),
               'docfolderingestinterval': jdata.get('docfolderingestinterval','900'),
               'docfolder': jdata.get('docfolder',''),
               'vectordbcollectionname': jdata.get('vectordbcollectionname','tml-pgpt'),
               'hyperbatch': jdata.get('hyperbatch','0'),
               'keyprocesstype': jdata.get('keyprocesstype',''),
               'keyattribute': jdata.get('keyattribute','hyperprediction'),
               'context': jdata.get('context',''),
               'prompt': jdata.get('prompt',''),
               'pgptport': jdata.get('pgptport','8001'),
               'pgpthost': jdata.get('pgpthost','http://127.0.0.1'),
               'pgpt_data_topic': jdata.get('pgpt_data_topic',''),
               'consumefrom': jdata.get('consumefrom',''),
               'rollbackoffset': jdata.get('rollbackoffset','5'),
               'pgptcontainername': jdata.get('pgptcontainername','maadsdocker/tml-privategpt-with-gpu-nvidia-amd64-v2'),
               'windowinstance': jdata.get('windowinstance','default')                                                        
              }
      
#-------------------------------- AGENTIC AI -----------------------------------------------------                        
        @app.post('/api/v1/agenticai')
        def agenticaidata(jdata: dict):
#          jdata = request.get_json()          
          if not jdata:
            return "Missing agentic ai or invalid agentic ai", 400
          
          step = str(jdata.get('step','') )
          
          try:
            if step=="9b":
             maxrows = jdata.get('rollbackoffsets',10)  
             ollamamodel= jdata.get('ollama-model','phi3:3.8b,phi3:3.8b,llama3.2:3b') #agent - team lead - supervisor
             vectordbpath= jdata.get('vectordbpath','/rawdata/vectordb')
             temperature= float(jdata.get('temperature','0.1'))
             vectordbcollectionname= jdata.get('vectordbcollectionname','tml-llm-model')
             ollamacontainername= jdata.get('ollamacontainername','maadsdocker/tml-privategpt-with-gpu-nvidia-amd64-llama3-tools')
             embedding= jdata.get('embedding','nomic-embed-text')
             agents_topic_prompt= jdata.get('agents_topic_prompt','')
             teamlead_topic= jdata.get('teamlead_topic','team-lead-responses')
             teamleadprompt= jdata.get('teamleadprompt','')
             supervisor_topic= jdata.get('supervisor_topic','supervisor-responses')
             supervisorprompt= jdata.get('supervisorprompt','')
             agenttoolfunctions= jdata.get('agenttoolfunctions','')
             agent_team_supervisor_topic= jdata.get('agent_team_supervisor_topic','all-agents-responses')              
             contextwindow = jdata.get('contextwindow','4096')  
             localmodelsfolder = jdata.get('localmodelsfolder','/rawdata/ollama')  
             agenttopic = jdata.get('agenttopic','agent-responses')  
             windowinstance = jdata.get('windowinstance','default')            
             step9barr = [maxrows,ollamamodel,vectordbpath,temperature,vectordbcollectionname,ollamacontainername,embedding,agents_topic_prompt,teamlead_topic,teamleadprompt,
                         supervisor_topic,supervisorprompt,agenttoolfunctions,agent_team_supervisor_topic,contextwindow,localmodelsfolder,agenttopic]
             stopstart(step,step9barr,windowinstance)
      
             return {               
              'status': "success",
              'rollbackoffset': jdata.get('rollbackoffsets',10),
              'ollamamodel': jdata.get('ollama-model','phi3:3.8b,phi3:3.8b,llama3.2:3b'), #agent - team lead - supervisor
              'vectordbpath': jdata.get('vectordbpath','/rawdata/vectordb'),
              'temperature': jdata.get('temperature','0.1'),
              'vectordbcollectionname': jdata.get('vectordbcollectionname','tml-llm-model'),
              'ollamacontainername': jdata.get('ollamacontainername','maadsdocker/tml-privategpt-with-gpu-nvidia-amd64-llama3-tools'),
              'embedding': jdata.get('embedding','nomic-embed-text'),
              'agents_topic_prompt': jdata.get('agents_topic_prompt',''),
              'teamlead_topic': jdata.get('teamlead_topic','team-lead-responses'),
              'teamleadprompt': jdata.get('teamleadprompt',''),
              'supervisor_topic': jdata.get('supervisor_topic','supervisor-responses'),
              'supervisorprompt': jdata.get('supervisorprompt',''),
              'agenttoolfunctions': jdata.get('agenttoolfunctions',''),
              'agent_team_supervisor_topic': jdata.get('agent_team_supervisor_topic','all-agents-responses'),
              'contextwindow': jdata.get('contextwindow','4096'),  
              'localmodelsfolder': jdata.get('localmodelsfolder','/rawdata/ollama'),
              'agenttopic': jdata.get('agenttopic','agent-responses'),
              'windowinstance': jdata.get('windowinstance','default')               
              }
          except Exception as e:
             writeviperlogs("ERROR",f"Agentic AI failed: {e}",VIPERTOKEN,VIPERHOST,VIPERPORT)                            
             return {
              'status': f"error:{e}",
              'rollbackoffset': jdata.get('rollbackoffsets',10),
              'ollamamodel': jdata.get('ollama-model','phi3:3.8b,phi3:3.8b,llama3.2:3b'), #agent - team lead - supervisor
              'vectordbpath': jdata.get('vectordbpath','/rawdata/vectordb'),
              'temperature': jdata.get('temperature','0.1'),
              'vectordbcollectionname': jdata.get('vectordbcollectionname','tml-llm-model'),
              'ollamacontainername': jdata.get('ollamacontainername','maadsdocker/tml-privategpt-with-gpu-nvidia-amd64-llama3-tools'),
              'embedding': jdata.get('embedding','nomic-embed-text'),
              'agents_topic_prompt': jdata.get('agents_topic_prompt',''),
              'teamlead_topic': jdata.get('teamlead_topic','team-lead-responses'),
              'teamleadprompt': jdata.get('teamleadprompt',''),
              'supervisor_topic': jdata.get('supervisor_topic','supervisor-responses'),
              'supervisorprompt': jdata.get('supervisorprompt',''),
              'agenttoolfunctions': jdata.get('agenttoolfunctions',''),
              'agent_team_supervisor_topic': jdata.get('agent_team_supervisor_topic','all-agents-responses'),
              'contextwindow': jdata.get('contextwindow','4096'),  
              'localmodelsfolder': jdata.get('localmodelsfolder','/rawdata/ollama'),
              'agenttopic': jdata.get('agenttopic','agent-responses'),
              'windowinstance': jdata.get('windowinstance','default')               
              }
      
#-------------------------------- CONSUME -----------------------------------------------------                        
        @app.post('/api/v1/consume')
        def consumedata(jdata: dict):
#          jdata = request.get_json()          
          osdu = jdata.get('osdu','false')
          kind = jdata.get('kind','tml')  

          if not jdata or not jdata.get('topic'):
            if osdu=='false':
              return "Missing ml or invalid consume", 400
            else:
              return {
                  "kind": f"{kind}",
                  "id": "consume-error",
                  "error": {
                      "code": 400,
                      "message": "Missing topic or invalid consume request",
                      "reason": "Topic parameter required"
                  }
              }             
          forward_statuses = []
          maintopic = jdata.get('topic','')
          forwardurl = jdata.get('forwardurl','')  
          legal = jdata.get('legal','tml-legal')  
          
          forward_headers = {'Content-Type': 'application/json'}

          if maintopic != '':
           try: 
            rollbackoffsets = int(jdata.get('rollbackoffsets',100))
            enabletls = int(jdata.get('enabletls',1))
            consumerid='tmlconsumerplugin'
            companyname='companyname'
            offset = int(jdata.get('offset',-1))
            brokerhost = ''
            brokerport = -999
            microserviceid = ''
            topicid = jdata.get('topicid','-999')
            preprocesstype = ''
            delay = 100
            partition = -1
      
            result=maadstml.viperconsumefromtopic(VIPERTOKEN,VIPERHOST,VIPERPORT,maintopic,
                        consumerid,companyname,partition,enabletls,delay,
                        offset, brokerhost,brokerport,microserviceid,
                        topicid,rollbackoffsets,preprocesstype)
            now_iso = datetime.utcnow().isoformat() + "Z"
            result = json.loads(result)  
            if osdu=='false':
                response =  {
                    'status': 'consumed',
                    'topic': maintopic,
                    'Messages': result,  # viperconsumefromtopic output
                    'consumer_id': consumerid
                }
            else:
                response = {
                    "kind": f"{kind}",
                    "id": f"osdu:tml:consume:{maintopic}:{int(time.time())}",
                    "data": {
                        "Topic": maintopic,
                        "ConsumerID": consumerid,
                        "CompanyName": companyname,
                        "Messages": result,  # Your viperconsumefromtopic output
                        "Partition": partition,
                        "Offset": offset,
                        "RollbackOffsets": rollbackoffsets,
                        "meta": {
                            "dataPartitionId": "tml-id",
                            "createTime": f"{now_iso}",
                            "modificationTime": f"{now_iso}",
                            "acl": {
                                "viewers": ["data.default.viewers@tml.group"],
                                "owners": ["data.default.owners@tml.group"]
                            },
                            "legal": {
                                "legaltags": f"{legal}",
                                "status": "compliant"
                            }
                        }
                    }
                }
  
            if forwardurl == '':
                #print("response=",response)
                return response
            else:              
               farr = [fw.strip() for fw in forwardurl.split(",")]  # Clean whitespace              
               for fw in farr: 
                 try:
                   fwdresponse = requests.post(
                    f"{fw}",
                     json=response,
                     headers={'Content-Type': 'application/json', 'data-partition-id': 'tml-id'}, timeout=30 )
                   forward_statuses.append({
                      'url': fw.strip(),
                      'status': fwdresponse.status_code,
                      'success': fwdresponse.ok
                   })                 
                 except Exception as e:
                    forward_statuses.append({'url': fw.strip(), 'error': str(e)})
                    writeviperlogs("ERROR",f"Forwarding URL failed: {e}",VIPERTOKEN,VIPERHOST,VIPERPORT)                

               response['forward_statuses'] = forward_statuses                   
               return response
           except Exception as e:
               print("Error=",e)
               writeviperlogs("ERROR",f"Consume failed: {e}",VIPERTOKEN,VIPERHOST,VIPERPORT)                             
               return {"error": f"Consumption failed: {e}"}
             
             
##################### INDUSTRIAL API ##############################################################
#-------------------------------- SCADA/MODBUS -----------------------------------------------------                        
        @app.post("/api/v1/scada_modbus_read")
        def start_vessel_read(req: dict):
            
            #req = request.get_json()
            job_id = str(time.time())
            
            scada_cfg = {
                "host": req.get("scada_host", "127.0.0.1"),
                "port": req.get("scada_port", 2502),
                "unit_id": req.get("slave_id", 1),
            }
            baseurl = req.get("base_url", "")
            with lock:  # ✅ Thread-safe
                if sg.read_job and sg.read_job["stop"]:
                    # Don't sleep - just skip or queue
                    pass
        
                # Stop existing thread first
                if sg.read_thread and sg.read_thread.is_alive():
                    sg.read_job["stop"] = True
                    sg.read_thread.join(timeout=float(req.get("read_interval_seconds", 0.3))+1.0)
            
                # Helper to send optional payloads
                def post_if_payload(key: str, endpoint: str) -> None:
                    payload = req.get(key, {})
                    print("payload====",payload)
                    if payload:
                        try:
                            u = endpoint
                            requests.post(u.strip(), json=payload, timeout=5.0)
                        except Exception as e:
                            print(f"Error: cannot send {key} post in scada modbus: {e}")
                            writeviperlogs("ERROR",f"cannot send {key} post in scada modbus: {e}",VIPERTOKEN,VIPERHOST,VIPERPORT)                            

#                post_if_payload("terminatewindow", f"{baseurl}/api/v1/terminatewindow")            
                post_if_payload("preprocessing", f"{baseurl}/api/v1/preprocess")
                post_if_payload("machinelearning", f"{baseurl}/api/v1/ml")
                post_if_payload("predictions", f"{baseurl}/api/v1/predict")
                post_if_payload("agenticai", f"{baseurl}/api/v1/agenticai")              
                post_if_payload("ai", f"{baseurl}/api/v1/ai")                            
              
                sg.read_job = {"stop": False, "job_id": job_id}
                sg.read_thread = threading.Thread(
                target=cv.modbus_read_loop,
                args=(
                    scada_cfg,
                    req.get("read_interval_seconds", 0.3),
                    req.get("callback_url",""),
                    req.get("max_reads",-1),
                    req.get("fields", []),
                    req.get("scaling", {}),
                    req.get("start_register", 40001) - 40001,
                    req.get("sendtotopic", ""),            
                    job_id,
                    VIPERTOKEN,
                    VIPERHOST,
                    VIPERPORT,
                    default_args,
                    req.get("vessel_names", {}),
                    req.get("preprocessing", {}),
                    req.get("machinelearning", {}),
                    req.get("predictions", {}),
                    req.get("agenticai", {}),
                    req.get("ai", {}),                
                    req.get("createvariables", "")  # ✅ Dynamic from request                  
                   ),
                   daemon=True,
                )
                sg.read_thread.start()
        
            return {
                "message": "SCADA Vessel read started",
                "job_id": job_id,
                "config_from_request": {
                    "fields": len(req.get("fields", [])),
                    "has_createvariables": bool(req.get("createvariables"))
                }
            }


        @app.post("/api/v1/vessel_data")
        def vessel_data_callback(data: dict):
#            data = request.get_json()
    
            # DYNAMIC: Handle ANY data structure from callback
            vessel = data.get('vessel', data)  # Nested OR flat
    
            # DYNAMIC: Find vessel identifier (vesselIndex OR first field)
            vessel_id = (vessel or {}).get('vesselIndex', 
                 next(iter(vessel), 'N/A') if vessel else 'N/A')
    
            # DYNAMIC: Find pressure field (operatingPressure OR first numeric)
            pressure = 0
            for key, val in vessel.items():
                if isinstance(val, (int, float)) and 'pressure' in key.lower():
                   pressure = val
                   break
    
            print(f"📨 Job {data.get('job_id', 'N/A')} | Vessel {vessel_id}: {pressure:.1f}")
            print(f"   Total fields: {len(vessel) if vessel else 0}")
    
            # DYNAMIC: Show computed vars (anything not in original fields list)
            original_fields = data.get('fields', [])
            computed_fields = {k: v for k, v in vessel.items() 
                              if k not in original_fields and isinstance(v, (int, float))}
    
            for field, value in list(computed_fields.items())[:3]:
                print(f"   {field}: {value:.0f}")

            print(json.dumps(data))
            return json.dumps(data)


        @app.post("/api/v1/scada_read_stop")
        def stop_vessel_read():
            if sg.read_job:
                sg.read_job["stop"] = True
            return {"message": "Stop signal sent"}
        
        @app.get("/api/v1/scada_status")
        def status():
            return {
                "running": sg.read_job is not None and not sg.read_job.get("stop", True) if sg.read_job else False
            }

        @app.post("/api/v1/external_payload")
        def extpayload(data: dict):
              datatopic = data.get("sendtotopic", "")
              baseurl = data.get("base_url", "")          
              try:
                if datatopic != "":
                   requests.post(f"{baseurl}/api/v1/jsondataline", json=data, timeout=5.0)
                   return "ok"
                else:
                   return "No sendtotopic its empty" 
              except Exception as e:
                return {
                 "message": f"Error: {e}"
                }
                
      
################################# MQTT #############################################################
        
        @app.post("/api/v1/mqtt_subscribe")
        def start_mqtt_subscribe(req: dict):
          
         try:
          job_id = str(time.time())
          baseurl = req.get("base_url", "")
          mqtt_cfg = {
            "broker": req.get("mqtt_broker", ""),
            "port": int(req.get("mqtt_port", "8883")),
            "topic": req.get("mqtt_subscribe_topic", ""),
            "sendtotopic": req.get("sendtotopic",""),
            "username": os.environ.get('MQTTUSERNAME', ''),
            "password": os.environ.get('MQTTPASSWORD', ''),
            "enable_tls": req.get("mqtt_enabletls","1"),
            "VIPERTOKEN": VIPERTOKEN,
            "VIPERHOST":  VIPERHOST,
            "VIPERPORT": VIPERPORT,
            "default_args": default_args,            
          }         

          with mqtt_lock:  # New lock for MQTT globals (add to scadaglobals.py)
          # Stop existing MQTT thread
            if sg.mqtt_thread and sg.mqtt_thread.is_alive():
              sg.mqtt_job["stop"] = True
              sg.mqtt_client.disconnect()
#              sg.mqtt_thread.join(timeout=2.0)

            # Helper to send optional payloads
            def post_if_payload(key: str, endpoint: str) -> None:
                payload = req.get(key, {})
                if payload:
                    try:
                        u = endpoint
                        requests.post(u.strip(), json=payload, timeout=5.0)
                    except Exception as e:
                        print(f"Error: cannot send {key} post in scada modbus: {e}")
                        writeviperlogs("ERROR",f"cannot send {key} post in scada modbus: {e}",VIPERTOKEN,VIPERHOST,VIPERPORT)                            
        
            post_if_payload("preprocessing", f"{baseurl}/api/v1/preprocess")
            post_if_payload("machinelearning", f"{baseurl}/api/v1/ml")
            post_if_payload("predictions", f"{baseurl}/api/v1/predict")
            post_if_payload("agenticai", f"{baseurl}/api/v1/agenticai")              
            post_if_payload("ai", f"{baseurl}/api/v1/ai")                            
            
            sg.mqtt_job = {"stop": False, "job_id": job_id}
            sg.mqtt_thread = threading.Thread(
               target=mq.mqttserverconnect_threaded,  # Your function, modified below
               args=(mqtt_cfg, job_id),
               daemon=False
             )
            sg.mqtt_thread.start()

            # Keep this thread alive as long as the job is running
    
          return {
            "message": "MQTT subscription started",
            "job_id": job_id            
          }
      
         except Exception as e:
            print("❌ JSON ERROR:", str(e))
            return {"error": f"JSON parse failed: {str(e)}"}
####################################################################################################      
      
        @app.post('/api/v1/jsondataline')
        def storejsondataline(jdata: dict):
#          jdata = request.get_json()
          topic = jdata.get('sendtotopic','')            
          jdata = json.dumps(jdata)
          readdata(jdata,VIPERTOKEN,VIPERHOST,VIPERPORT,topic)
          return "ok"
    
        @app.post('/api/v1/jsondataarray')
        def storejsondataarray(jdata: List[dict]):    
#          jdata = request.get_json()
          
          for item in jdata: 
             topic = item.get('sendtotopic','')                        
             item = json.dumps(item)            
             readdata(item,VIPERTOKEN,VIPERHOST,VIPERPORT,topic)
          return "ok"      

####################################################################################################
        @app.post('/api/v1/health')
        def tmux_health_check_json() -> Dict[str, Any]:
            def run_tmux(cmd):
                try:
                    result = subprocess.run(['tmux'] + cmd, capture_output=True, text=True, timeout=10)
                    return result.stdout.strip()
                except:
                    return ""
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "sessions": [],
                "summary": {
                    "total_plugin_windows": 0,
                    "error_count": 0,
                    "healthy": True
                }
            }
            
            # Get clean session list
            sessions_raw = run_tmux(['ls', '-F', '#{session_name}']) or run_tmux(['list-sessions', '-F', '#{session_name}'])
            sessions = [s.strip() for s in sessions_raw.split('\n') if s.strip()]
            
            crash_patterns = [r'panic[:\s]', r'fatal\s+error', r'segmentation.*fault', 
                             r'SIGSEGV', r'runtime\s+error', r'goroutine\s+panic', 
                             r'signal:.*killed', r'signal:.*abrt']
            
            for session_name in sessions:
                # ✅ FIX 1: Check if SESSION starts with plugin_
                is_plugin_session = session_name.startswith('plugin_')
                session_name_user ="n/a"
                if is_plugin_session:
                  session_name_user=session_name.split("_")[1]
                  
                session_data = {
                    "name": session_name,
                    "user_session": session_name_user, 
                    "is_plugin_session": is_plugin_session,
                    "plugin_windows": [],
                    "status": "healthy",
                    "plugin_window_count": 0
                }
                
                # Get windows for this session
                windows_raw = run_tmux(['list-windows', '-t', session_name, 
                                       '-F', '#{window_index}:#{window_name}'])
                windows = [w for w in windows_raw.split('\n') if ':' in w]
                
                # ✅ FIX 2: Include ANY window starting with plugin_ OR session is plugin_
                plugin_windows = []
                for win in windows:
                    win_index, win_name = win.split(':', 1)
                    # Check if WINDOW starts with plugin_ OR SESSION is plugin_
                    #if win_name.startswith('plugin_') or is_plugin_session:
                    plugin_windows.append((win_index, win_name))
                
                # Process plugin windows
                for win_index, win_name in plugin_windows:
                    result["summary"]["total_plugin_windows"] += 1
                    session_data["plugin_window_count"] += 1
                    
                    pane_content = run_tmux(['capture-pane', '-t', f'{session_name}:{win_index}.0', 
                                           '-S', '-1000', '-e', '-q'])
                    
                    crashes = [line.strip() for line in pane_content.split('\n') 
                              if any(re.search(p, line, re.IGNORECASE) for p in crash_patterns)]
                    
                    window_data = {
                        "index": win_index,
                        "name": win_name,
                        "status": "healthy" if not crashes else "crashed",
                        "crash_lines": crashes[:5]
                    }
                    
                    if crashes:
                        result["summary"]["error_count"] += 1
                        session_data["status"] = "unhealthy"
                        result["summary"]["healthy"] = False
                    
                    session_data["plugin_windows"].append(window_data)
                
                # ✅ FIX 3: Include ANY session with plugin activity
                if session_data["plugin_window_count"] > 0 or is_plugin_session:
                    result["sessions"].append(session_data)
          
            writeviperlogs("INFO",f"{result}",VIPERTOKEN,VIPERHOST,VIPERPORT)                            
            
            return result


      
####################################################################################################      
        #app.run(port=default_args['rest_port']) # for dev
        if os.environ['TSS']=="0": 
          try:  
            #http_server = WSGIServer(('', int(default_args['rest_port'])), app)

            uvicorn.run(
              app,  # Replace 'your_file_name' with actual filename
              host="0.0.0.0",
              port=int(default_args['rest_port']),
              log_level="info",
              reload=False  # Disable reload in production
            )

          except Exception as e:
           tsslogging.locallogs("ERROR", "STEP 3: Cannot connect to WSGIServer in {} - {}".format(os.path.basename(__file__),e))
                
           tsslogging.tsslogit("ERROR: Cannot connect to WSGIServer in {}".format(os.path.basename(__file__)), "ERROR" )                     
 #          tsslogging.git_push("/{}".format(repo),"Entry from {} - {}".format(os.path.basename(__file__),e),"origin")        
           print("ERROR: Cannot connect to  WSGIServer") 
           writeviperlogs("ERROR",f"Cannot start TML Plugin server: {e}",VIPERTOKEN,VIPERHOST,VIPERPORT)                            
           return             
        else:
          try:  
            print("Listening")  
            writeviperlogs("INFO","TML Plugin Server Started",VIPERTOKEN,VIPERHOST,VIPERPORT)                            
            #http_server = WSGIServer(('', int(default_args['tss_rest_port'])), app)

            uvicorn.run(
               app,  # Replace 'your_file_name' with actual filename
               host="0.0.0.0",
               port=int(default_args['tss_rest_port']),
               log_level="info",
               reload=False  # Disable reload in production
            )
          except Exception as e:
           tsslogging.locallogs("ERROR", "STEP 3: Cannot connect to WSGIServer in {} - {}".format(os.path.basename(__file__),e))                                
           tsslogging.tsslogit("ERROR: Cannot connect to WSGIServer in {}".format(os.path.basename(__file__)), "ERROR" )                     
#           tsslogging.git_push("/{}".format(repo),"Entry from {} - {}".format(os.path.basename(__file__),e),"origin")        
           print("ERROR: Cannot connect to  WSGIServer") 
           writeviperlogs("ERROR",f"Cannot start plugin server: {e}",VIPERTOKEN,VIPERHOST,VIPERPORT)                            
           return             
            
        tsslogging.locallogs("INFO", "STEP 3: RESTAPI HTTP Server started ... successfully")
#        http_server.serve_forever()        

     #return [VIPERTOKEN,VIPERHOST,VIPERPORT]
        
def readdata(valuedata,VIPERTOKEN, VIPERHOST, VIPERPORT,topic=''):
      args = default_args    

      # MAin Kafka topic to store the real-time data
      if topic=='':
        maintopic = args['topics']
      else:
        maintopic = topic
  
      producerid = args['producerid']
      try:
          producetokafka(valuedata, "", "",producerid,maintopic,"",args,VIPERTOKEN, VIPERHOST, VIPERPORT)
          # change time to speed up or slow down data   
          #time.sleep(0.15)
      except Exception as e:
          print(e)  
          pass  

def windowname(wtype,sname,dagname):
    randomNumber = random.randrange(10, 9999)
    wn = "python-{}-{}-{},{}".format(wtype,randomNumber,sname,dagname)
    with open("/tmux/pythonwindows_{}.txt".format(sname), 'a', encoding='utf-8') as file: 
      file.writelines("{}\n".format(wn))
    
    return wn

def startproducing(**context):
       global VIPERTOKEN, VIPERHOST, VIPERPORT, HTTPADDR 
       sd = context['dag'].dag_id
       sname=context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_solutionname".format(sd))
       pname=context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_projectname".format(sd))

       VIPERTOKEN = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERTOKEN".format(sname))
       VIPERHOST = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERHOSTPRODUCE".format(sname))
       VIPERPORT = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERPORTPRODUCE".format(sname))
       HTTPADDR = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_HTTPADDR".format(sname))

       tsslogging.locallogs("INFO", "STEP 3: producing data started")

       chip = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_chip".format(sname)) 
       
       repo=tsslogging.getrepo() 
       if sname != '_mysolution_':
        fullpath="/{}/tml-airflow/dags/tml-solutions/{}/{}".format(repo,pname,os.path.basename(__file__))  
       else:
         fullpath="/{}/tml-airflow/dags/{}".format(repo,os.path.basename(__file__))  
            
       hs,VIPERHOSTFROM=tsslogging.getip(VIPERHOST)     
       ti = context['task_instance']
       ti.xcom_push(key="{}_PRODUCETYPE".format(sname),value='REST')
       ti.xcom_push(key="{}_TOPIC".format(sname),value=default_args['topics'])
       if os.environ['TSS']=="0": 
         ti.xcom_push(key="{}_CLIENTPORT".format(sname),value="_{}".format(default_args['rest_port']))
       else:
         ti.xcom_push(key="{}_CLIENTPORT".format(sname),value="_{}".format(default_args['tss_rest_port']))

       ti.xcom_push(key="{}_TSSCLIENTPORT".format(sname),value="_{}".format(default_args['tss_rest_port']))  
       ti.xcom_push(key="{}_TMLCLIENTPORT".format(sname),value="_{}".format(default_args['rest_port']))  
            
       ti.xcom_push(key="{}_IDENTIFIER".format(sname),value=default_args['identifier'])
       ti.xcom_push(key="{}_FROMHOST".format(sname),value="{},{}".format(hs,VIPERHOSTFROM))
       ti.xcom_push(key="{}_TOHOST".format(sname),value=VIPERHOST)
    
       ti.xcom_push(key="{}_PORT".format(sname),value="_{}".format(VIPERPORT))
       ti.xcom_push(key="{}_HTTPADDR".format(sname),value=HTTPADDR)
                 
       wn = windowname('produce',sname,sd)      
       subprocess.run(["tmux", "new", "-d", "-s", "{}".format(wn)])
       subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "cd /Viper-produce", "ENTER"])
       subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "python {} 1 {} {}{} {}".format(fullpath,VIPERTOKEN,HTTPADDR,VIPERHOSTFROM,VIPERPORT[1:]), "ENTER"])        
        
if __name__ == '__main__':
    
    if len(sys.argv) > 1:
       if sys.argv[1] == "1":          
         VIPERTOKEN = sys.argv[2]
         VIPERHOST = sys.argv[3] 
         VIPERPORT = sys.argv[4]
         os.environ['VIPERTOKEN']=VIPERTOKEN
         os.environ['VIPERHOST']=VIPERHOST
         os.environ['VIPERPORT']=VIPERPORT
        
         gettmlsystemsparams()
