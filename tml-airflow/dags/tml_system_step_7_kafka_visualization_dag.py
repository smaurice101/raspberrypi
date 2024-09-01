from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from datetime import datetime
from airflow.decorators import dag, task
import sys
import subprocess
import tsslogging
import os
import time
import random

sys.dont_write_bytecode = True
######################################## USER CHOOSEN PARAMETERS ########################################
default_args = {
  'topic' : 'iot-preprocess',    # <<< *** Separate multiple topics by a comma - Viperviz will stream data from these topics to your browser
  'secure': '1',   # <<< *** 1=connection is encrypted, 0=no encryption
  'offset' : '-1',    # <<< *** -1 indicates to read from the last offset always
  'append' : '0',   # << ** Do not append new data in the browser
  'rollbackoffset' : '500', # *************** Rollback the data stream by rollbackoffset.  For example, if 500, then Viperviz wll grab all of the data from the last offset - 500
  'vipervizport' : '9005', # Enter port or leave blank to let TSS automatically pick free port  
}

######################################## DO NOT MODIFY BELOW #############################################

# Instantiate your DAG
@dag(dag_id="tml_system_step_7_kafka_visualization_dag", default_args=default_args, tags=["tml_system_step_7_kafka_visualization_dag"], schedule=None,catchup=False)
def startstreaming():    
  def empty():
      pass
dag = startstreaming()

def windowname(wtype,vipervizport):
    randomNumber = random.randrange(10, 9999)
    wn = "viperviz-{}-{}".format(wtype,randomNumber)
    with open('/tmux/vipervizwindows.txt', 'a', encoding='utf-8') as file: 
      file.writelines("{},{}\n".format(wn,vipervizport))
    
    return wn

def startstreamingengine(**context):
        repo=tsslogging.getrepo()  
        tsslogging.tsslogit("Visualization DAG in {}".format(os.path.basename(__file__)), "INFO" )                     
        tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")    
        chip = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="chip") 
       
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
        
        vipervizportp = default_args['vipervizport']
        if vipervizportp != '':
            vipervizport = int(vipervizportp)
        
        ti = context['task_instance']
        ti.xcom_push(key='VIPERVIZPORT',value="_{}".format(vipervizport))
        ti.xcom_push(key='topic',value=topic)
        ti.xcom_push(key='secure',value="_{}".format(secure))
        ti.xcom_push(key='offset',value="_{}".format(offset))
        ti.xcom_push(key='append',value="_{}".format(append))
        ti.xcom_push(key='chip',value=chip)
        ti.xcom_push(key='rollbackoffset',value="_{}".format(rollbackoffset))
    
        # start the viperviz on Vipervizport
        # STEP 5: START Visualization Viperviz 
        wn = windowname('visual',vipervizport)
        subprocess.run(["tmux", "new", "-d", "-s", "{}".format(wn)])
        subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "cd /Viperviz", "ENTER"])
        subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "/Viperviz/viperviz-linux-{} 0.0.0.0 {}".format(chip,vipervizport), "ENTER"])
