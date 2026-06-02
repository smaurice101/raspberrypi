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
import threading
import uuid

sys.dont_write_bytecode = True

############################################################### DO NOT MODIFY BELOW ####################################################    

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
       pname=context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_projectname".format(sd))
        
       repo=tsslogging.getrepo()    
       tsslogging.tsslogit("Docker DAG in {}".format(os.path.basename(__file__)), "INFO" )                     
       tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")            
       
       chip = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_chip".format(sname))         
       cname = os.environ['DOCKERUSERNAME']  + "/{}-{}".format(sname,chip)          
       dockercname="{}-{}".format(sname,chip)    
           
       print("Containername=",cname)
       tsslogging.locallogs("INFO", "STEP 8: Starting docker push for: {}".format(cname))
       if os.environ['TSS'] == "1":
         try: 
           f = open("/tmux/cname.txt", "w")
           f.write(cname)
           f.close()
         except Exception as e:
           pass
     
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
         subprocess.call(f"docker rmi -f {cname}", shell=True)
         subprocess.call(f"docker rmi -f {cname}-tmlworking", shell=True)
             
         cbuf="docker commit {} {}".format(cid,cname)
         v=subprocess.call("docker commit {} {}-tmlworking".format(cid,cname), shell=True)

         QUEUE_DIR = "/tmux/optimizer_queue"
         os.makedirs(QUEUE_DIR, exist_ok=True)
         #job_file = os.path.join(QUEUE_DIR, f"{cname}.job")
    
          # Write the arguments inside the file as metadata
         with open(f"{QUEUE_DIR}/{dockercname}.job", "w") as f:
              f.write(f"CNAME={cname}\n")
              f.write(f"SNAME={sname}\n")
              f.write(f"SD={sd}\n")
              f.write(f"REPO={repo}\n")
              f.write(f"OCNAME={cname}-tmlworking\n")               
          
         tsslogging.locallogs("INFO", "STEP 8: Docker Container process started - check Github logs for status - it could take few minutes. Here is the commit command: {} - message={}".format(cbuf,v))         
           
       elif len(cid) <= 1:
              tsslogging.locallogs("ERROR", "STEP 8: There seems to be an issue with docker commit. Here is the command: docker commit {} {}".format(cid,cname)) 
              tsslogging.tsslogit("Deploying to Docker in {}".format(os.path.basename(__file__)), "ERROR" )             
              tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")
           
       os.environ['tssbuild']="1"
    
       doparse("/{}/tml-airflow/dags/tml-solutions/{}/docker_run_stop-{}.py".format(repo,pname,pname), ["--solution-name--;{}".format(sname)])
       doparse("/{}/tml-airflow/dags/tml-solutions/{}/docker_run_stop-{}.py".format(repo,pname,pname), ["--solution-dag--;{}".format(sd)])
    
     except Exception as e:
        print("[ERROR] Step 8: ",e)
        tsslogging.locallogs("ERROR", "STEP 8: Deploying to Docker in {}: {}".format(os.path.basename(__file__),e))
        tsslogging.tsslogit("Deploying to Docker in {}: {}".format(os.path.basename(__file__),e), "ERROR" )             
        #tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")
