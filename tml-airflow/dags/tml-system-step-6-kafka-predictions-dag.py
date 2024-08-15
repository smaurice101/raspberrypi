import maadstml
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from datetime import datetime
from airflow.decorators import dag, task
import sys

sys.dont_write_bytecode = True
######################################## USER CHOOSEN PARAMETERS ########################################
default_args = {
  'myname' : 'Sebastian Maurice',   # <<< *** Change as needed      
  'enabletls': 1,   # <<< *** 1=connection is encrypted, 0=no encryption
  'microserviceid' : '', # <<< *** leave blank
  'producerid' : 'iotsolution',    # <<< *** Change as needed   
  'preprocess_data_topic' : 'iot-preprocess-data', # << *** data for the independent variables - You created this in STEP 2
  'ml_prediction_topic' : 'ml-predictions', # topic to store the predictions - You created this in STEP 2
  'description' : 'TML solution',    # <<< *** Change as needed   
  'companyname' : 'Your company', # <<< *** Change as needed      
  'myemail' : 'Your email', # <<< *** Change as needed      
  'mylocation' : 'Your location', # <<< *** Change as needed      
  'brokerhost' : '', # <<< *** Change as needed      
  'brokerport' : -999, # <<< *** Change as needed      
  'streamstojoin' : 'Voltage_preprocessed_AnomProb,Current_preprocessed_AnomProb', # << ** These are the streams in the preprocess_data_topic for these independent variables
  'inputdata' : '', # << ** You can specify independent variables manually - rather than consuming from the preprocess_data_topic stream
  'consumefrom' : '', # << This is ml_data_topic in STEP 5 that contains the estimated parameters
  'mainalgokey' : '', # leave blank
  'offset' : -1, # << ** input data will start from the end of the preprocess_data_topic and rollback maxrows
  'delay' : 60, # << network delay parameter 
  'usedeploy' : '', # << 1=use algorithms in ./deploy folder, 0=use ./models folder
  'networktimeout' : 6000, # << additional network parameter 
  'maxrows' : '',  # << ** the number of offsets to rollback - For example, if 50, you will get 50 predictions continuously 
  'produceridhyperprediction' : '',  # << leave blank
  'consumeridtraininedparams' : '',  # << leave blank
  'groupid' : '',  # << leave blank
  'topicid' : -1,   # << leave as is
  'pathtoalgos' : '', # << this is specified in fullpathtotrainingdata in STEP 5
  'array' : 0, # 0=do not save as array, 1=save as array    
  'start_date': datetime (2024, 6, 29),    # <<< *** Change as needed   
  'retries': 1,   # <<< *** Change as needed   
    
}
######################################## DO NOT MODIFY BELOW #############################################

# Instantiate your DAG
@dag(dag_id="tml-system-step-6-kafka-predictions-dag", default_args=default_args, tags=["tml-system-step-6-kafka-predictions-dag"], schedule=None,catchup=False)
def startpredictions():
  # This sets the lat/longs for the IoT devices so it can be map
  VIPERTOKEN=""
  VIPERHOST=""
  VIPERPORT=""
  HPDEHOST=''
  HPDEPORT=''
    

  # Set Global variable for Viper confifuration file - change the folder path for your computer
  viperconfigfile="/Viper-predict/viper.env"

  maintopic =  default_args['ml_data_tpic']  
  mainproducerid = default_args['producerid']     
                
  VIPERTOKEN = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="VIPERTOKEN")
  VIPERHOST = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="VIPERHOST")
  VIPERPORT = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="VIPERPORT")

  HPDEHOST = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="HPDEHOST")
  HPDEPORT = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="HPDEPORT")

  @task(task_id="performPredictions")  
  def performPrediction(maintopic):
#############################################################################################################
#                                     JOIN DATA STREAMS 

      # Set personal data
      companyname=default_args['companyname']
      myname=default_args['myname']
      myemail=default_args['myemail']
      mylocation=default_args['mylocation']

      # Enable SSL/TLS communication with Kafka
      enabletls=default_args['enabletls']
      # If brokerhost is empty then this function will use the brokerhost address in your
      # VIPER.ENV in the field 'KAFKA_CONNECT_BOOTSTRAP_SERVERS'
      brokerhost=default_args['brokerhost']
      # If this is -999 then this function uses the port address for Kafka in VIPER.ENV in the
      # field 'KAFKA_CONNECT_BOOTSTRAP_SERVERS'
      brokerport=default_args['brokerport']
      # If you are using a reverse proxy to reach VIPER then you can put it here - otherwise if
      # empty then no reverse proxy is being used
      microserviceid=default_args['microserviceid']

      description=default_args['description']
      
      # Note these are the same streams or independent variables that are in the machine learning python file
      streamstojoin=default_args['streamstojoin']  #"Voltage_preprocessed_AnomProb,Current_preprocessed_AnomProb"

      #############################################################################################################
      #                                     START HYPER-PREDICTIONS FROM ESTIMATED PARAMETERS
      # Use the topic created from function viperproducetotopicstream for new data for 
      # independent variables
      inputdata=default_args['inputdata']

      # Consume from holds the algorithms
      consumefrom=default_args['consumefrom'] #"iot-trained-params-input"
      
      # if you know the algorithm key put it here - this will speed up the prediction
      mainalgokey=default_args['mainalgokey']
      # Offset=-1 means go to the last offset of hpdetraining_partition
      offset=default_args['offset'] #-1
      # wait 60 seconds for Kafka - if exceeded then VIPER will backout
      delay=default_args['delay']
      # use the deployed algorithm - must exist in ./deploy folder
      usedeploy=default_args['usedeploy']
      # Network timeout
      networktimeout=default_args['networktimeout']
      # maxrows - this is percentage to rollback stream
      maxrows=default_args['maxrows']
      #Start predicting with new data streams
      produceridhyperprediction=default_args['produceridhyperprediction']
      consumeridtraininedparams=default_args['consumeridtraininedparams']
      groupid=default_args['groupid']
      topicid=default_args['topicid']  # -1 to predict for current topicids in the stream

      # Path where the trained algorithms are stored in the machine learning python file
      pathtoalgos=default_args['pathtoalgos'] #'/Viper-tml/viperlogs/iotlogistic'
      array=default_args['array']
      
      result6=maadstml.viperhpdepredict(VIPERTOKEN,VIPERHOST,VIPERPORT,consumefrom,producetotopic,
                                     companyname,consumeridtraininedparams,
                                     produceridhyperprediction, HPDEHOST,inputdata,maxrows,mainalgokey,
                                     -1,offset,enabletls,delay,HPDEPORT,
                                     brokerhost,brokerport,networktimeout,usedeploy,microserviceid,
                                     topicid,maintopic,streamstojoin,array,pathtoalgos)

  while True:
    performPrediction(maintopic)      

#############################################################################################################
#                                     SETUP THE TOPIC DATA STREAMS EXAMPLE

# Topic to retreieve the new preprocessed data for predictions
maintopic="iot-preprocess"

# Topic to store the predictions
predictiontopic="iot-ml-prediction-results-output"

      while True:
          performPrediction(maintopic,producerid,VIPERPORT,-1,predictiontopic)
          time.sleep(.1)
          


dag = startpredictions()
