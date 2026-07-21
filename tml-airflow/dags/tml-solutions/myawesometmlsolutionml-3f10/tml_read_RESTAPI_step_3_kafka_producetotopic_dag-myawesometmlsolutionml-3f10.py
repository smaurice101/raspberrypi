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
  "ingestion_settings": {
    "active_system": "", # You can specify: kafka, rabbitmq, redis, scada, splunk, elasticsearch, clickhouse, influxdb, logstash
    "polling_interval_seconds": 1.0,
    "max_batch_size": 10,
    "strict_json_validation": True
  },
  "systems": {
    "kafka": {
      "proxy_url": "https://secure-kafka-proxy.local:8443",
      "consumer_group": "threat_agent_group",
      "instance_name": "agent_01",
      "topic_name": "iot-raw-data",               # Added to fix KeyError
      "output_stream_topic": "iot-raw-data",       # Added for maadstml output routing
      "rollback_target_offset": -1,                # Matches 'topicid': '-999' fallback rules
      "payload_key_path": ["value"],
      "security": {
        "auth_type": "bearer",
        "token": "CLOUD_SECRET_TOKEN_ABC123",
        "verify_ssl": True,
        "custom_ca_cert_path": "/raspberrypitss/certs/server_ca.crt",
        "mtls": {
          "enabled": True,
          "client_cert_path": "/raspberrypitss/certs/client_agent.crt",
          "client_key_path": "/raspberrypitss/certs/client_agent.key"
        }
      }
    },
    "rabbitmq": {
      "management_url": "http://localhost:15672",
      "queue_name": "siem_alerts",
      "virtual_host": "%2F",
      "payload_key_path": ["payload"],
      "security": {
        "auth_type": "basic",
        "username": "guest",
        "password": "secure_password_here",
        "verify_ssl": False
      }
    },
    "redis": {
      "webdis_url": "http://localhost:7379",
      "redis_command": "GET",
      "key_name": "threat_intel_baseline",
      "security": {
        "auth_type": "custom_header",
        "header_name": "X-Webdis-Token",
        "header_value": "secret-proxy-token-abc123",
        "verify_ssl": False
      }
    },
    "scada": {
      "scada_url": "http://scada-gateway.local:8088",
      "endpoint": "/api/v1/tags/assembly_line_1",
      "security": {
        "auth_type": "none",
        "verify_ssl": False
      }
    },
    "splunk": {
      "management_url": "https://splunk-server.local:8089",
      "search_query": "search index=security_alerts sourcetype=json | head 10",
      "security": {
        "auth_type": "bearer",
        "token": "YOUR_SPLUNK_SESSION_OR_HEC_TOKEN",
        "verify_ssl": True
      }
    },
    "elasticsearch": {
      "node_url": "https://elasticsearch-node.local:9200",
      "index_pattern": "security-logs-*",
      "search_body": {
        "query": { "match_all": {} },
        "size": 10
      },
      "root_array_path": ["hits", "hits"],
      "payload_key_path": ["_source"],
      "security": {
        "auth_type": "basic",
        "username": "elastic",
        "password": "changeme",
        "verify_ssl": True
      }
    },
    "clickhouse": {
      "http_url": "https://clickhouse-server.local:8443",
      "query": "SELECT * FROM security.events ORDER BY timestamp DESC LIMIT 10 FORMAT JSON",
      "database": "security",
      "root_array_path": ["data"],
      "security": {
        "auth_type": "custom_header",
        "header_name": "X-ClickHouse-User",
        "header_value": "analyst_user",
        "verify_ssl": True
      }
    },
    "influxdb": {
      "host_url": "https://influxdb.local:8086",
      "org": "security_operations",
      "flux_query": "from(bucket: \"threat_metrics\") |> range(start: -5m) |> limit(n: 10)",
      "security": {
        "auth_type": "bearer",
        "token": "YOUR_INFLUXDB_API_TOKEN",
        "verify_ssl": True
      }
    },
    "logstash": {
      "http_input_url": "http://logstash.local:8080",
      "endpoint": "/status",
      "security": {
        "auth_type": "none",
        "verify_ssl": False
      }
    }
  }
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

def gettmlsystemsparams():
    repo=tsslogging.getrepo()  
    tsslogging.tsslogit("RESTAPI producing DAG in {}".format(os.path.basename(__file__)), "INFO" )                     
    tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")            
        
    if VIPERHOST != "":
        app = Flask(__name__)
                 
        app.config['VIPERTOKEN'] = os.environ['VIPERTOKEN']
        app.config['VIPERHOST'] = os.environ['VIPERHOST']
        app.config['VIPERPORT'] = os.environ['VIPERPORT']
                
               
        @app.route(rule='/jsondataline', methods=['POST'])
        def storejsondataline():
          jdata = request.get_json()
          readdata(jdata,app.config['VIPERTOKEN'],app.config['VIPERHOST'],app.config['VIPERPORT'])
          return "ok"
    
        @app.route(rule='/jsondataarray', methods=['POST'])
        def storejsondataarray():    
          jdata = request.get_json()
          json_array = json.load(jdata)
          for item in json_array: 
             readdata(item,app.config['VIPERTOKEN'],app.config['VIPERHOST'],app.config['VIPERPORT'])
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
        
def readdata(valuedata,VIPERTOKEN, VIPERHOST, VIPERPORT):
      args = default_args    

      # MAin Kafka topic to store the real-time data
      maintopic = args['topics']
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
        
         if default_args["ingestion_settings"]["active_system"] != "":
           tsslogging.startstreamengine(default_args, VIPERHOST, VIPERPORT, VIPERTOKEN)
         else:
         # start the FastAPI sever
           gettmlsystemsparams()
