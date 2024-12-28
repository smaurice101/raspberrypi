import asyncio
import signal
from google.protobuf.json_format import MessageToJson
from grpc_reflection.v1alpha import reflection
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
import json
import nest_asyncio
nest_asyncio.apply()
#from grpc.experimental import aio
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


VIPERTOKEN=""
VIPERHOST=""
VIPERPORT=""
HTTPADDR=""
VIPERHOSTFROM=""


class TmlprotoService(pb2_grpc.TmlprotoServicer):

  def __init__(self, *args, **kwargs):
    pass

  async def GetServerResponse(self, request, context):

    maintopic = default_args['topics']
    producerid = default_args['producerid']


    if request != None:
     try:
      message = json.dumps(json.loads(request.message))
      inputbuf=f"{message}"
      print("inputbuf=",inputbuf)

      topicid=default_args['topicid']

     # Add a 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topi> delay=int(args['delay'])
      enabletls = int(default_args['enabletls'])
      identifier = default_args['identifier']
      delay = int(default_args['delay'])
      try:
        result=maadstml.viperproducetotopic(VIPERTOKEN,VIPERHOST,VIPERPORT,maintopic,producerid,enabletls,delay,'','', '',0,inputbuf,'',
                                            topicid,identifier)
        return pb2.MessageResponse(message="Success producing message",received=True)
      except Exception as e:
        return pb2.MessageResponse(message="Failed to produce message, err={} message={}".format(e,inputbuf),received=False)
     except Exception as e:
      return pb2.MessageResponse(message="Failed to produce message, err={} message={}".format(e,inputbuf),received=False)


    return pb2.MessageResponse(message="Failed to produce message",received=False)

async def serve():


    tsslogging.locallogs("INFO", "STEP 3: producing data started")
    repo=tsslogging.getrepo()
    tsslogging.tsslogit("gRPC producing DAG in {}".format(os.path.basename(__file__)), "INFO" )
    tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")
    mainport=0
    server_options = [
        ("grpc.keepalive_time_ms", 20000),
        ("grpc.keepalive_timeout_ms", 10000),
        ("grpc.http2.min_ping_interval_without_data_ms", 5000),
        ("grpc.max_connection_idle_ms", 10000),
        ("grpc.max_connection_age_ms", 30000),
        ("grpc.max_connection_age_grace_ms", 5000),
        ("grpc.http2.max_pings_without_data", 5),
        ("grpc.keepalive_permit_without_calls", 1),
    ]

    try:
        server = grpc.aio.server(futures.ThreadPoolExecutor(),options=server_options)
#        server = grpc.server(futures.ThreadPoolExecutor(max_workers=100))
        SERVICE_NAMES = (
          pb2.DESCRIPTOR.services_by_name["Tmlproto"].full_name,
          reflection.SERVICE_NAME,
        )
        reflection.enable_server_reflection(SERVICE_NAMES, server)

        pb2_grpc.add_TmlprotoServicer_to_server(TmlprotoService(), server)
        if os.environ['TSS']=="0":
#          server_creds = grpc.alts_server_credentials()
          with open('/{}/tml-airflow/certs/server.key'.format(repo), 'rb') as f:
            server_key = f.read()
          with open('/{}/tml-airflow/certs/server.crt'.format(repo), 'rb') as f:
           server_cert = f.read()
          server_creds = grpc.ssl_server_credentials( [(server_key, server_cert)] )
          mainport=int(default_args['gRPC_Port'])
          server.add_secure_port("[::]:{}".format(int(default_args['gRPC_Port'])), server_creds)

        else:
          server.add_insecure_port("[::]:{}".format(int(default_args['tss_gRPC_Port'])))
          mainport=int(default_args['tss_gRPC_Port'])
    except Exception as e:
           tsslogging.locallogs("ERROR", "STEP 3: Cannot connect to gRPC server in {} - {}".format(os.path.basename(__file__),e))

           tsslogging.tsslogit("ERROR: Cannot connect to gRPC server in {} - {}".format(os.path.basename(__file__),e), "ERROR" )
           tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")
           print("ERROR: Cannot connect to gRPC server in:",e)
           return

    tsslogging.locallogs("INFO", "STEP 3: gRPC server started .. waiting for connections")
    await server.start()
    print("gRPC server started - listening on port ",mainport)
    await server.wait_for_termination()

async def shutdown_server(server) -> None:
    #logging.info ("Shutting down server...")
    await server.stop(None)

def handle_sigterm(sig, frame) -> None:
    asyncio.create_task(shutdown_server(server))

async def handle_sigint() -> None:
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, loop.stop)

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

       tsslogging.locallogs("INFO", "STEP 3: producing data started")

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

       tsslogging.locallogs("INFO", "STEP 3: producing data completed")

if __name__ == '__main__':

    if len(sys.argv) > 1:
       if sys.argv[1] == "1":
         VIPERTOKEN = sys.argv[2]
         VIPERHOST = sys.argv[3]
         VIPERPORT = sys.argv[4]
#         serve()

         server = None
         signal.signal(signal.SIGTERM, handle_sigterm)
         try:
            print("Starting asyncio event loop")
            asyncio.get_event_loop().run_until_complete(serve())
         except KeyboardInterrupt:
           pass






