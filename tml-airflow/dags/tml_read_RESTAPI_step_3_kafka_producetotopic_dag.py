import maadstml
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import json
from datetime import datetime
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

    if isnew2:
      time.sleep(5)

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
  
def stopstart(steps,stepsarr,windowinstance='default'):

  pythonrun=''
  step=''
  if steps=='step4':
    step='4'
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
  elif steps=='step5':
    step='5'
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
        print(f"new_pythonrun: {new_pythonrun}")
      
  elif steps=='step6':
    step='6'    
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
  
  if windowinstance=='default':
    subprocess.run(["tmux", "send-keys", "-t", wn, "C-c"])
    subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "{}".format(new_pythonrun), "ENTER"],capture_output=True, text=True)        
  else:  
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
            wt = wt + mw + ","
    wt = wt[:-1]      
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
  else: 
       subprocess.run(['tmux', 'kill-session', '-t', f"plugin_{wn}_{step}"])
       subprocess.run(['tmux', 'kill-session', '-t', f"plugin_{wn}"])    
       wt = wn
  return wt    

def gettmlsystemsparams():
    repo=tsslogging.getrepo()  

  ############################################### API Routes ########################################      

    if VIPERHOST != "":
        app = Flask(__name__)
                 
        app.config['VIPERTOKEN'] = os.environ['VIPERTOKEN']
        app.config['VIPERHOST'] = os.environ['VIPERHOST']
        app.config['VIPERPORT'] = os.environ['VIPERPORT']

#-------------------------------- TERMINATE WINDOW -----------------------------------------------------      
        @app.route(rule='/terminatewindow', methods=['POST'])
        def windowterminate(): 
          jdata = request.get_json()          
          if not jdata:
            return "Missing windows", 400
          
          step = jdata.get('step','')            
          windowname = jdata.get('windowname','')
          
          if windowname != '':
               wd=terminatetmuxwindows(step,windowname)
               return jsonify({
                    'status': f"success: windows terminated: {wd}",
               }), 201

          return jsonify({
              'status': 'success: no windows terminated',
          }), 201

#-------------------------------- CREATETOPIC -----------------------------------------------------      
        @app.route(rule='/createtopic', methods=['POST'])
        def storecreatetopic():
          jdata = request.get_json()          
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
                result=maadstml.vipercreatetopic(app.config['VIPERTOKEN'],app.config['VIPERHOST'],app.config['VIPERPORT'],pt,'companyname',
                                 'myname','myemail','mylocation',description,enabletls,
                                 brokerhost,brokerport,numpartitions,replication,'')
                print(result)
            return jsonify({
              'status': 'success',
              'topics': topics,
              'partitions': numpartitions,
              'replication': replication,
              'description': description
            }), 201
          except Exception as e:
            return jsonify({
              'status': f"error: {e}",
              'topics': topics,
              'partitions': numpartitions,
              'replication': replication,
              'description': description
            }), 400
            
        
#-------------------------------- PREPROCESS -----------------------------------------------------            
        @app.route(rule='/preprocess', methods=['POST'])
        def storepreprocess():
          jdata = request.get_json()          
          if not jdata or not jdata.get('rawdatatopic'):
            return "Missing preprocess or invalid preprocess", 400

          step = jdata.get('step','')  
          try:
           if step=='4':
            step4raw_data_topic = jdata.get('rawdatatopic','')  
            step4preprocess_data_topic = jdata.get('preprocessdatatopic','')
            step4preprocesstypes = jdata.get('preprocesstypes','')
            step4jsoncriteria = jdata.get('jsoncriteria','')  
            rollbackoffset = jdata.get('rollbackoffsets',200)  
            
            windowinstance = jdata.get("windowinstance","default")                        
            step4arr = [step4raw_data_topic,step4preprocesstypes,step4jsoncriteria,step4preprocess_data_topic,rollbackoffset]
            stopstart('step4',step4arr,windowinstance)
            
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
             stopstart('step4c',step4carr,windowinstance)

           return jsonify({
              'status': 'success',
              'step4raw_data_topic': jdata.get('rawdatatopic',''),
              'step4preprocess_data_topic': jdata.get('preprocessdatatopic',''),
              'step4preprocesstypes': jdata.get('preprocesstypes',''),
              'step4jsoncriteria': jdata.get('jsoncriteria',''),
              'rollbackoffset': jdata.get('rollbackoffset',400),            
              'windowinstance': jdata.get("windowinstance","default")                 
              }), 201
          except Exception as e:
           return jsonify({
              'status': f"error:{e}",
              'step4raw_data_topic': jdata.get('rawdatatopic',''),
              'step4preprocess_data_topic': jdata.get('preprocessdatatopic',''),
              'step4preprocesstypes': jdata.get('preprocesstypes',''),
              'step4jsoncriteria': jdata.get('jsoncriteria',''),
              'rollbackoffset': jdata.get('rollbackoffset',400),            
              'windowinstance': jdata.get("windowinstance","default")                 
              }), 201
            
          
