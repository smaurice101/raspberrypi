from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime
from airflow.decorators import dag, task
import maadstml 
import sys
import tsslogging
import os

sys.dont_write_bytecode = True

######################################## USER CHOOSEN PARAMETERS ########################################
default_args = {
 'owner' : 'Sebastian Maurice', # <<< ********** You change as needed
 'companyname': 'Otics',  # <<< ********** You change as needed
  'myname' : 'Sebastian',  # <<< ********** You change as needed
  'myemail' : 'Sebastian.Maurice',  # <<< ********** You change as needed
  'mylocation' : 'Toronto',  # <<< ********** You change as needed
  'replication' : 1,  # <<< ********** You change as needed
  'numpartitions': 1,  # <<< ********** You change as needed
  'enabletls': 1,  # <<< ********** You change as needed
  'brokerhost' : '',  # <<< ********** Leave as is
  'brokerport' : -999,  # <<< ********** Leave as is
  'microserviceid' : '',  # <<< ********** You change as needed
  'raw_data_topic' : 'iot-raw-data', # Separate multiple topics with comma <<< ********** You change topic names as needed
  'preprocess_data_topic' : 'iot-preprocess-data,iot-preprocess2-data', # Separate multiple topics with comma <<< ********** You change topic names as needed
  'ml_data_topic' : 'ml-data', # Separate multiple topics with comma <<< ********** You change topic names as needed
  'prediction_data_topic' : 'prediction-data', # Separate multiple topics with comma <<< ********** You change topic names as needed
  'description' : 'Topics to store iot data',  
  'start_date': datetime (2024, 6, 29),
  'retries': 1,
    
}

######################################## DO NOT MODIFY BELOW #############################################

# Instantiate your DAG
@dag(dag_id="tml_system_step_2_kafka_createtopic_dag_mytmlsolution4", default_args=default_args, tags=["tml_system_step_2_kafka_createtopic_dag_mytmlsolution4"], schedule=None,catchup=False)
def startkafkasetup():
  @task(task_id="setupkafkatopics")
  def setupkafkatopic(args):
     # Set personal data
      companyname=args['companyname']
      myname=args['myname']
      myemail=args['myemail']
      mylocation=args['mylocation']

      # Replication factor for Kafka redundancy
      replication=args['replication']
      # Number of partitions for joined topic
      numpartitions=args['numpartitions']
      # Enable SSL/TLS communication with Kafka
      enabletls=args['enabletls']
      # If brokerhost is empty then this function will use the brokerhost address in your
      # VIPER.ENV in the field 'KAFKA_CONNECT_BOOTSTRAP_SERVERS'
      brokerhost=args['brokerhost']
      # If this is -999 then this function uses the port address for Kafka in VIPER.ENV in the
      # field 'KAFKA_CONNECT_BOOTSTRAP_SERVERS'
      brokerport=args['brokerport']
      # If you are using a reverse proxy to reach VIPER then you can put it here - otherwise if
      # empty then no reverse proxy is being used
      microserviceid=args['microserviceid']
        
      VIPERTOKEN = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="VIPERTOKEN")
      VIPERHOST = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="VIPERHOST")
      VIPERPORT = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="VIPERPORT")

      #############################################################################################################
      #                         CREATE TOPIC TO STORE TRAINED PARAMS FROM ALGORITHM  
      
      topickeys = ['raw_data_topic','preprocess_data_topic','ml_data_topic','prediction_data_topic'] 
    
      for k in topickeys:
        producetotopic=args[k]
        description=args['description']
    
        topicsarr = producetotopic.split(",")
      
        for topic in topicsarr:  
          result=maadstml.vipercreatetopic(VIPERTOKEN,VIPERHOST,VIPERPORT,topic,companyname,
                                     myname,myemail,mylocation,description,enabletls,
                                     brokerhost,brokerport,numpartitions,replication,
                                     microserviceid='')
          print("Result=",result)

               
dag = startkafkasetup()
