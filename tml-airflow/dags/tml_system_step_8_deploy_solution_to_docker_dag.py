from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime
from airflow.decorators import dag, task
import os 
import subprocess
import tsslogging
import git

import sys

sys.dont_write_bytecode = True

######################################################USER CHOSEN PARAMETERS ###########################################################
default_args = {
 'solution_dag_to_trigger' : 'solution_preprocessing_dag',   # << Enter the name of the Solution DAG to trigger when container runs
}

############################################################### DO NOT MODIFY BELOW ####################################################
# Instantiate your DAG
@dag(dag_id="tml_system_step_8_deploy_solution_to_docker_dag", default_args=default_args, tags=["tml_system_step_8_deploy_solution_to_docker_dag"], schedule=None,  catchup=False)
def starttmldeploymentprocess():
    # Define tasks
    def empty():
        pass
dag = starttmldeploymentprocess()
    
def dockerit(**context):
     if 'tssbuild' in os.environ:
        if os.environ['tssbuild']=="1":
            return        
     try:
       repo=tsslogging.getrepo()    
       tsslogging.tsslogit("Docker DAG in {}".format(os.path.basename(__file__)), "INFO" )                     
       tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")            
       sname = context['ti'].xcom_pull(task_ids='solution_task_getparams',key="solutionname")
       if 'CHIP' in os.environ:
          chip = os.environ['CHIP']
       else:
          chip=""
       if chip.lower() == "arm64":  
          cname = os.environ['DOCKERUSERNAME']  + "/{}-{}".format(sname,chip)          
       else:    
          cname = os.environ['DOCKERUSERNAME']  + "/{}".format(sname)
      
       print("Containername=",cname)
        
       ti = context['task_instance']
       ti.xcom_push(key="containername",value=cname)
       ti.xcom_push(key='solution_dag_to_trigger', value=solution_dag_to_trigger)
        
       scid = tsslogging.getrepo('/tmux/cidname.txt')
       cid = os.environ['SCID']
       tsslogging.tmuxchange(default_args['solution_dag_to_trigger'])
       key = "trigger-{}".format(sname)
       os.environ[key] = default_args['solution_dag_to_trigger']
       subprocess.call("docker commit {} {}".format(cid,cname), shell=True, stdout=output, stderr=output)
       subprocess.call("docker push {}".format(cname), shell=True, stdout=output, stderr=output)  
       os.environ['tssbuild']="1"
     except Exception as e:
        tsslogging.tsslogit("Deploying to Docker in {}: {}".format(os.path.basename(__file__),e), "ERROR" )             
        tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")
