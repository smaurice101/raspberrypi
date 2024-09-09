from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime
from airflow.decorators import dag, task
import os 
import tsslogging
import sys

sys.dont_write_bytecode = True

######################################################USER CHOSEN PARAMETERS ###########################################################
default_args = {
 'owner': 'Sebastian Maurice',   # <<< *** Change as needed   
}

############################################################### DO NOT MODIFY BELOW ####################################################
# Instantiate your DAG
@dag(dag_id="tml_system_step_9_privategpt_qdrant_dag_myawesometmlsolution2-3f10", default_args=default_args, tags=["tml_system_step_9_privategpt_qdrant_dag_myawesometmlsolution2-3f10"], schedule=None,  catchup=False)
def startaiprocess():
    # Define tasks
    def empty():
        pass
dag = startaiprocess()    

    
def startprivategpt(**context):
     VIPERHOST=""
     VIPERPORT=""
     HTTPADDR=""

     ############ TO BE COMPLETED
