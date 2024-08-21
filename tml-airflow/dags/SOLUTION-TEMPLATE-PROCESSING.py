from __future__ import annotations

import pendulum

from airflow.decorators import task
from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator
from airflow.sensors.external_task import ExternalTaskSensor 

# TML Solution template for processing
# Use this DAG to start processing data with:
# 1. visualization
# 2. containerization
# 3. documentationa

#https://codemirror.net/5/doc/manual.html#commands

# STEP 1: Get the Parameters
with DAG(
    dag_id="solution_getparams_dag",
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    schedule=None,
    tags=["solution_getparams_dag"],
) as dag:
      sensor_A = ExternalTaskSensor(
      task_id="solution_task_getparams",
      external_dag_id="tml_system_step_1_getparams_dag",
      external_task_id="getparams",
  )

# STEP 2: Create the Kafka topics
with DAG(
    dag_id="solution_createtopic_dag",
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    schedule=None,
    tags=["solution_createtopic_dag"],
) as dag:
      sensor_B = ExternalTaskSensor(
      task_id="solution_task_createtopic",
      external_dag_id="tml_system_step_2_kafka_createtopic_dag",
      external_task_id="setupkafkatopics",
  )

# STEP 3: Produce data to topic        
with DAG(
    dag_id="solution_producetotopic_dag",
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    schedule=None,
    tags=["solution_producetotopic_dag"],
) as dag:
      sensor_C = ExternalTaskSensor(
      task_id="solution_task_producetotopic",
      external_dag_id="tml_localfile_step_3_kafka_producetotopic_dag",
      external_task_id="readdata",
  )

# STEP 4: Preprocess the data        
with DAG(
    dag_id="solution_preprocess_dag",
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    schedule=None,
    tags=["solution_preprocess_dag"],
) as dag:
      sensor_D = ExternalTaskSensor(
      task_id="solution_task_preprocess",
      external_dag_id="tml_system_step_4_kafka_preprocess_dag",
      external_task_id="processtransactiondata",
  )

        
# STEP 5: Visualization the data        
with DAG(
    dag_id="solution_visualization_dag",
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    schedule=None,
    tags=["solution_visualization_dag"],
) as dag:
      sensor_E = ExternalTaskSensor(
      task_id="solution_task_visualization",
      external_dag_id="tml_system_step_7_kafka_visualization_dag",
      external_task_id="startstreamingengine",
  )

# STEP 6: Containerize the solution        
with DAG(
    dag_id="solution_docker_dag",
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    schedule=None,
    tags=["solution_docker_dag"],
) as dag:
      sensor_F = ExternalTaskSensor(
      task_id="solution_task_containerize",
      external_dag_id="tml_system_step_8_deploy_solution_to_docker_dag",
      external_task_id="dockerit",
  )

# STEP 7: Document the solution
with DAG(
    dag_id="solution_document_dag",
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    schedule=None,
    tags=["solution_document_dag"],
) as dag:
      sensor_G = ExternalTaskSensor(
      task_id="solution_task_document",
      external_dag_id="tml_system_step_10_documentation_dag",
      external_task_id="generatedoc",
  )
