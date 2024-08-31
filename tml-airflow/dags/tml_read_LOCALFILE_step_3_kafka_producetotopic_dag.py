from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime
from airflow.decorators import dag, task
import sys
import maadstml
import tsslogging
import os
import subprocess

sys.dont_write_bytecode = True
######################################## USER CHOOSEN PARAMETERS ########################################
default_args = {
  'owner' : 'Sebastian Maurice', # <<< *** Change as needed   
  'enabletls': 1, # <<< *** 1=connection is encrypted, 0=no encryption
  'microserviceid' : '', # <<< *** leave blank
  'producerid' : 'iotsolution',   # <<< *** Change as needed   
  'topics' : 'iot-raw-data', # *************** This is one of the topic you created in SYSTEM STEP 2
  'identifier' : 'TML solution',   # <<< *** Change as needed   
  'inputfile' : '/rawdata/IoTData.txt',  # <<< ***** replace ?  to input file name to read. NOTE this data file should be JSON messages per line and stored in the HOST folder mapped to /rawdata folder 
  'delay' : 7000, # << ******* 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic
  'topicid' : -999, # <<< ********* do not modify  
}

######################################## DO NOT MODIFY BELOW #############################################

# Instantiate your DAG
@dag(dag_id="tml_localfile_step_3_kafka_producetotopic_dag", default_args=default_args, tags=["tml_localfile_step_3_kafka_producetotopic_dag"], start_date=datetime(2023, 1, 1),  schedule=None,catchup=False)
def startproducingtotopic():
  def empty():
    pass
dag = startproducingtotopic()

# This sets the lat/longs for the IoT devices so it can be map
VIPERTOKEN=""
VIPERHOST=""
VIPERPORT=""
  
  
def producetokafka(value, tmlid, identifier,producerid,maintopic,substream,args):
 inputbuf=value     
 topicid=args['topicid']

 # Add a 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic 
 delay = args['delay']
 enabletls = args['enabletls']
 identifier = args['identifier']

 try:
    result=maadstml.viperproducetotopic(VIPERTOKEN,VIPERHOST,VIPERPORT,maintopic,producerid,enabletls,delay,'','', '',0,inputbuf,substream,
                                        topicid,identifier)
 except Exception as e:
    print("ERROR:",e)

def readdata(**context):
  VIPERTOKEN = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="VIPERTOKEN")
  VIPERHOST = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="VIPERHOSTPRODUCE")
  VIPERPORT = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="VIPERPORTPRODUCE")

  repo = tsslogging.getrepo()
  tsslogging.tsslogit("Localfile producing DAG in {}".format(os.path.basename(__file__)), "INFO" )                     
  tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")        

  args = default_args  
  inputfile=args['inputfile']

  # MAin Kafka topic to store the real-time data
  maintopic = args['topics']
  producerid = args['producerid']

  k=0
  try:
    file1 = open(inputfile, 'r')
    print("Data Producing to Kafka Started:",datetime.now())
  except Exception as e:
    tsslogging.tsslogit("Localfile producing DAG in {}".format(os.path.basename(__file__)), "INFO" )                     
    tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")        
    return

  while True:
    line = file1.readline()
    line = line.replace(";", " ")
    print("line=",line)
    # add lat/long/identifier
    k = k + 1
    try:
      if line == "":
        #break
        file1.seek(0)
        k=0
        print("Reached End of File - Restarting")
        print("Read End:",datetime.now())
        continue
      if k > 1000:
        break
      producetokafka(line.strip(), "", "",producerid,maintopic,"",args)
      # change time to speed up or slow down data   
      #time.sleep(0.15)
    except Exception as e:
      print(e)  
      pass  

  file1.close()

def startproducing(**context):
    
  ti = context['task_instance']
  ti.xcom_push(key='PRODUCETYPE',value='LOCALFILE')
  ti.xcom_push(key='TOPIC',value=default_args['topics'])
  ti.xcom_push(key='PORT',value=default_args['inputfile'])
  ti.xcom_push(key='IDENTIFIER',value=default_args['identifier'])

  repo=tsslogging.getrepo() 
  sname = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="solutionname")
  if sname != '_mysolution_':
     fullpath="/{}/tml-airflow/dags/tml-solutions/{}/{}".format(repo,sname,os.path.basename(__file__))  
  else:
     fullpath="/{}/tml-airflow/dags/{}".format(repo,os.path.basename(__file__))  
    
  subprocess.run(["tmux", "new", "-d", "-s", "viper-produce-python"])
  subprocess.run(["tmux", "send-keys", "-t", "viper-produce-python", "C-c", "ENTER"])
  subprocess.run(["tmux", "send-keys", "-t", "viper-produce-python", "cd /Viper-produce", "ENTER"])
  subprocess.run(["tmux", "send-keys", "-t", "viper-produce-python", "python {} 1 {}".format(fullpath,context), "ENTER"])        
        
if __name__ == '__main__':
    
    if len(sys.argv) > 1:
       if sys.argv[1] == "1":  
         readdata(sys.argv[2])
