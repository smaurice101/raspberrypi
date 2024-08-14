from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import datetime
from airflow.decorators import dag, task
import os 
import sys

sys.dont_write_bytecode = True
######################################################USER CHOSEN PARAMETERS ###########################################################
default_args = {
 'owner': 'Sebastian Maurice',  # <<< ******** change as needed 
 'start_date': datetime.datetime (2024, 6, 29),
 'brokerhost' : '127.0.0.1',  # <<<<***************** THIS WILL ACCESS LOCAL KAFKA - YOU CAN CHANGE TO CLOUD KAFKA HOST
 'brokerport' : '9092',     # <<<<***************** LOCAL AND CLOUD KAFKA listen on PORT 9092
 'cloudusername' : '',  # <<<< --------FOR KAFKA CLOUD UPDATE WITH API KEY  - OTHERWISE LEAVE BLANK
 'cloudpassword' : '',  # <<<< --------FOR KAFKA CLOUD UPDATE WITH API SECRET - OTHERWISE LEAVE BLANK   
 'retries': 1,
}


############################################################### DO NOT MODIFY BELOW ####################################################
# Instantiate your DAG
@dag(dag_id="tml_system_step_1_getparams_dag", default_args=default_args, tags=["tml-system-step-1-getparams"], schedule=None, start_date=datetime.datetime(2022, 3, 4), catchup=False)
def tmlparams():
    # Define tasks
  basedir = "/"
  viperconfigfile=basedir + "/Viper-produce/viper.env"

  def updateviperenv():
  # update ALL
    filepaths = ['/Viper-produce/viper.env','/Viper-preprocess/viper.env','/Viper-preprocess2/viper.env','/Viper-ml/viper.env','/Viperviz/viper.env']
    for mainfile in filepaths:
        with open(mainfile, 'r', encoding='utf-8') as file: 
          data = file.readlines() 
        r=0 
        for d in data:
           if 'KAFKA_CONNECT_BOOTSTRAP_SERVERS' in d: 
             data[r] = "KAFKA_CONNECT_BOOTSTRAP_SERVERS={}:{}".format(default_args['brokerhost'],default_args['brokerport'])
           if 'CLOUD_USERNAME' in d: 
             data[r] = "CLOUD_USERNAME={}".format(default_args['cloudusername'])
           if 'CLOUD_PASSWORD' in d: 
             data[r] = "CLOUD_PASSWORD={}".format(default_args['cloudpassword'])
                
           r += 1
        with open(mainfile, 'w', encoding='utf-8') as file: 
          file.writelines(data)


  @task(task_id="getparams")
  def getparams(args):
     VIPERHOST=""
     VIPERPORT=""
     HTTPADDR2="http://"
     HPDEHOST=""
     HPDEPORT=""
    
     with open(basedir + "/Viper-produce/admin.tok", "r") as f:
        VIPERTOKEN=f.read()

     if VIPERHOST=="":
        with open(basedir + '/Viper-produce/viper.txt', 'r') as f:
          output = f.read()
          VIPERHOST = HTTPADDR + output.split(",")[0]
          VIPERPORT = output.split(",")[1]
        with open('/Hpde/hpde.txt', 'r') as f:
          output = f.read()
          HPDEHOST = HTTPADDR2 + output.split(",")[0]
          HPDEPORT = output.split(",")[1]

     ti.xcom_push(key='VIPERTOKEN',value=VIPERTOKEN)
     ti.xcom_push(key='VIPERHOST',value=VIPERHOST)
     ti.xcom_push(key='VIPERPORT',value=VIPERPORT)
     ti.xcom_push(key='HTTPADDR',value=HTTPADDR)
     ti.xcom_push(key='HPDEHOST',value=HPDEHOST)
     ti.xcom_push(key='HPDEPORT',value=HPDEPORT)
             
     updateviperenv()
    
     return [VIPERTOKEN,VIPERHOST,VIPERPORT,HTTPADDR]
     
  tmlsystemparams=getparams(default_args)
  if tmlsystemparams[1]=="":
      print("ERROR: No host specified")
    
dag = tmlparams()
