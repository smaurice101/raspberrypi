import maadstml
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import json
from datetime import datetime
from airflow.decorators import dag, task
from flask import Flask, request, jsonify, session
from gevent.pywsgi import WSGIServer
import sys
import tsslogging
import os
import subprocess
import time
import random

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
  'rest_port' : '9001',  # <<< ***** replace replace with port number i.e. this is listening on port 9000 
  'delay' : '7000', # << ******* 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic
  'topicid' : '-999', # <<< ********* do not modify              
}

######################################## DO NOT MODIFY BELOW #############################################

# Instantiate your DAG
@dag(dag_id="tml_read_RESTAPI_step_3_kafka_producetotopic_dag_myawesometmlsolution", default_args=default_args, tags=["tml_read_RESTAPI_step_3_kafka_producetotopic_dag_myawesometmlsolution"],schedule=None,catchup=False)
def startproducingtotopic():
   def empty():
     pass
    
dag = startproducingtotopic()

VIPERTOKEN=""
VIPERHOST=""
VIPERPORT=""
HTTPADDR="https://"    

def producetokafka(value, tmlid, identifier,producerid,maintopic,substream,args,VIPERTOKEN, VIPERHOST, VIPERPORT):
     inputbuf=value     
     topicid=int(args['topicid'])
  
     # Add a 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic 
     delay=int(args['delay'])
     enabletls = int(args['enabletls'])
     identifier = args['identifier']
     print("VIPERPORT=",VIPERPORT,VIPERHOST)
     VIPERPORT=1121
     VIPERHOST="https://127.0.0.1"   
        
     try:
        result=maadstml.viperproducetotopic(VIPERTOKEN,VIPERHOST,VIPERPORT,maintopic,producerid,enabletls,delay,'','', '',0,inputbuf,substream,
                                            topicid,identifier)
     except Exception as e:
        print("ERROR:",e)

def gettmlsystemsparams(VIPERTOKEN,VIPERHOST,VIPERPORT):
    repo=tsslogging.getrepo()  
    tsslogging.tsslogit("RESTAPI producing DAG in {}".format(os.path.basename(__file__)), "INFO" )                     
    tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")            
        
    if VIPERHOST != "":
        app = Flask(__name__)
        app.config['VIPERTOKEN'] = VIPERTOKEN
        app.config['VIPERHOST'] = VIPERHOST
        app.config['VIPERPORT'] = VIPERPORT
        
        @app.route(rule='/jsondataline', methods=['POST'])
        def storejsondataline():
          jdata = request.get_json()
          readdata(jdata,os.environ['VIPERTOKEN'],os.environ['VIPERHOST'],os.environ['VIPERPORT'])
          return "ok"
    
        @app.route(rule='/jsondataarray', methods=['POST'])
        def storejsondataarray():    
          jdata = request.get_json()
          json_array = json.load(jdata)
          for item in json_array: 
             readdata(item,os.environ['VIPERTOKEN'],os.environ['VIPERHOST'],os.environ['VIPERPORT'])
          return "ok"      
        
        #app.run(port=default_args['rest_port']) # for dev
        http_server = WSGIServer(('', int(default_args['rest_port'])), app)
        http_server.serve_forever()        

     #return [VIPERTOKEN,VIPERHOST,VIPERPORT]
        
def readdata(valuedata,VIPERTOKEN, VIPERHOST, VIPERPORT):
      args = default_args    

      # MAin Kafka topic to store the real-time data
      maintopic = args['topics']
      producerid = args['producerid']
      try:
          producetokafka(valuedata.strip(), "", "",producerid,maintopic,"",args,VIPERTOKEN, VIPERHOST, VIPERPORT)
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
       VIPERTOKEN = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERTOKEN".format(sname))
       VIPERHOST = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERHOSTPRODUCE".format(sname))
       VIPERPORT = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERPORTPRODUCE".format(sname))
       HTTPADDR = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_HTTPADDR".format(sname))

       ti = context['task_instance']
       ti.xcom_push(key="{}_PRODUCETYPE".format(sname),value='REST')
       ti.xcom_push(key="{}_TOPIC".format(sname),value=default_args['topics'])
       ti.xcom_push(key="{}_PORT".format(sname),value=default_args['rest_port'])
       ti.xcom_push(key="{}_IDENTIFIER".format(sname),value=default_args['identifier'])
        
       chip = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_chip".format(sname)) 
       
       repo=tsslogging.getrepo() 
       if sname != '_mysolution_':
        fullpath="/{}/tml-airflow/dags/tml-solutions/{}/{}".format(repo,sname,os.path.basename(__file__))  
       else:
         fullpath="/{}/tml-airflow/dags/{}".format(repo,os.path.basename(__file__))  
            
       wn = windowname('produce',sname,sd)      
       subprocess.run(["tmux", "new", "-d", "-s", "{}".format(wn)])
       subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "cd /Viper-produce", "ENTER"])
       subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "python {} 1 {} {}{} {}".format(fullpath,VIPERTOKEN,HTTPADDR,VIPERHOST,VIPERPORT[1:]), "ENTER"])        
        
if __name__ == '__main__':
    
    if len(sys.argv) > 1:
       if sys.argv[1] == "1":          
         VIPERTOKEN = sys.argv[2]
         VIPERHOST = sys.argv[3] 
         VIPERPORT = sys.argv[4]
         os.environ['VIPERTOKEN']=VIPERTOKEN
         os.environ['VIPERHOST']=VIPERHOST
         os.environ['VIPERPORT']=VIPERPORT
        
         gettmlsystemsparams(VIPERTOKEN,VIPERHOST,VIPERPORT)
