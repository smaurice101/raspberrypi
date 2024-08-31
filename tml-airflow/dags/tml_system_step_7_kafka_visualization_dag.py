from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from datetime import datetime
from airflow.decorators import dag, task
import sys
import subprocess
import tsslogging
import os

sys.dont_write_bytecode = True
######################################## USER CHOOSEN PARAMETERS ########################################
default_args = {
  'topic' : 'iot-preprocess',    # <<< *** Separate multiple topics by a comma - Viperviz will stream data from these topics to your browser
  'secure': '1',   # <<< *** 1=connection is encrypted, 0=no encryption
  'offset' : '-1',    # <<< *** -1 indicates to read from the last offset always
  'append' : '0',   # << ** Do not append new data in the browser
  'rollbackoffset' : '500', # *************** Rollback the data stream by rollbackoffset.  For example, if 500, then Viperviz wll grab all of the data from the last offset - 500
  'start_date': datetime (2023, 1, 1),   # <<< *** Change as needed   
  'retries': 1,   # <<< *** Change as needed   
    
}

######################################## DO NOT MODIFY BELOW #############################################

# Instantiate your DAG
@dag(dag_id="tml_system_step_7_kafka_visualization_dag", default_args=default_args, tags=["tml_system_step_7_kafka_visualization_dag"], start_date=datetime(2023, 1, 1), schedule=None,catchup=False)
def startstreaming():    
  def empty():
      pass
dag = startstreaming()

def startstreamingengine(**context):
        repo=tsslogging.getrepo()  
        tsslogging.tsslogit("Visualization DAG in {}".format(os.path.basename(__file__)), "INFO" )                     
        tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")            
        chip = "amd64"         
        if 'CHIP' in os.environ:
            chip = os.environ['CHIP']
            chip = chip.lower()
       
        topic = default_args['topic']
        secure = default_args['secure']
        offset = default_args['offset']
        append = default_args['append']
        rollbackoffset = default_args['rollbackoffset']
        
        if 'VIPERVIZPORT' in os.environ:
            if os.environ['VIPERVIZPORT'] != '':
              vipervizport = os.environ['VIPERVIZPORT']
            else:
              vipervizport=tsslogging.getfreeport()
        else:
            vipervizport=tsslogging.getfreeport()
          
        ti = context['task_instance']
        ti.xcom_push(key='VIPERVIZPORT',value=vipervizport)
        ti.xcom_push(key='topic',value=topic)
        ti.xcom_push(key='secure',value=secure)
        ti.xcom_push(key='offset',value=offset)
        ti.xcom_push(key='append',value=append)
        ti.xcom_push(key='chip',value=chip)
        ti.xcom_push(key='rollbackoffset',value=rollbackoffset)
    
        # start the viperviz on Vipervizport
        # STEP 5: START Visualization Viperviz 
        subprocess.run(["tmux", "new", "-d", "-s", "visualization-viperviz"])
        subprocess.run(["tmux", "send-keys", "-t", "visualization-viperviz", "C-c", "ENTER"])
        subprocess.run(["tmux", "send-keys", "-t", "visualization-viperviz", "'cd /Viperviz'", "ENTER"])
        subprocess.run(["tmux", "send-keys", "-t", "visualization-viperviz", "'/Viperviz/viperviz-linux-{} 0.0.0.0 {}'".format(chip,vipervizport), "ENTER"])
