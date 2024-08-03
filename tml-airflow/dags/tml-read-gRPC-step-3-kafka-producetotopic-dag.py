import maadstml
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from datetime import datetime
from airflow.decorators import dag, task
import grpc
from concurrent import futures
import time
import tml_grpc_pb2_grpc as pb2_grpc
import tml_grpc_pb2 as pb2

import sys

sys.dont_write_bytecode = True
##################################################  gRPC SERVER ###############################################
# This is a gRPCserver that will handle connections from a client
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
  'gRPC_Port' : 9001,  # <<< ***** replace with gRPC port i.e. this gRPC server listening on port 9001 
  'delay' : 7000, # << ******* 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic
  'topicid' : -999, # <<< ********* do not modify          
  'start_date': datetime (2024, 6, 29),
  'retries': 1,
    
}

######################################## USER CHOOSEN PARAMETERS ########################################

    
######################################## START DAG AND TASK #############################################

# Instantiate your DAG
@dag(dag_id="tml-read-gRPC-step-3-kafka-producetotopic-dag", default_args=default_args, tags=["tml-read-gRPC-step-3-kafka-producetotopic-dag"], schedule=None,catchup=False)
def startproducingtotopic():
  # This sets the lat/longs for the IoT devices so it can be map
  VIPERTOKEN=""
  VIPERHOST=""
  VIPERPORT=""

  class TmlprotoService(pb2_grpc.TmlprotoServicer):

    def __init__(self, *args, **kwargs):
        pass

    def GetServerResponse(self, request, context):

        # get the string from the incoming request
        message = request.message
        readata(message)
        #result = f'Hello I am up and running received "{message}" message from you'
        #result = {'message': result, 'received': True}

        #return pb2.MessageResponse(**result)
    
  @task(task_id="serve")  
  def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_UnaryServicer_to_server(UnaryService(), server)
    server.add_insecure_port("[::]:{}".format(default_args['gRPC_Port']))
    server.start()
    server.wait_for_termination()
    
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
    VIPERTOKEN = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="VIPERTOKEN")
    VIPERHOST = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="VIPERHOST")
    VIPERPORT = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="VIPERPORT")
    
    return [VIPERTOKEN,VIPERHOST,VIPERPORT]
        
          
  def readdata(valuedata):
      args = default_args
      # MAin Kafka topic to store the real-time data
      maintopic = args['topics']
      producerid = args['producerid']
    
      try:
          producetokafka(valuedata.strip(), "", "",producerid,maintopic,"",args)
          # change time to speed up or slow down data   
          time.sleep(0.15)
      except Exception as e:
          print(e)  
          pass  
  
    
  serve()
    

dag = startproducingtotopic()
