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
@dag(dag_id="container_run_stop_process_dag_myawesometmlsolution3", default_args=default_args, tags=["container_run_stop_process_dag_myawesometmlsolution3"], schedule=None,  catchup=False)
def containerprocess():
    # Define tasks
   def empty():
     pass
dag = containerprocess()

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
    
def run(**context):
    if 'CHIP' in os.environ:
         chip = os.environ['CHIP']
    else:
         chip=""

    if chip.lower() == "arm64":  
        containername = os.environ['DOCKERUSERNAME']  + "/{}-{}".format(sname,chip)          
    else:    
        containername = os.environ['DOCKERUSERNAME']  + "/{}".format(sname)
    
    airflowport,vipervizport=getfreeport()    
    
    sname = context['ti'].xcom_pull(task_ids='solution_task_getparams',key="solutionname")    
    topic = context['ti'].xcom_pull(task_ids='solution_task_visualization',key="topic")
    secure = context['ti'].xcom_pull(task_ids='solution_task_visualization',key="secure")
    offset = context['ti'].xcom_pull(task_ids='solution_task_visualization',key="offset")
    append = context['ti'].xcom_pull(task_ids='solution_task_visualization',key="append")
    chip = context['ti'].xcom_pull(task_ids='solution_task_visualization',key="chip")
    rollbackoffset = context['ti'].xcom_pull(task_ids='solution_task_visualization',key="rollbackoffset")

    repo = tsslogging.getrepo()
    tsslogging.tsslogit("Executing docker run in {}".format(os.path.basename(__file__)), "INFO" )                     
    tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")        
    dockerrun = ("docker run -d --net=host --env TSS=0 --env SOLUTIONNAME=TSS --env GITUSERNAME={} " \
                 "--env GITPASSWORD=<Enter Github Password>  --env GITREPOURL={}  " \
                 "--env READTHEDOCS=<Enter Readthedocs token> {}" \
                 .format(os.environ['GITUSERNAME'],os.environ['GITREPOURL'],containername))  
        
    subprocess.call(dockerrun, shell=True, stdout=output, stderr=output)
    vizurl = "http://localhost:{}/dashboard.html?topic={}&offset={}&groupid=&rollbackoffset={}&topictype=prediction&append={}&secure={}".format(vipervizport,topic,offset,rollbackoffset,append,secure)
    airflowurl = "http://localhost:{}".format(airflowport)
    
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

    return dockerrun,vizurl,airflowurl

def stop(**context):
    if 'CHIP' in os.environ:
         chip = os.environ['CHIP']
    else:
         chip=""
    if chip.lower() == "arm64":  
        containername = os.environ['DOCKERUSERNAME']  + "/{}-{}".format(sname,chip)          
    else:    
        containername = os.environ['DOCKERUSERNAME']  + "/{}".format(sname)

    sname = context['ti'].xcom_pull(task_ids='solution_task_getparams',key="solutionname")  
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
    sname = context['ti'].xcom_pull(task_ids='solution_task_getparams',key="solutionname")        
        
    runsapp = []
    visualapp = []
    airflowapp = []
    for i in range(0,cnum):
        dr,viz,air=run(context)
        runsapp.append(dr)
        visualapp.append(viz)
        airflowapp.append(air)
    
    key="DOCKERRUN-{}".format(sname)    
    os.environ[key]=",".join(runsapp)
    key="VISUALRUN-{}".format(sname)    
    os.environ[key]=",".join(visualapp)
    key="AIRFLOWRUN-{}".format(sname)    
    os.environ[key]=",".join(airflowapp)
    
    cname = context['ti'].xcom_pull(task_ids='solution_task_containerize',key="containername")
    key="DOCKERRUN-{}".format(sname)    
    dockerrun=os.environ[key]
    dockerrun=dockerrun.replace(",","\n\n")
    subprocess.call(["sed", "-i", "-e",  "s/--dockercontainer--/{}/g".format(cname), "/{}/docs/source/operating.rst".format(sname)])

    subprocess.call(["sed", "-i", "-e",  "s/--dockerrun--/{}/g".format(dockerrun), "/{}/docs/source/operating.rst".format(sname)])
    
    key="VISUALRUN-{}".format(sname)    
    visualrun=os.environ[key]
    visualrun=visualrun.replace(",","\n\n")
    subprocess.call(["sed", "-i", "-e",  "s/--visualizationurl--/{}/g".format(visualrun), "/{}/docs/source/operating.rst".format(sname)])

    key="AIRFLOWRUN-{}".format(sname)    
    airflowrun=os.environ[key]
    airflowrun=visualrun.replace(",","\n\n")
    subprocess.call(["sed", "-i", "-e",  "s/--airflowurl--/{}/g".format(visualrun), "/{}/docs/source/operating.rst".format(sname)])

    tsslogging.git_push("/{}".format(sname),"{}-readthedocs".format(sname),sname)
