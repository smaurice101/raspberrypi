from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from datetime import datetime
from airflow.decorators import dag, task

#Define default arguments
default_args = {
 'companyname': 'Otics',
  'myname' : 'Sebastian',
  'myemail' : 'Sebastian.Maurice',
  'mylocation' : 'Toronto',
  'replication' : 1,
  'numpartitions': 1,
  'enabletls': 1,
  'brokerhost' : '',
  'brokerport' : -999,
  'microserviceid' : '',
  'topics' : 'iot-raw-data,iot-preprocess-data,iot-preprocess2-data', # Separate multiple topics with comma
  'description' : 'Topics to store iot data',  
  'start_date': datetime (2024, 6, 29),
  'retries': 1,
    
}

# Instantiate your DAG
@dag(dag_id="tml_system_step_2_kafka_createtopic_dag", default_args=default_args, tags=["tml-system-step-2-kafka-createtopic"], schedule=None,catchup=False)
def startkafkasetup():
  @task(task_id="setupkafkatopics")
  def setupkafkatopic(args):
     # Set personal data
      companyname=args['companyname']
      myname=args['myname']
      myemail=args['myemail']
      mylocation=args['mylocation']

      # Replication factor for Kafka redundancy
      replication=args['replication']
      # Number of partitions for joined topic
      numpartitions=args['numpartitions']
      # Enable SSL/TLS communication with Kafka
      enabletls=args['enabletls']
      # If brokerhost is empty then this function will use the brokerhost address in your
      # VIPER.ENV in the field 'KAFKA_CONNECT_BOOTSTRAP_SERVERS'
      brokerhost=args['brokerhost']
      # If this is -999 then this function uses the port address for Kafka in VIPER.ENV in the
      # field 'KAFKA_CONNECT_BOOTSTRAP_SERVERS'
      brokerport=args['brokerport']
      # If you are using a reverse proxy to reach VIPER then you can put it here - otherwise if
      # empty then no reverse proxy is being used
      microserviceid=args['microserviceid']
        
      VIPERTOKEN = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="VIPERTOKEN")
      VIPERHOST = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="VIPERHOST")
      VIPERPORT = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="VIPERPORT")

      #############################################################################################################
      #                         CREATE TOPIC TO STORE TRAINED PARAMS FROM ALGORITHM  
      
      producetotopic=args['topics']
      description=args['description']
    
      topicsarr = producetotopic.split(",")
      
      for topic in topicsarr:  
        result=maadstml.vipercreatetopic(VIPERTOKEN,VIPERHOST,VIPERPORT,producetotopic,companyname,
                                     myname,myemail,mylocation,description,enabletls,
                                     brokerhost,brokerport,numpartitions,replication,
                                     microserviceid='')
        # Load the JSON array in variable y
        print("Result=",result)

      setupkafkatopic(default_args)
      
      
dag = startkafkasetup()
