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
import tsslogging
import sys
import os
import subprocess
import random

sys.dont_write_bytecode = True
##################################################  gRPC SERVER ###############################################
# This is a gRPCserver that will handle connections from a client
# There are two endpoints you can use to stream data to this server:
# 1. jsondataline -  You can POST a single JSONs from your client app. Your json will be streamed to Kafka topic.
# 2. jsondataarray -  You can POST JSON arrays from your client app. Your json will be streamed to Kafka topic.

######################################## USER CHOOSEN PARAMETERS ########################################
default_args = {
  'owner' : 'Sebastian Maurice', # <<< *** Change as needed
  'enabletls': '1', # <<< *** 1=connection is encrypted, 0=no encryption
  'microserviceid' : '', # <<< ***** leave blank
  'producerid' : 'iotsolution',  # <<< *** Change as needed
  'topics' : 'iot-raw-data', # *************** This is one of the topic you created in SYSTEM STEP 2
  'identifier' : 'TML solution',  # <<< *** Change as needed
  'tss_gRPC_Port' : '9001',  # <<< ***** replace with gRPC port i.e. this gRPC server listening on port 9001     
  'gRPC_Port' : '9002',  # <<< ***** replace with gRPC port i.e. this gRPC server listening on port 9001 
  'delay' : '7000', # << ******* 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic
  'topicid' : '-999', # <<< ********* do not modify              
}
    
######################################## DO NOT MODIFY BELOW #############################################

# Instantiate your DAG
@dag(dag_id="tml_read_gRPC_step_3_kafka_producetotopic_dag_myawesometmlsolution-3f10", default_args=default_args, tags=["tml_read_gRPC_step_3_kafka_producetotopic_dag_myawesometmlsolution-3f10"], schedule=None,catchup=False)
def startproducingtotopic():
  # This sets the lat/longs for the IoT devices so it can be map
  def empty():
      pass

dag = startproducingtotopic()

VIPERTOKEN=""
VIPERHOST=""
VIPERPORT=""
HTTPADDR=""
VIPERHOSTFROM=""

class TmlprotoService(pb2_grpc.TmlprotoServicer):

  def __init__(self, *args, **kwargs):
    pass

  def GetServerResponse(self, request, context):

    # get the string from the incoming request
    #print(pb2.MessageResponse(**result))
    message = request.message
#    print({message})
    #readata(message)
    result = f'Hello I am up and running received "{message}" message from you'
    result = {'message': result, 'received': True}
    print(result)
#    print(pb2.MessageResponse(**result))
    #return pb2.MessageResponse(**result)
  def readdata(self,valuedata):
    args = default_args
  # MAin Kafka topic to store the real-time data
    maintopic = args['topics']
    producerid = args['producerid']

    try:
      producetokafka(valuedata, "", "",producerid,maintopic,"",args)
      # change time to speed up or slow down data
      time.sleep(0.15)
    except Exception as e:
      print(e)
      pass

  def producetokafka(self,value, tmlid, identifier,producerid,maintopic,substream,args):
    inputbuf=value
    topicid=args['topicid']

 # Add a 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topi> delay=int(args['delay'])
    enabletls = int(args['enabletls'])
    identifier = args['identifier']

    try:
      result=maadstml.viperproducetotopic(VIPERTOKEN,VIPERHOST,VIPERPORT,maintopic,producerid,enabletls,delay,'','', '',0,inputbuf,s>
                                        topicid,identifier)
    except Exception as e:
      print("ERROR:",e)

def serve():
    repo=tsslogging.getrepo()   
    tsslogging.tsslogit("gRPC producing DAG in {}".format(os.path.basename(__file__)), "INFO" )                     
    tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")          

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_TmlprotoServicer_to_server(TmlprotoService(), server)
    if os.environ['TSS']=="0":
      server.add_insecure_port("[::]:{}".format(default_args['gRPC_Port']))
    else:
      server.add_insecure_port("[::]:{}".format(default_args['tss_gRPC_Port']))
    
    server.start()
    server.wait_for_termination()        

def producetokafka(value, tmlid, identifier,producerid,maintopic,substream,args):
 inputbuf=value     
 topicid=args['topicid']

 # Add a 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic 
 delay=int(args['delay'])
 enabletls = int(args['enabletls'])
 identifier = args['identifier']

 try:
    result=maadstml.viperproducetotopic(VIPERTOKEN,VIPERHOST,VIPERPORT,maintopic,producerid,enabletls,delay,'','', '',0,inputbuf,substream,
                                        topicid,identifier)
 except Exception as e:
    print("ERROR:",e)

def readdata(valuedata):
  args = default_args
  # MAin Kafka topic to store the real-time data
  maintopic = args['topics']
  producerid = args['producerid']

  try:
      producetokafka(valuedata, "", "",producerid,maintopic,"",args)
      # change time to speed up or slow down data   
      time.sleep(0.15)
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
       global VIPERTOKEN
       global VIPERHOST
       global VIPERPORT
       global HTTPADDR 
       global VIPERHOSTFROM  
        
       sd = context['dag'].dag_id
       sname=context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_solutionname".format(sd))
    
       VIPERTOKEN = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERTOKEN".format(sname))
       VIPERHOST = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERHOSTPRODUCE".format(sname))
       VIPERPORT = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERPORTPRODUCE".format(sname))
       HTTPADDR = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_HTTPADDR".format(sname))
        
       chip = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_chip".format(sname)) 
       repo=tsslogging.getrepo() 
      
       if sname != '_mysolution_':
        fullpath="/{}/tml-airflow/dags/tml-solutions/{}/{}".format(repo,sname,os.path.basename(__file__))  
       else:
         fullpath="/{}/tml-airflow/dags/{}".format(repo,os.path.basename(__file__))  

       hs,VIPERHOSTFROM=tsslogging.getip(VIPERHOST)     
       ti = context['task_instance']
       ti.xcom_push(key="{}_PRODUCETYPE".format(sname),value='gRPC')
       ti.xcom_push(key="{}_TOPIC".format(sname),value=default_args['topics'])

       if os.environ['TSS']=="0":
        ti.xcom_push(key="{}_CLIENTPORT".format(sname),value="_{}".format(default_args['gRPC_Port']))
       else:
        ti.xcom_push(key="{}_CLIENTPORT".format(sname),value="_{}".format(default_args['tss_gRPC_Port']))

       ti.xcom_push(key="{}_TSSCLIENTPORT".format(sname),value="_{}".format(default_args['tss_gRPC_Port']))  
       ti.xcom_push(key="{}_TMLCLIENTPORT".format(sname),value="_{}".format(default_args['gRPC_Port']))  

       ti.xcom_push(key="{}_IDENTIFIER".format(sname),value=default_args['identifier'])

       ti.xcom_push(key="{}_FROMHOST".format(sname),value="{},{}".format(hs,VIPERHOSTFROM))
       ti.xcom_push(key="{}_TOHOST".format(sname),value=VIPERHOST)

       ti.xcom_push(key="{}_PORT".format(sname),value=VIPERPORT)
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
         serve()
