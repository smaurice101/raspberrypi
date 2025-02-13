from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime
from airflow.decorators import dag, task
import maadstml 
import sys
import tsslogging
import os
import subprocess

sys.dont_write_bytecode = True

######################################## USER CHOOSEN PARAMETERS ########################################
default_args = {
 'owner' : 'Sebastian Maurice', # <<< ********** You change as needed
 'companyname': 'Otics',  # <<< ********** You change as needed
  'myname' : 'Sebastian',  # <<< ********** You change as needed
  'myemail' : 'Sebastian.Maurice',  # <<< ********** You change as needed
  'mylocation' : 'Toronto',  # <<< ********** You change as needed
  'replication' : '1',  # <<< ********** You change as needed
  'numpartitions': '1',  # <<< ********** You change as needed
  'enabletls': '1',  # <<< ********** You change as needed
  'brokerhost' : '',  # <<< ********** Leave as is
  'brokerport' : '-999',  # <<< ********** Leave as is
  'microserviceid' : '',  # <<< ********** You change as needed
  'raw_data_topic' : 'iot-raw-data', # Separate multiple topics with comma <<< ********** You change topic names as needed
  'preprocess_data_topic' : 'iot-preprocess,iot-preprocess2', # Separate multiple topics with comma <<< ********** You change topic names as needed
  'ml_data_topic' : 'ml-data', # Separate multiple topics with comma <<< ********** You change topic names as needed
  'prediction_data_topic' : 'prediction-data', # Separate multiple topics with comma <<< ********** You change topic names as needed
  'pgpt_data_topic' : 'cisco-network-privategpt',  #  PrivateGPT will produce responses to this topic - change as  needed
  'description' : 'Topics to store iot data',      
}

######################################## DO NOT MODIFY BELOW #############################################


def deletetopics(topic):

    if 'KUBE' in os.environ:
       if os.environ['KUBE'] == "1":
         return
    buf = "/Kafka/kafka_2.13-3.0.0/bin/kafka-topics.sh --bootstrap-server localhost:9092 --topic {} --delete".format(topic)
    
    proc=subprocess.run(buf, shell=True)
    #proc.terminate()
    #proc.wait()
                
    repo=tsslogging.getrepo()    
    tsslogging.tsslogit("Deleting topic {} in {}".format(topic,os.path.basename(__file__)), "INFO" )                     
    tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")  
    
def setupkafkatopics(**context):
 # Set personal data

  tsslogging.locallogs("INFO", "STEP 2: Create topics started") 
    
  args = default_args
  companyname=args['companyname']
  myname=args['myname']
  myemail=args['myemail']
  mylocation=args['mylocation']
  description=args['description']  

  # Replication factor for Kafka redundancy
  replication=int(args['replication'])
  # Number of partitions for joined topic
  numpartitions=int(args['numpartitions'])
  # Enable SSL/TLS communication with Kafka
  enabletls=int(args['enabletls'])
  # If brokerhost is empty then this function will use the brokerhost address in your
  brokerhost=args['brokerhost']
  # If this is -999 then this function uses the port address for Kafka in VIPER.ENV in the
  # field 'KAFKA_CONNECT_BOOTSTRAP_SERVERS'
  brokerport=int(args['brokerport'])
  # If you are using a reverse proxy to reach VIPER then you can put it here - otherwise if
  # empty then no reverse proxy is being used
  microserviceid=args['microserviceid']

  raw_data_topic=args['raw_data_topic']
  preprocess_data_topic=args['preprocess_data_topic']
  ml_data_topic=args['ml_data_topic']
  prediction_data_topic=args['prediction_data_topic']
  
  sd = context['dag'].dag_id
  sname=context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_solutionname".format(sd))

  VIPERTOKEN = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERTOKEN".format(sname))
  VIPERHOST = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERHOSTPRODUCE".format(sname))
  VIPERPORT = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERPORTPRODUCE".format(sname))
  mainbroker = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_brokerhost".format(sname))
  HTTPADDR = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_HTTPADDR".format(sname))

  ti = context['task_instance'] 
  ti.xcom_push(key="{}_companyname".format(sname), value=companyname)
  ti.xcom_push(key="{}_myname".format(sname), value=myname)
  ti.xcom_push(key="{}_myemail".format(sname), value=myemail)
  ti.xcom_push(key="{}_mylocation".format(sname), value=mylocation)
  ti.xcom_push(key="{}_replication".format(sname), value="_{}".format(replication))
  ti.xcom_push(key="{}_numpartitions".format(sname), value="_{}".format(numpartitions))
  ti.xcom_push(key="{}_enabletls".format(sname), value="_{}".format(enabletls))
  ti.xcom_push(key="{}_microserviceid".format(sname), value=microserviceid)
  ti.xcom_push(key="{}_raw_data_topic".format(sname), value=raw_data_topic)
  ti.xcom_push(key="{}_preprocess_data_topic".format(sname), value=preprocess_data_topic)
  ti.xcom_push(key="{}_ml_data_topic".format(sname), value=ml_data_topic)
  ti.xcom_push(key="{}_prediction_data_topic".format(sname), value=prediction_data_topic)
  


  #############################################################################################################
  #                         CREATE TOPIC TO STORE TRAINED PARAMS FROM ALGORITHM  

  topickeys = ['raw_data_topic','preprocess_data_topic','ml_data_topic','prediction_data_topic','pgpt_data_topic'] 
  VIPERHOSTMAIN = "{}{}".format(HTTPADDR,VIPERHOST)    

  for k in topickeys:
    producetotopic=args[k]
    description=args['description']

    topicsarr = producetotopic.split(",")
    for topic in topicsarr:  
        if topic != '' and "127.0.0.1" in mainbroker:
          try:  
            deletetopics(topic)
          except Exception as e:
            print("ERROR: ",e)
            continue 

    if '127.0.0.1' in mainbroker:
        replication=1
            
    for topic in topicsarr:  
      if topic == '':
          continue
      print("Creating topic=",topic)  
      try:
        result=maadstml.vipercreatetopic(VIPERTOKEN,VIPERHOSTMAIN,VIPERPORT[1:],topic,companyname,
                                 myname,myemail,mylocation,description,enabletls,
                                 brokerhost,brokerport,numpartitions,replication,
                                 microserviceid='')
      except Exception as e:
       tsslogging.locallogs("ERROR", "STEP 2: Cannot create topic {} in {} - {}".format(topic,os.path.basename(__file__),e)) 
    
       repo=tsslogging.getrepo()    
       tsslogging.tsslogit("Cannot create topic {} in {} - {}".format(topic,os.path.basename(__file__),e), "ERROR" )                     
       tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")  
        
  tsslogging.locallogs("INFO", "STEP 2: Completed")
