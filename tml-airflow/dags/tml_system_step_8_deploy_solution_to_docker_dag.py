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

############################################################### DO NOT MODIFY BELOW ####################################################
# Instantiate your DAG
@dag(dag_id="tml_system_step_8_deploy_solution_to_docker_dag", tags=["tml_system_step_8_deploy_solution_to_docker_dag"], schedule=None,  catchup=False)
def starttmldeploymentprocess():
    # Define tasks
    def empty():
        pass
dag = starttmldeploymentprocess()
    

def doparse(fname,farr):
      data = ''
      with open(fname, 'r', encoding='utf-8') as file: 
        data = file.readlines() 
        r=0
        for d in data:        
            for f in farr:
                fs = f.split(";")
                if fs[0] in d:
                    data[r] = d.replace(fs[0],fs[1])
            r += 1  
      with open(fname, 'w', encoding='utf-8') as file: 
        file.writelines(data)
        
def dockerit(**context):
     if 'tssbuild' in os.environ:
        if os.environ['tssbuild']=="1":
            return        
     try:
     
       sd = context['dag'].dag_id
       sname=context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_solutionname".format(sd))
        
       repo=tsslogging.getrepo()    
       tsslogging.tsslogit("Docker DAG in {}".format(os.path.basename(__file__)), "INFO" )                     
       tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")            
       
       chip = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_chip".format(sname))         
       cname = os.environ['DOCKERUSERNAME']  + "/{}-{}".format(sname,chip)          
      
       print("Containername=",cname)
       tsslogging.locallogs("INFO", "STEP 8: Starting docker push for: {}".format(cname))
            
       ti = context['task_instance']
       ti.xcom_push(key="{}_containername".format(sname),value=cname)
       ti.xcom_push(key="{}_solution_dag_to_trigger".format(sname), value=sd)
        
       scid = tsslogging.getrepo('/tmux/cidname.txt')
       cid = scid # cid added
  
       key = "trigger-{}".format(sname)
       os.environ[key] = sd
       if os.environ['TSS'] == "1" and len(cid) > 1: 
         print("[INFO] docker commit {} {}".format(cid,cname))  
         subprocess.call("docker rmi -f $(docker images --filter 'dangling=true' -q --no-trunc)", shell=True)
         cbuf="docker commit {} {}".format(cid,cname)
         v=subprocess.call("docker commit {} {}".format(cid,cname), shell=True)
         time.sleep(20)    
         if v != 0:   
           tsslogging.locallogs("WARN", "STEP 8: There seems to be an issue creating the container.  Here is the commit command: {} - message={}.  Container may NOT pushed.".format(cbuf,v)) 
         else:
           tsslogging.locallogs("INFO", "STEP 8: Docker Container created.  Will push it now.  Here is the commit command: {} - message={}".format(cbuf,v))         
           
         v=subprocess.call("docker push {}".format(cname), shell=True)  
         time.sleep(20)               
         if v != 0:   
              tsslogging.locallogs("WARN", "STEP 8: There may be an issue pushing to Docker Hub, or just wait few seconds to see if the container shows up.  Here is the command: docker push {} - message={}".format(cname,v)) 
         else:                   
              tsslogging.locallogs("INFO", "STEP 8: Successfully ran Docker push: docker push {} - message={}".format(cname,v)) 
       elif len(cid) <= 1:
              tsslogging.locallogs("ERROR", "STEP 8: There seems to be an issue with docker commit. Here is the command: docker commit {} {}".format(cid,cname)) 
              tsslogging.tsslogit("Deploying to Docker in {}".format(os.path.basename(__file__)), "ERROR" )             
              tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")
           
       os.environ['tssbuild']="1"
    
       doparse("/{}/tml-airflow/dags/tml-solutions/{}/docker_run_stop-{}.py".format(repo,sname,sname), ["--solution-name--;{}".format(sname)])
       doparse("/{}/tml-airflow/dags/tml-solutions/{}/docker_run_stop-{}.py".format(repo,sname,sname), ["--solution-dag--;{}".format(sd)])
    
     except Exception as e:
        print("[ERROR] Step 8: ",e)
        tsslogging.locallogs("ERROR", "STEP 8: Deploying to Docker in {}: {}".format(os.path.basename(__file__),e))
        tsslogging.tsslogit("Deploying to Docker in {}: {}".format(os.path.basename(__file__),e), "ERROR" )             
        tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")
