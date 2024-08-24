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
 'solution_airflow_port' : '', # << Leave blank if you waant TSS to choose a free port automatically  
 'solution_viperviz_port' : '', # << Leave blank if you waant TSS to choose a free port automatically    
 'instances': 1,  # << Number of instances of your container 
 'start_date': datetime (2024, 6, 29),   # <<< *** Change as needed   
 'retries': 1,   # <<< *** Change as needed   
}

############################################################### DO NOT MODIFY BELOW ####################################################
# Instantiate your DAG
@dag(dag_id="container_run_stop_process_dag", default_args=default_args, tags=["container_run_stop_process_dag"], schedule=None,  catchup=False)
def containerprocess():
    # Define tasks
  
  
  def getfreeport():
        airflowport=default_args['solution_airflow_port']
        vipervizport=default_args['solution_viperviz_port']
        
        if airflowport=='':
              airflowport=tsslogging.getfreeport()
                
        if vipervizport=='':
            vipervizport=tsslogging.getfreeport()
            if vipervizport == airflowport:
                vipervizport=tsslogging.getfreeport()
            
        return airflowport, vipervizport    
    
  def run():
    if 'CHIP' in os.environ:
         chip = os.environ['CHIP']
    else:
         chip=""

    if chip.lower() == "arm64":  
        containername = os.environ['DOCKERUSERNAME']  + "/{}-{}".format(sname,chip)          
    else:    
        containername = os.environ['DOCKERUSERNAME']  + "/{}".format(sname)
    
    airflowport,vipervizport=getfreeport()    
    
    sname = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="solutionname")    
    repo = tsslogging.getrepo()
    tsslogging.tsslogit("Executing docker run in {}".format(os.path.basename(__file__)), "INFO" )                     
    tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")        
    dockerrun = ("docker run -d --net=host --env VIPERVIZPORT={} --env GITUSERNAME={} " \
                 "--env GITPASSWORD={}  --env GITREPOURL={} --env AIRFLOWPORT={} {}" \
                 .format(vipervizport,os.environ['GITUSERNAME'],os.environ['GITPASSWORD'],os.environ['GITREPOURL'], \
                  airflowport,containername))        
    subprocess.call(dockerrun, shell=True, stdout=output, stderr=output)
    
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

  @task(task_id="stop")
  def stop():
    if 'CHIP' in os.environ:
         chip = os.environ['CHIP']
    else:
         chip=""
    if chip.lower() == "arm64":  
        containername = os.environ['DOCKERUSERNAME']  + "/{}-{}".format(sname,chip)          
    else:    
        containername = os.environ['DOCKERUSERNAME']  + "/{}".format(sname)

    sname = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="solutionname")  
    if os.environ[containername] == "":        
      repo = tsslogging.getrepo() 
      tsslogging.tsslogit("Your container {} is not running".format(containername), "WARN" )                     
      tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")        
    else:
      tsslogging.tsslogit("Stopping container {} in {}".format(containername,os.path.basename(__file__)), "INFO" )                     
      tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")        
      dockerstop = "docker container stop $(docker container ls -q --filter name={}*)".format(os.environ[containername])        
      subprocess.call(dockerstop, shell=True, stdout=output, stderr=output)
  
  @task(task_id="startruns")
  def startruns():        
    cnum = int(default_args['instances'])
    sname = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="solutionname")    
    
    runsapp = []
    for i in range(0,cnum):
        dr=run()
        runsapp.append(dr)
    
    key="DOCKERRUN-{}".format(sname)    
    os.environ[key]=",".join(runsapp)
    

dag = containerprocess()
