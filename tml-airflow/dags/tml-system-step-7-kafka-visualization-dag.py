from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from datetime import datetime
from airflow.decorators import dag, task
import sys

sys.dont_write_bytecode = True
######################################## USER CHOOSEN PARAMETERS ########################################
default_args = {
  'owner' : 'Sebastian Maurice',    # <<< *** Change as needed   
  'enabletls': 1,   # <<< *** 1=connection is encrypted, 0=no encryption
  'microserviceid' : '',   # <<< *** leave blank
  'producerid' : 'iotsolution',    # <<< *** Change as needed   
  'topics' : 'iot-raw-data', # *************** This is one of the topic you created in SYSTEM STEP 2
  'identifier' : 'TML solution',    # <<< *** Change as needed   
  'inputfile' : '/rawdata/?',  # <<< ***** replace ?  to input file to read. NOTE this data file should JSON messages per line and stored in the HOST folder mapped to /rawdata folder 
  'start_date': datetime (2024, 6, 29),   # <<< *** Change as needed   
  'retries': 1,   # <<< *** Change as needed   
    
}

######################################## DO NOT MODIFY BELOW #############################################

# Instantiate your DAG
@dag(dag_id="tml-system-step-7-kafka-visualization-dag", default_args=default_args, tags=["tml-system-step-7-kafka-visualization-dag"], schedule=None,catchup=False)
def startproducingtotopic():
  # This sets the lat/longs for the IoT devices so it can be map
  VIPERTOKEN=""
  VIPERHOST=""
  VIPERPORT=""
    
    

dag = startproducingtotopic()
