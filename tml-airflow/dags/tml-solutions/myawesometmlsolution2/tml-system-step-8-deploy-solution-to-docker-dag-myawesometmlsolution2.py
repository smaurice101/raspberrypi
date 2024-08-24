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
 'owner': 'Sebastian Maurice',   # <<< *** Change as needed   
 'containername' : '', # << Specify the name of the container (NO SPACES IN NAME)- if BLANK the solutionname will be used
 'solution_airflowport' : '',   
 'start_date': datetime (2024, 6, 29),   # <<< *** Change as needed   
 'retries': 1,   # <<< *** Change as needed   
}

############################################################### DO NOT MODIFY BELOW ####################################################
# Instantiate your DAG
@dag(dag_id="tml_system_step_8_deploy_solution_to_docker_dag_myawesometmlsolution2", default_args=default_args, tags=["tml_system_step_8_deploy_solution_to_docker_dag_myawesometmlsolution2"], schedule=None,  catchup=False)
def starttmldeploymentprocess():
    # Define tasks

    
  @task(task_id="dockerit")
  def dockerit():
     if 'tssbuild' in os.environ:
        if os.environ['tssbuild']==1:
            return        
     try:
       repo=tsslogging.getrepo()    
       tsslogging.tsslogit("Docker DAG in {}".format(os.path.basename(__file__)), "INFO" )                     
       tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")            
       sname = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="solutionname")
       if 'CHIP' in os.environ:
          chip = os.environ['CHIP']
       else:
          chip=""
       if chip.lower() == "arm64":  
          cname = os.environ['DOCKERUSERNAME']  + "/{}-{}".format(sname,chip)          
       else:    
          cname = os.environ['DOCKERUSERNAME']  + "/{}".format(sname)
    
       scid = tsslogging.getrepo('/tmux/cidname.txt')
       ti.xcom_push(key='containername',value=cname)
       cid = os.environ['SCID']
       subprocess.call("docker commit {} {}".format(cid,cname), shell=True, stdout=output, stderr=output)
       subprocess.call("docker push {}".format(cname), shell=True, stdout=output, stderr=output)  
       os.environ['tssbuild']=1
     except Exception as e:
        tsslogging.tsslogit("Deploying to Docker in {}: {}".format(os.path.basename(__file__),e), "ERROR" )             
        tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")
        

dag = starttmldeploymentprocess()
