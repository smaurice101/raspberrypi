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
  'owner' : 'Sebastian Maurice',    # <<< *** Change as needed     
  'enabletls': 1,   # <<< *** 1=connection is encrypted, 0=no encryption   
  'microserviceid' : '',   # <<< *** leave blank
  'producerid' : 'iotsolution',    # <<< *** Change as needed   
  'topics' : 'iot-raw-data', # *************** This is one of the topic you created in SYSTEM STEP 2
  'identifier' : 'TML solution',    # <<< *** Change as needed   
  'inputfile' : '/rawdata/?',  # <<< ***** replace ?  to input file to read. NOTE this data file should JSON messages per line and stored in the HOST folder mapped to /rawdata folder 
  'start_date': datetime (2024, 6, 29),    # <<< *** Change as needed   
  'retries': 1,   # <<< *** Change as needed   
    
}
######################################## DO NOT MODIFY BELOW #############################################

# Instantiate your DAG
@dag(dag_id="tml-system-step-6-kafka-predictions-dag", default_args=default_args, tags=["tml-system-step-6-kafka-predictions-dag"], schedule=None,catchup=False)
def startproducingtotopic():
  # This sets the lat/longs for the IoT devices so it can be map
  VIPERTOKEN=""
  VIPERHOST=""
  VIPERPORT=""
  HPDEHOST=''
  HPDEPORT=''
    

# Set Global variable for Viper confifuration file - change the folder path for your computer
viperconfigfile="/Viper-predict/viper.env"

#############################################################################################################
#                                      STORE VIPER TOKEN
# Get the VIPERTOKEN from the file admin.tok - change folder location to admin.tok
# to your location of admin.tok
def getparams():
     global VIPERHOST, VIPERPORT, HTTPADDR, HTTPADDR2,HPDEHOST, HPDEPORT
     with open("/Viper-predict/admin.tok", "r") as f:
        VIPERTOKEN=f.read()

     if VIPERHOST=="":
        with open('/Viper-predict/viper.txt', 'r') as f:
          output = f.read()
          VIPERHOST = HTTPADDR + output.split(",")[0]
          VIPERPORT = output.split(",")[1]
        with open('/Hpde/hpde.txt', 'r') as f:
          output = f.read()
          HPDEHOST = HTTPADDR2 + output.split(",")[0]
          HPDEPORT = output.split(",")[1]
          
     return VIPERTOKEN

VIPERTOKEN=getparams()

if VIPERHOST=="":
    print("ERROR: Cannot read viper.txt: VIPERHOST is empty or HPDEHOST is empty")
if HPDEHOST=="":
    print("ERROR: Cannot read viper.txt: HPDEHOST is empty")


# Set personal data

def performPrediction(maintopic,producerid,VIPERPORT,topicid,producetotopic):
#############################################################################################################
#                                     JOIN DATA STREAMS 

      # Set personal data
      companyname="Otics Advanced Analytics"
      myname="Sebastian"
      myemail="Sebastian.Maurice"
      mylocation="Toronto"

      # Replication factor for Kafka redundancy
      replication=1
      # Number of partitions for joined topic
      numpartitions=1
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

      description="Topic containing joined streams for Machine Learning training dataset"
      
      # Note these are the same streams or independent variables that are in the machine learning python file
      streamstojoin="Voltage_preprocessed_AnomProb,Current_preprocessed_AnomProb"

      #############################################################################################################
      #                                     START HYPER-PREDICTIONS FROM ESTIMATED PARAMETERS
      # Use the topic created from function viperproducetotopicstream for new data for 
      # independent variables
      inputdata=""

      # Consume from holds the algorithms
      consumefrom="iot-trained-params-input"
      
      # if you know the algorithm key put it here - this will speed up the prediction
      mainalgokey=""
      # Offset=-1 means go to the last offset of hpdetraining_partition
      offset=-1
      # wait 60 seconds for Kafka - if exceeded then VIPER will backout
      delay=60000
      # use the deployed algorithm - must exist in ./deploy folder
      usedeploy=1
      # Network timeout
      networktimeout=120
      # maxrows - this is percentage to rollback stream
      maxrows=50
      #Start predicting with new data streams
      produceridhyperprediction=''
      consumeridtraininedparams=''
      groupid=''
      topicid=-1  # -1 to predict for current topicids in the stream

      # Path where the trained algorithms are stored in the machine learning python file
      pathtoalgos='/Viper-tml/viperlogs/iotlogistic'
      array=0
      
      result6=maadstml.viperhpdepredict(VIPERTOKEN,VIPERHOST,VIPERPORT,consumefrom,producetotopic,
                                     companyname,consumeridtraininedparams,
                                     produceridhyperprediction, HPDEHOST,inputdata,maxrows,mainalgokey,
                                     -1,offset,enabletls,delay,HPDEPORT,
                                     brokerhost,brokerport,networktimeout,usedeploy,microserviceid,
                                     topicid,maintopic,streamstojoin,array,pathtoalgos)


##########################################################################
#############################################################################################################
#                                     SETUP THE TOPIC DATA STREAMS EXAMPLE

# Topic to retreieve the new preprocessed data for predictions
maintopic="iot-preprocess"

# Topic to store the predictions
predictiontopic="iot-ml-prediction-results-output"

producerid=datasetup(maintopic,predictiontopic)

print("Started the predictions: ", maintopic,producerid)

def spawnvipers():
      while True:
          performPrediction(maintopic,producerid,VIPERPORT,-1,predictiontopic)
          time.sleep(.1)
          
spawnvipers()           


dag = startproducingtotopic()
