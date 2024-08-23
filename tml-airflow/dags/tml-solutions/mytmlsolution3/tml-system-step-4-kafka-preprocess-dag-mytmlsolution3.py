from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from datetime import datetime
from airflow.decorators import dag, task
import sys
import maadstml
import tsslogging
import os

sys.dont_write_bytecode = True
######################################## USER CHOOSEN PARAMETERS ########################################
default_args = {
  'owner' : 'Sebastian Maurice',  # <<< *** Change as needed      
  'enabletls': 1, # <<< *** 1=connection is encrypted, 0=no encryption
  'microserviceid' : '',  # <<< *** leave blank
  'producerid' : 'iotsolution',   # <<< *** Change as needed   
  'raw_data_topic' : 'iot-raw-data', # *************** INCLUDE ONLY ONE TOPIC - This is one of the topic you created in SYSTEM STEP 2
  'preprocess_data_topic' : 'iot-preprocess-data', # *************** INCLUDE ONLY ONE TOPIC - This is one of the topic you created in SYSTEM STEP 2
  'maxrows' : 500, # <<< ********** Number of offsets to rollback the data stream -i.e. rollback stream by 500 offsets
  'offset' : -1, # <<< Rollback from the end of the data streams  
  'brokerhost' : '',   # <<< *** Leave as is
  'brokerport' : -999,  # <<< *** Leave as is   
  'preprocessconditions' : '', ## <<< Leave blank      
  'delay' : 70, # Add a 70 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic     
  'array' : 0, # do not modify
  'saveasarray' : 1, # do not modify
  'topicid' : -999, # do not modify
  'rawdataoutput' : 1, # <<< 1 to output raw data used in the preprocessing, 0 do not output
  'asynctimeout' : 120, # <<< 120 seconds for connection timeout 
  'timedelay' : 0, # <<< connection delay
  'tmlfilepath' : '', # leave blank
  'usemysql' : 1, # do not modify
  'streamstojoin' : '', # leave blank
  'identifier' : 'IoT device performance and failures', # <<< ** Change as needed
  'preprocesstypes' : 'anomprob,trend,avg', # <<< **** MAIN PREPROCESS TYPES CHNAGE AS NEEDED refer to https://tml-readthedocs.readthedocs.io/en/latest/
  'pathtotmlattrs' : '', # Leave blank         
  'jsoncriteria' : '', # <<< **** Specify your json criteria  refer to https://tml-readthedocs.readthedocs.io/en/latest/
  'identifier' : 'TML solution',   # <<< *** Change as needed   
  'start_date': datetime (2024, 6, 29),  # <<< *** Change as needed   
  'retries': 1,  # <<< *** Change as needed   
    
}

######################################## DO NOT MODIFY BELOW #############################################

# Instantiate your DAG
@dag(dag_id="tml_system_step_4_kafka_preprocess_dag_mytmlsolution3", default_args=default_args, tags=["tml_system_step_4_kafka_preprocess_dag_mytmlsolution3"], schedule=None,catchup=False)
def startprocessing():
  # This sets the lat/longs for the IoT devices so it can be map
  VIPERTOKEN=""
  VIPERHOST=""
  VIPERPORT=""

    
  @task(task_id="processtransactiondata")
  def processtransactiondata():

     preprocesstopic = default_args['preprocess_data_topic']
     maintopic =  default_args['raw_data_topic']  
     mainproducerid = default_args['producerid']     
                
     VIPERTOKEN = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="VIPERTOKEN")
     VIPERHOST = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="VIPERHOST")
     VIPERPORT = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="VIPERPORT")
        
 #############################################################################################################
      #                                    PREPROCESS DATA STREAMS

      # Roll back each data stream by 10 percent - change this to a larger number if you want more data
      # For supervised machine learning you need a minimum of 30 data points in each stream
     maxrows=default_args['maxrows']
        
      # Go to the last offset of each stream: If lastoffset=500, then this function will rollback the 
      # streams to offset=500-50=450
     offset=default_args['offset']
      # Max wait time for Kafka to response on milliseconds - you can increase this number if
      #maintopic to produce the preprocess data to
     topic=maintopic
      # producerid of the topic
     producerid=mainproducerid
      # use the host in Viper.env file
     brokerhost=default_args['brokerhost']
      # use the port in Viper.env file
     brokerport=default_args['brokerport']
      #if load balancing enter the microsericeid to route the HTTP to a specific machine
     microserviceid=default_args['microserviceid']

  
      # You can preprocess with the following functions: MAX, MIN, SUM, AVG, COUNT, DIFF,OUTLIERS
      # here we will take max values of the arcturus-humidity, we will Diff arcturus-temperature, and average arcturus-Light_Intensity
      # NOTE: The number of process logic functions MUST match the streams - the operations will be applied in the same order
#
     preprocessconditions=default_args['preprocessconditions']
         
     # Add a 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic 
     delay=default_args['delay']
     # USE TLS encryption when sending to Kafka Cloud (GCP/AWS/Azure)
     enabletls=default_args['enabletls']
     array=default_args['array']
     saveasarray=default_args['saveasarray']
     topicid=default_args['topicid']
    
     rawdataoutput=default_args['rawdataoutput']
     asynctimeout=default_args['asynctimeout']
     timedelay=default_args['timedelay']

     jsoncriteria = default_args['jsoncriteria']
        
     tmlfilepath=default_args['tmlfilepath']
     usemysql=default_args['usemysql']

     streamstojoin=default_args['streamstojoin']
     identifier = default_args['identifier']

     # if dataage - use:dataage_utcoffset_timetype
     preprocesstypes=default_args['preprocesstypes']

     pathtotmlattrs=default_args['pathtotmlattrs']       
     try:
        result=maadstml.viperpreprocesscustomjson(VIPERTOKEN,VIPERHOST,VIPERPORT,topic,producerid,offset,jsoncriteria,rawdataoutput,maxrows,enabletls,delay,brokerhost,
                                          brokerport,microserviceid,topicid,streamstojoin,preprocesstypes,preprocessconditions,identifier,
                                          preprocesstopic,array,saveasarray,timedelay,asynctimeout,usemysql,tmlfilepath,pathtotmlattrs)
        #print(result)
        return result
     except Exception as e:
        print(e)
        return e
  
  if VIPERHOST != "":
     repo=tsslogging.getrepo()  
     tsslogging.tsslogit("Preprocessing DAG in {}".format(os.path.basename(__file__)), "INFO" )                     
     tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")    
        
     while True:
       try: 
         processtransactiondata()
       except Exception as e:     
         tsslogging.tsslogit("Preprocessing DAG in {} {}".format(os.path.basename(__file__),e), "ERROR" )                     
         tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")    
         break
            
    
dag = startprocessing()
