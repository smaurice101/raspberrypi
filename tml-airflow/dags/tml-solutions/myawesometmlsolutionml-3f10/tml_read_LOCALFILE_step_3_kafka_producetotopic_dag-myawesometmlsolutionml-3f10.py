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
import json 
import time
import random 

sys.dont_write_bytecode = True
######################################## USER CHOOSEN PARAMETERS ########################################
default_args = {
  'owner' : 'Sebastian Maurice', # <<< *** Change as needed   
  'enabletls': '1', # <<< *** 1=connection is encrypted, 0=no encryption
  'microserviceid' : '', # <<< *** leave blank
  'producerid' : 'iotsolution',   # <<< *** Change as needed   
  'topics' : 'iot-raw-data', # *************** This is one of the topic you created in SYSTEM STEP 2
  'identifier' : 'TML solution',   # <<< *** Change as needed   
  'inputfile' : '/rawdatademo/IoTData.txt',  # <<< ***** replace ?  to input file name to read. NOTE this data file should be JSON messages per line and stored in the HOST folder mapped to /rawdata folder 
  'delay' : '7000', # << ******* 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic
  'topicid' : '-999', # <<< ********* do not modify  
  'sleep' : 0.2, # << Control how fast data streams - if 0 - the data will stream as fast as possible - BUT this may cause connecion reset by peer 
}

######################################## DO NOT MODIFY BELOW #############################################


# This sets the lat/longs for the IoT devices so it can be map
VIPERTOKEN=""
VIPERHOST=""
VIPERPORT=""
  
  
def producetokafka(value, tmlid, identifier,producerid,maintopic,substream,args):
 inputbuf=value     
 topicid=int(args['topicid'])

 # Add a 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic 
 delay = int(args['delay'])
 enabletls = int(args['enabletls'])
 identifier = args['identifier']

 try:
    result=maadstml.viperproducetotopic(VIPERTOKEN,VIPERHOST,VIPERPORT,maintopic,producerid,enabletls,delay,'','', '',0,inputbuf,substream,
                                        topicid,identifier)
 except Exception as e:
    print("ERROR:",e)

def readdata():

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
    tsslogging.locallogs("ERROR", "Localfile producing DAG in {} - {}".format(os.path.basename(__file__),e))     
    
    tsslogging.tsslogit("Localfile producing DAG in {}".format(os.path.basename(__file__)), "INFO" )                     
    tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")        
    return

  tsslogging.locallogs("INFO", "STEP 3: reading local file..successfully")   

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
      producetokafka(line.strip(), "", "",producerid,maintopic,"",args)
      # change time to speed up or slow down data   
      time.sleep(args['sleep'])
    except Exception as e:
      print(e)  
      pass  

  file1.close()

def windowname(wtype,sname,dagname):
    randomNumber = random.randrange(10, 9999)
    wn = "python-{}-{}-{},{}".format(wtype,randomNumber,sname,dagname)
    with open("/tmux/pythonwindows_{}.txt".format(sname), 'a', encoding='utf-8') as file: 
      file.writelines("{}\n".format(wn))
    
    return wn

def startproducing(**context):

  tsslogging.locallogs("INFO", "STEP 3: producing data started")     
  
  sd = context['dag'].dag_id

  sname=context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_solutionname".format(sd))
  VIPERTOKEN = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERTOKEN".format(sname))
  VIPERHOST = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERHOSTPRODUCE".format(sname))
  VIPERPORT = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERPORTPRODUCE".format(sname))
  HTTPADDR = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_HTTPADDR".format(sname))

  VIPERHOSTFROM=tsslogging.getip(VIPERHOST)     
  ti = context['task_instance']
  ti.xcom_push(key="{}_PRODUCETYPE".format(sname),value='LOCALFILE')
  ti.xcom_push(key="{}_TOPIC".format(sname),value=default_args['topics'])
  ti.xcom_push(key="{}_CLIENTPORT".format(sname),value="")
  ti.xcom_push(key="{}_IDENTIFIER".format(sname),value="{},{}".format(default_args['identifier'],default_args['inputfile']))

  ti.xcom_push(key="{}_FROMHOST".format(sname),value=VIPERHOSTFROM)
  ti.xcom_push(key="{}_TOHOST".format(sname),value=VIPERHOST)

  ti.xcom_push(key="{}_TSSCLIENTPORT".format(sname),value="")
  ti.xcom_push(key="{}_TMLCLIENTPORT".format(sname),value="")
    
  ti.xcom_push(key="{}_PORT".format(sname),value=VIPERPORT)
  ti.xcom_push(key="{}_HTTPADDR".format(sname),value=HTTPADDR)
        
  chip = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_chip".format(sname))   

  repo=tsslogging.getrepo() 

  if sname != '_mysolution_':
     fullpath="/{}/tml-airflow/dags/tml-solutions/{}/{}".format(repo,sname,os.path.basename(__file__))  
  else:
     fullpath="/{}/tml-airflow/dags/{}".format(repo,os.path.basename(__file__))  
    
  wn = windowname('produce',sname,sd)  
  subprocess.run(["tmux", "new", "-d", "-s", "{}".format(wn)])
  subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "cd /Viper-produce", "ENTER"])
  subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "python {} 1 {} {}{} {} ".format(fullpath,VIPERTOKEN,HTTPADDR,VIPERHOST,VIPERPORT[1:]), "ENTER"])        
        
if __name__ == '__main__':
    
    if len(sys.argv) > 1:
       if sys.argv[1] == "1":  
         VIPERTOKEN = sys.argv[2]
         VIPERHOST = sys.argv[3] 
         VIPERPORT = sys.argv[4]          
         readdata()
