# Developed by: Sebastian Maurice, PhD
# Date: 2022-01-18 
# Toronto, Ontario Canada

#######################################################################################################################################

# This file will perform TML for Walmart Foot Traffic.  Before using this code you MUST have:
# 1) Downloaded and installed MAADS-VIPER from: https://github.com/smaurice101/transactionalmachinelearning

# 2) You have:
# a) VIPER listening for a connection on port IP: http://127.0.01 and PORT: 8000 (you can specify different IP and PORT
#    just change the  VIPERHOST="http://127.0.0.1" and VIPERPORT=8000)
# b) HPDE listening for a connection on port IP: http://127.0.01 and PORT: 8001 (you can specify different IP and PORT
#    just change the  hpdehost="http://127.0.0.1" and hpdeport=8001)

# 3) You have created a Kafka cluster in Confluent Cloud (https://confluent.cloud/)

# 4) You have updated the VIPER.ENV file in the following fields:
# a) KAFKA_CONNECT_BOOTSTRAP_SERVERS=[Enter the bootstrap server - this is the Kafka broker(s) - separate multiple brokers by a comma]
# b) KAFKA_ROOT=kafka
# c) SSL_CLIENT_CERT_FILE=[Enter the full path to client.cer.pem]
# d) SSL_CLIENT_KEY_FILE=[Enter the full path to client.key.pem]
# e) SSL_SERVER_CERT_FILE=[Enter the full path to server.cer.pem]

# f) CLOUD_USERNAME=[Enter the Cloud Username- this is the KEY]
# g) CLOUD_PASSWORD=[Enter the Cloud Password - this is the secret]

# NOTE: IF YOU GET STUCK WATCH THE YOUTUBE VIDEO: https://www.youtube.com/watch?v=b1fuIeC7d-8
# Or email support@otics.ca
#########################################################################################################################################

# Import the core libraries
import maadstml

# Uncomment IF using jupyter notebook
#import nest_asyncio

import json
import time
from joblib import Parallel, delayed

# Uncomment IF using jupyter notebook
#nest_asyncio.apply()

# Set Global variables for VIPER and HPDE - You can change IP and Port for your setup of 
# VIPER and HPDE
VIPERHOST="https://127.0.0.1"
VIPERPORT=21003
hpdehost="http://127.0.0.1"
hpdeport=30001

# Set Global variable for Viper confifuration file - change the folder path for your computer
#viperconfigfile="c:/maads/companies/firstgenesis/viper.env"
viperconfigfile="c:/maads/golang/go/bin/viper.env"

#############################################################################################################
#                                      STORE VIPER TOKEN
# Get the VIPERTOKEN from the file admin.tok - change folder location to admin.tok
# to your location of admin.tok
def getparams():
     with open("c:/maads/golang/go/bin/admin.tok", "r") as f:
        VIPERTOKEN=f.read()
     return VIPERTOKEN

VIPERTOKEN=getparams()

def performSupervisedMachineLearning(maintopic,topicid):

#############################################################################################################
#                                     JOIN DATA STREAMS 

      # Set personal data
      companyname="OTICS Advanced Analytics"
      myname="Sebastian"
      myemail="Sebastian.Maurice"
      mylocation="Toronto"

      # Replication factor for Kafka redundancy
      replication=3
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
      #independentvariables="Voltage_preprocessed_AnomProb,Current_preprocessed_AnomProb,Voltage_preprocessed_Avg,Current_preprocessed_Avg"
      independentvariables="Voltage_preprocessed_AnomProb,Current_preprocessed_AnomProb"
            
      rollbackoffsets=500
      consumeridtrainingdata2=''
      partition_training=''
      producerid=''
      consumefrom=''

      topicid=-1 # pickup any topicid
      
    #  fullpathtotrainingdata='c:/maads/golang/go/bin/viperlogs/models3/'

      fullpathtotrainingdata='c:/maads/golang/go/bin/viperlogs/iotlogistic'

      #logisticlogic: classification_name=failureprob;arcturus-temperature=12,22;arcturus-humidity=-n,4;
      processlogic='classification_name=failure_prob:Voltage_preprocessed_AnomProb=70,n:Current_preprocessed_AnomProb=70,n'
#      processlogic='classification_name=medicationfraud_prob:OUTPHARM_preprocessed_Geodiff=10,n:OUTPHARM_preprocessed_Uniquestrcount=1,n\
#:MedicationDispense_preprocessed_Avgtimediff=-n,592000'

      identifier="IOT Performance Monitor and Failure Probability Model"
#      transformtype='log-log' #log-lin,lin-log,log-log
#      sendcoefto='iot-preprocess'
 #     coeftoprocess='0,1,2'
  #    coefsubtopicnames='constant,elasticity,elasticity2'
      array=0
      transformtype='' #log-lin,lin-log,log-log
      sendcoefto=''
      coeftoprocess=''
      coefsubtopicnames=''
      identifier="IoT Failure Probability Model"

      result=maadstml.viperhpdetraining(VIPERTOKEN,VIPERHOST,VIPERPORT,consumefrom,producetotopic,
                                      companyname,consumeridtrainingdata2,producerid, hpdehost,
                                      viperconfigfile,enabletls,partition_training,
                                      deploy,modelruns,modelsearchtuner,hpdeport,offset,islogistic,
                                      brokerhost,brokerport,networktimeout,microserviceid,topicid,maintopic,
                                      independentvariables,dependentvariable,rollbackoffsets,fullpathtotrainingdata,processlogic,identifier)    
      
      print("Training Result=",result)
##########################################################################

maintopic="iot-preprocess"

while True:
  try:
     # Re-train every 10 seconds- change to whatever number you wish
     performSupervisedMachineLearning(maintopic,0)
   #  time.sleep(10)  
  except Exception as e:
    print(e)   
    continue   
