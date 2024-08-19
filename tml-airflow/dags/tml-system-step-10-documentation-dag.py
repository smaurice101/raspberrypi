from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime
from airflow.decorators import dag, task
import os 
import sys

sys.dont_write_bytecode = True

######################################################USER CHOSEN PARAMETERS ###########################################################
default_args = {    
 'start_date': datetime (2024, 6, 29),   # <<< *** Change as needed   
 'retries': 1,   # <<< *** Change as needed   
}

############################################################### DO NOT MODIFY BELOW ####################################################
# Instantiate your DAG
@dag(dag_id="tml_system_step_10_documentation_dag", default_args=default_args, tags=["tml-system-step-10-documentation-dag"], schedule=None,  catchup=False)
def startdocumentation():
    # Define tasks

  @task(task_id="getparams")
  def generatedoc():    
    
    sname = VIPERTOKEN = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="solutionname")
    sdesc = VIPERTOKEN = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="solutiondescription")

    vipervizport = ti.xcom_pull(dag_id='tml-system-step-7-kafka-visualization-dag',task_ids='startstreamingengine',key="VIPERVIZPORT")

    # Kick off shell script
     
      
    
dag = startdocumentation()