#-------------------------------- MACHINE LEARNING -----------------------------------------------------                  
        @app.route(rule='/ml', methods=['POST'])
        def storeml():
          jdata = request.get_json()          
          if not jdata:
            return "Missing ml or invalid ml", 400

          step = jdata.get('step','')  
          try:
            if step==5:
             trainingdatafolder = jdata.get('trainingdatafolder','')  
             ml_data_topic = jdata.get('ml_data_topic','')  
             preprocess_data_topic = jdata.get('preprocess_data_topic','')  
             islogistic = jdata.get('islogistic',0)  
             dependentvariable = jdata.get('dependentvariable','failure')  
             independentvariables = jdata.get('independentvariables','')  
             processlogic = jdata.get('processlogic','')  
             rollbackoffsets = jdata.get('rollbackoffsets',50)  
             windowinstance = jdata.get("windowinstance","default")            
             step5arr = [rollbackoffsets,processlogic,independentvariables,dependentvariable,
                         islogistic,preprocess_data_topic,ml_data_topic,trainingdatafolder]
             stopstart('step5',step5arr,windowinstance)
             return jsonify({
              'status': "success",
              'trainingdatafolder': jdata.get('trainingdatafolder',''),
              'ml_data_topic': jdata.get('ml_data_topic',''),  
              'preprocess_data_topic': jdata.get('preprocess_data_topic',''),
              'islogistic': jdata.get('islogistic',0),
              'dependentvariable': jdata.get('dependentvariable','failure'),
              'independentvariables': jdata.get('independentvariables',''),
              'processlogic': jdata.get('processlogic',''),
              'rollbackoffsets': jdata.get('rollbackoffsets',50),
              'windowinstance': jdata.get("windowinstance","default")                          
              }), 201    
          except Exception as e:
             return jsonify({
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
              }), 400
              
#-------------------------------- PREDICTIONS -----------------------------------------------------                        
        @app.route(rule='/predict', methods=['POST'])
        def predictdata():
          jdata = request.get_json()          
          if not jdata:
            return "Missing ml or invalid prediction", 400
          
          step = jdata.get('step','')  

          try:
            if step==6:
             pathtoalgos = jdata.get('pathtoalgos','')  
             maxrows = jdata.get('rollbackoffsets',50)  
             consumefrom = jdata.get('consumefrom','')  
             inputdata = jdata.get('inputdata','')  
             streamstojoin = jdata.get('streamstojoin','')  
             ml_prediction_topic = jdata.get('ml_prediction_topic','')  
             preprocess_data_topic = jdata.get('preprocess_data_topic','')  
             windowinstance = jdata.get("windowinstance","default")            
             step6arr = [maxrows,preprocess_data_topic,ml_prediction_topic,streamstojoin,inputdata,consumefrom,pathtoalgos]
             stopstart('step6',step6arr,windowinstance)
             return jsonify({
              'status': "success",
               'pathtoalgos': jdata.get('pathtoalgos',''),
               'maxrows': jdata.get('rollbackoffsets',50), 
               'consumefrom': jdata.get('consumefrom',''), 
               'inputdata': jdata.get('inputdata',''),
               'streamstojoin': jdata.get('streamstojoin',''),  
               'ml_prediction_topic': jdata.get('ml_prediction_topic',''),  
               'preprocess_data_topic': jdata.get('preprocess_data_topic',''),  
               'windowinstance': jdata.get("windowinstance","default")    
              }), 201          
          except Exception as e:
             return jsonify({
              'status': f"error:{e}",
               'pathtoalgos': jdata.get('pathtoalgos',''),
               'maxrows': jdata.get('rollbackoffsets',50), 
               'consumefrom': jdata.get('consumefrom',''), 
               'inputdata': jdata.get('inputdata',''),
               'streamstojoin': jdata.get('streamstojoin',''),  
               'ml_prediction_topic': jdata.get('ml_prediction_topic',''),  
               'preprocess_data_topic': jdata.get('preprocess_data_topic',''),  
               'windowinstance': jdata.get("windowinstance","default")    
              }), 400
    
