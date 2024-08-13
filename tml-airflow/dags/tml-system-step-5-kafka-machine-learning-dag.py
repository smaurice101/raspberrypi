from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from datetime import datetime
from airflow.decorators import dag, task
import sys

sys.dont_write_bytecode = True
######################################## USER CHOOSEN PARAMETERS ########################################
default_args = {
  'owner' : 'Sebastian Maurice',   # <<< *** Change as needed      
  'enabletls': 1,   # <<< *** 1=connection is encrypted, 0=no encryption
  'microserviceid' : '', # <<< *** leave blank
  'producerid' : 'iotsolution',    # <<< *** Change as needed   
  'topics' : 'iot-raw-data', # *************** This is one of the topic you created in SYSTEM STEP 2
  'identifier' : 'TML solution',    # <<< *** Change as needed   
  'inputfile' : '/rawdata/?',  # <<< ***** replace ?  to input file to read. NOTE this data file should JSON messages per line and stored in the HOST folder mapped to /rawdata folder 
  'start_date': datetime (2024, 6, 29),   # <<< *** Change as needed   
  'retries': 1,   # <<< *** Change as needed   
    
}

######################################## DO NOT MODIFY BELOW #############################################

# Instantiate your DAG
@dag(dag_id="tml-system-step-5-kafka-machine-learning-dag", default_args=default_args, tags=["tml-system-step-5-kafka-machine-learning-dag"], schedule=None,catchup=False)
def startmachinelearning():
  # This sets the lat/longs for the IoT devices so it can be map
  VIPERTOKEN=""
  VIPERHOST=""
  VIPERPORT=""

  @task(task_id="performSupervisedMachineLearning")  
  def performSupervisedMachineLearning(maintopic,topicid):

      # Set personal data
      companyname="OTICS Advanced Analytics"
      myname="Sebastian"
      myemail="Sebastian.Maurice"
      mylocation="Toronto"

      # Replication factor for Kafka redundancy
      replication=1
      # Number of partitions for joined topic
      numpartitions=3
      # Enable SSL/TLS communication with Kafka
      enabletls=1
      # If brokerhost is empty then this function will use the brokerhost address in your
      # VIPER.ENV in the field 'KAFKA_CONNECT_BOOTSTRAP_SERVERS'
      brokerhost=''
      # If this is -999 then this function uses the port address for Kafka in VIPER.ENV in the
      # field 'KAFKA_CONNECT_BOOTSTRAP_SERVERS'
      brokerport=-999
      # If you are using a reverse proxy to reach VIPER then you can put it here - otherwise if
      # empty then no reverse proxy is being used
      microserviceid=''


      #############################################################################################################
      #                         CREATE TOPIC TO STORE TRAINED PARAMS FROM ALGORITHM  
      
      producetotopic="iot-trained-params-input"

      description="Topic to store the trained machine learning parameters"
      result=maadstml.vipercreatetopic(VIPERTOKEN,VIPERHOST,VIPERPORT,producetotopic,companyname,
                                     myname,myemail,mylocation,description,enabletls,
                                     brokerhost,brokerport,numpartitions,replication,
                                     microserviceid='')

      #############################################################################################################
      #                         VIPER CALLS HPDE TO PERFORM REAL_TIME MACHINE LEARNING ON TRAINING DATA 


      # deploy the algorithm to ./deploy folder - otherwise it will be in ./models folder
      deploy=1
      # number of models runs to find the best algorithm
      modelruns=100
      # Go to the last offset of the partition in partition_training variable
      offset=-1
      # If 0, this is not a logistic model where dependent variable is discreet
      islogistic=1
      # set network timeout for communication between VIPER and HPDE in seconds
      # increase this number if you timeout
      networktimeout=600

      # This parameter will attempt to fine tune the model search space - a number close to 0 means you will have lots of
      # models but their quality may be low.  A number close to 100 means you will have fewer models but their predictive
      # quality will be higher.
      modelsearchtuner=90

      #this is the dependent variable
      dependentvariable="failure"
      # Assign the independentvariable streams
      independentvariables="Voltage_preprocessed_AnomProb,Current_preprocessed_AnomProb"
            
      rollbackoffsets=500
      consumeridtrainingdata2=''
      partition_training=''
      producerid=''
      consumefrom=''

      topicid=-1 # pickup any topicid      
      fullpathtotrainingdata='/Viper-tml/viperlogs/iotlogistic'

     # These are the conditions that sets the dependent variable to a 1 - if condition not met it will be 0
      processlogic='classification_name=failure_prob:Voltage_preprocessed_AnomProb=55,n:Current_preprocessed_AnomProb=55,n'
      
      identifier="IOT Performance Monitor and Failure Probability Model"

      array=0
      transformtype='' # Sets the model to: log-lin,lin-log,log-log
      sendcoefto=''  # you can send coefficients to another topic for further processing
      coeftoprocess=''  # indicate the index of the coefficients to process i.e. 0,1,2
      coefsubtopicnames=''  # Give the coefficients a name: constant,elasticity,elasticity2
      identifier="IoT Failure Probability Model"

     # Call HPDE to train the model
      result=maadstml.viperhpdetraining(VIPERTOKEN,VIPERHOST,VIPERPORT,consumefrom,producetotopic,
                                      companyname,consumeridtrainingdata2,producerid, HPDEHOST,
                                      viperconfigfile,enabletls,partition_training,
                                      deploy,modelruns,modelsearchtuner,HPDEPORT,offset,islogistic,
                                      brokerhost,brokerport,networktimeout,microserviceid,topicid,maintopic,
                                      independentvariables,dependentvariable,rollbackoffsets,fullpathtotrainingdata,processlogic,identifier)    
    

dag = startmachinelearning()
