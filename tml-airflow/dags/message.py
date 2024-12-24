from airflow import DAG
from airflow.decorators import dag, task

# Instantiate your DAG
@dag(dag_id="ALOHA_PLEASE_BE_PATIENT_FOR_DAGS_TO_POPULATE",default_args={}, tags=[""],schedule=None,catchup=False)
def message():
   def empty():
     pass
dag = message()