#-------------------------------- CONSUME -----------------------------------------------------                        
        @app.route(rule='/consume', methods=['POST'])
        def consumedata():
          jdata = request.get_json()          
          osdu = jdata.get('osdu','false')
          kind = jdata.get('kind','tml')  

          if not jdata or not jdata.get('topic'):
            if osdu=='false':
              return "Missing ml or invalid consume", 400
            else:
              return jsonify({
                  "kind": f"{kind}",
                  "id": "consume-error",
                  "error": {
                      "code": 400,
                      "message": "Missing topic or invalid consume request",
                      "reason": "Topic parameter required"
                  }
              }), 400              
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
                return jsonify(response), 200
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
               response['forward_statuses'] = forward_statuses                   
               return jsonify(response), 200
           except Exception as e:
               print("Error=",e)
               return jsonify({"error": f"Consumption failed: {e}"}), 500
             
  #         return result      
####################################################################################################      
      
        @app.route(rule='/jsondataline', methods=['POST'])
        def storejsondataline():
          jdata = request.get_json()
          topic = jdata.get('sendtotopic','')            
          jdata = json.dumps(jdata)
          readdata(jdata,app.config['VIPERTOKEN'],app.config['VIPERHOST'],app.config['VIPERPORT'],topic)
          return "ok"
    
        @app.route(rule='/jsondataarray', methods=['POST'])
        def storejsondataarray():    
          jdata = request.get_json()
          
          for item in json_array: 
             topic = item.get('sendtotopic','')                        
             item = json.dumps(item)            
             readdata(item,app.config['VIPERTOKEN'],app.config['VIPERHOST'],app.config['VIPERPORT'],topic)
          return "ok"      
        
        #app.run(port=default_args['rest_port']) # for dev
        if os.environ['TSS']=="0": 
          try:  
            http_server = WSGIServer(('', int(default_args['rest_port'])), app)
          except Exception as e:
           tsslogging.locallogs("ERROR", "STEP 3: Cannot connect to WSGIServer in {} - {}".format(os.path.basename(__file__),e))
                
           tsslogging.tsslogit("ERROR: Cannot connect to WSGIServer in {}".format(os.path.basename(__file__)), "ERROR" )                     
           tsslogging.git_push("/{}".format(repo),"Entry from {} - {}".format(os.path.basename(__file__),e),"origin")        
           print("ERROR: Cannot connect to  WSGIServer") 
           return             
        else:
          try:  
            print("Listening")  
            http_server = WSGIServer(('', int(default_args['tss_rest_port'])), app)
          except Exception as e:
           tsslogging.locallogs("ERROR", "STEP 3: Cannot connect to WSGIServer in {} - {}".format(os.path.basename(__file__),e))                                
           tsslogging.tsslogit("ERROR: Cannot connect to WSGIServer in {}".format(os.path.basename(__file__)), "ERROR" )                     
           tsslogging.git_push("/{}".format(repo),"Entry from {} - {}".format(os.path.basename(__file__),e),"origin")        
           print("ERROR: Cannot connect to  WSGIServer") 
           return             
            
        tsslogging.locallogs("INFO", "STEP 3: RESTAPI HTTP Server started ... successfully")
        http_server.serve_forever()        

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
