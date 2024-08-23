import maadstml
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import json
from datetime import datetime
from airflow.decorators import dag, task
from flask import Flask
import sys
import tsslogging
import os

sys.dont_write_bytecode = True
##################################################  REST API SERVER #####################################
# This is a REST API server that will handle connections from a client
# There are two endpoints you can use to stream data to this server:
# 1. jsondataline -  You can POST a single JSONs from your client app. Your json will be streamed to Kafka topic.
# 2. jsondataarray -  You can POST JSON arrays from your client app. Your json will be streamed to Kafka topic.


######################################## USER CHOOSEN PARAMETERS ########################################
default_args = {
  'owner' : 'Sebastian Maurice',    
  'enabletls': 1,
  'microserviceid' : '',
  'producerid' : 'iotsolution',  
  'topics' : 'iot-raw-data', # *************** This is one of the topic you created in SYSTEM STEP 2
  'identifier' : 'TML solution',  
  'rest_port' : 9001,  # <<< ***** replace replace with port number i.e. this is listening on port 9000 
  'delay' : 7000, # << ******* 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic
  'topicid' : -999, # <<< ********* do not modify          
  'start_date': datetime (2024, 6, 29),
  'retries': 1,
    
}

######################################## DO NOT MODIFY BELOW #############################################

# Instantiate your DAG
@dag(dag_id="tml_read_RESTAPI_step_3_kafka_producetotopic_dag_mytmlsolution4", default_args=default_args, tags=["tml_read_RESTAPI_step_3_kafka_producetotopic_dag_mytmlsolution4"], schedule=None,catchup=False)
def startproducingtotopic():
  # This sets the lat/longs for the IoT devices so it can be map
  VIPERTOKEN=""
  VIPERHOST=""
  VIPERPORT=""
    

  def producetokafka(value, tmlid, identifier,producerid,maintopic,substream,args):
     inputbuf=value     
     topicid=args['topicid']
  
     # Add a 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic 
     delay=args['delay']
     enabletls = args['enabletls']
     identifier = args['identifier']

     try:
        result=maadstml.viperproducetotopic(VIPERTOKEN,VIPERHOST,VIPERPORT,maintopic,producerid,enabletls,delay,'','', '',0,inputbuf,substream,
                                            topicid,identifier)
     except Exception as e:
        print("ERROR:",e)

  @task(task_id="gettmlsystemsparams")         
  def gettmlsystemsparams():

    repo=tsslogging.getrepo()  
    tsslogging.tsslogit("RESTAPI producing DAG in {}".format(os.path.basename(__file__)), "INFO" )                     
    tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")            
        
    VIPERTOKEN = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="VIPERTOKEN")
    VIPERHOST = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="VIPERHOST")
    VIPERPORT = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="VIPERPORT")

    ti.xcom_push(key='PRODUCETYPE',value='REST')
    ti.xcom_push(key='TOPIC',value=default_args['topics'])
    ti.xcom_push(key='PORT',value=default_args['rest_port'])
    ti.xcom_push(key='IDENTIFIER',value=default_args['identifier'])

    if VIPERHOST != "":
        app = Flask(__name__)
        app.run(port=default_args['rest_port'])

        @app.route('/jsondataline', methods=['POST'])
        def storejsondataline():
          jdata = request.get_json()
          readdata(jdata)

        @app.route('/jsondataarray', methods=['POST'])
        def storejsondataarray():    
          jdata = request.get_json()
          json_array = json.load(jdata)
          for item in json_array: 
             readdata(item)
        

     #return [VIPERTOKEN,VIPERHOST,VIPERPORT]
        
  def readdata(valuedata):
      args = default_args    

      # MAin Kafka topic to store the real-time data
      maintopic = args['topics']
      producerid = args['producerid']
      try:
          producetokafka(valuedata.strip(), "", "",producerid,maintopic,"",args)
          # change time to speed up or slow down data   
          #time.sleep(0.15)
      except Exception as e:
          print(e)  
          pass  
  
dag = startproducingtotopic()
