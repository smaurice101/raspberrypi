from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from datetime import datetime

#Define default arguments
default_args = {
 'owner': 'Sebastian Maurice',
 'start_date': datetime (2024, 6, 29),
 'retries': 1,
}

# Instantiate your DAG
dag = DAG (dag_id="tml_system_step_1_getparams_dag", default_args=default_args, tags=["tml-system-step-1-getparams"], schedule=None)

# Define tasks
def getparams():
     global VIPERHOST, VIPERPORT, HTTPADDR
     with open(basedir + "/Viper-produce/admin.tok", "r") as f:
        VIPERTOKEN=f.read()

     if VIPERHOST=="":
        with open(basedir + '/Viper-produce/viper.txt', 'r') as f:
          output = f.read()
          VIPERHOST = HTTPADDR + output.split(",")[0]
          VIPERPORT = output.split(",")[1]
          
     return VIPERTOKEN

    
VIPERTOKEN = PythonOperator(
 task_id='tml_system_step_1_getparams',
 python_callable=getparams,
 dag=dag,
)

if VIPERHOST=="":
    print("ERROR: Cannot read viper.txt: VIPERHOST is empty or HPDEHOST is empty")
