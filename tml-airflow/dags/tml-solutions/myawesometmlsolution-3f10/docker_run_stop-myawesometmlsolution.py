from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime
from airflow.decorators import dag, task
import os 
import subprocess
import tsslogging
import git
import time
import sys

sys.dont_write_bytecode = True

######################################################USER CHOSEN PARAMETERS ###########################################################
default_args = {
 'solution_name' : '', # << Leave blank - these will be updated by TSS
 'solution_dag' : '', # << Leave blank - these will be updated by TSS     
 'instances': 1,  # << Number of instances of your container 
 'start_date': datetime (2024, 6, 29),   # <<< *** Change as needed   
 'retries': 1,   # <<< *** Change as needed   
}

############################################################### DO NOT MODIFY BELOW ####################################################
# Instantiate your DAG
@dag(dag_id="container_run_stop_process_dag_myawesometmlsolution", default_args=default_args, tags=["container_run_stop_process_dag_myawesometmlsolution"], schedule=None,  catchup=False)
def containerprocess():
    # Define tasks
   def empty():
     pass
dag = containerprocess()
    
def run(**context):
    if 'CHIP' in os.environ:
         chip = os.environ['CHIP']
    else:
         chip="amd64"

    sname = default_args['solution_name']
    snamedag = default_args['solution_dag']
            
    containername = os.environ['DOCKERUSERNAME']  + "/{}-{}".format(sname,chip)          
    
    repo = tsslogging.getrepo()
    tsslogging.tsslogit("Executing docker run in {}".format(os.path.basename(__file__)), "INFO" )                     
    tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")        
    dockerrun = ("docker run -d --net=host --env TSS=0 --env SOLUTIONNAME={} --env SOLUTIONDAG={} --env GITUSERNAME={} " \
                 "--env GITPASSWORD={}  --env GITREPOURL={}  --env READTHEDOCS={} {}" \
                 .format(sname,snamedag,os.environ['GITUSERNAME'],os.environ['GITPASSWORD'],os.environ['GITREPOURL'],os.environ['READTHEDOCS'],containername))  
        
    subprocess.call(dockerrun, shell=True)
    
    maxtime = 300 # 2 min
    s=""
    iter=0
    while True:
      s=subprocess.check_output("/tmux/dockerid.sh {}".format(containername), shell=True)

      s=s.rstrip()
      s=s.decode("utf-8")
      if s == '':
          continue
      elif s != '': 
        break
      elif iter > maxtime:
          break
      iter +=1 
      time.sleep(1)

    if s != '':
        os.environ[containername]=s
    else:
        os.environ[containername]=""

    return dockerrun

def stop(**context):
    if 'CHIP' in os.environ:
         chip = os.environ['CHIP']
    else:
         chip="amd64"

    sname = default_args['solution_name']
            
    containername = os.environ['DOCKERUSERNAME']  + "/{}-{}".format(sname,chip)          

    if os.environ[containername] == "":        
      repo = tsslogging.getrepo() 
      tsslogging.tsslogit("Your container {} is not running".format(containername), "WARN" )                     
      tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")        
    else:
      tsslogging.tsslogit("Stopping container {} in {}".format(containername,os.path.basename(__file__)), "INFO" )                     
      tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")        
      dockerstop = "docker container stop $(docker container ls -q --filter name={}*)".format(os.environ[containername])        
      subprocess.call(dockerstop, shell=True, stdout=output, stderr=output)
  
def startruns(**context):        
    cnum = int(default_args['instances'])
    sname = default_args['solution_name']      
    snamedag = default_args['solution_dag']      
        
    runsapp = []
    for i in range(0,cnum):
        dr=run(context)
        runsapp.append(dr)
    repo=tsslogging.getrepo()
    tsslogging.tsslogit("Running Solution (Name={}, DAG={}} to Docker in {}: {}".format(sname,snamedag,os.path.basename(__file__),e), "INFO" )             
    tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")
