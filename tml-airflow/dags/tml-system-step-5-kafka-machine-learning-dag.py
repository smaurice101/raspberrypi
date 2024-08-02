from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from datetime import datetime
from airflow.decorators import dag, task

######################################## USER CHOOSEN PARAMETERS ########################################
default_args = {
  'owner' : 'Sebastian Maurice',    
  'enabletls': 1,
  'microserviceid' : '',
  'producerid' : 'iotsolution',  
  'topics' : 'iot-raw-data', # *************** This is one of the topic you created in SYSTEM STEP 2
  'identifier' : 'TML solution',  
  'inputfile' : '/rawdata/?',  # <<< ***** replace ?  to input file to read. NOTE this data file should JSON messages per line and stored in the HOST folder mapped to /rawdata folder 
  'start_date': datetime (2024, 6, 29),
  'retries': 1,
    
}

######################################## USER CHOOSEN PARAMETERS ########################################

######################################## START DAG AND TASK #############################################

# Instantiate your DAG
@dag(dag_id="tml-system-step-5-kafka-machine-learning-dag", default_args=default_args, tags=["tml-system-step-5-kafka-machine-learning-dag"], schedule=None,catchup=False)
def startproducingtotopic():
  # This sets the lat/longs for the IoT devices so it can be map
  VIPERTOKEN=""
  VIPERHOST=""
  VIPERPORT=""
    


def sendtransactiondata(maintopic,mainproducerid,VIPERPORT,index,preprocesstopic):


 #############################################################################################################
      #                                    PREPROCESS DATA STREAMS

      # Roll back each data stream by 10 percent - change this to a larger number if you want more data
      # For supervised machine learning you need a minimum of 30 data points in each stream
     maxrows=500
      # Go to the last offset of each stream: If lastoffset=500, then this function will rollback the 
      # streams to offset=500-50=450
     offset=-1
      # Max wait time for Kafka to response on milliseconds - you can increase this number if
      #maintopic to produce the preprocess data to
     topic=maintopic
      # producerid of the topic
     producerid=mainproducerid
      # use the host in Viper.env file
     brokerhost=''
      # use the port in Viper.env file
     brokerport=-999
      #if load balancing enter the microsericeid to route the HTTP to a specific machine
     microserviceid=''

  
      # You can preprocess with the following functions: MAX, MIN, SUM, AVG, COUNT, DIFF,OUTLIERS
      # here we will take max values of the arcturus-humidity, we will Diff arcturus-temperature, and average arcturus-Light_Intensity
      # NOTE: The number of process logic functions MUST match the streams - the operations will be applied in the same order
#
     preprocessconditions=''
         
     # Add a 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic 
     delay=70
     # USE TLS encryption when sending to Kafka Cloud (GCP/AWS/Azure)
     enabletls=1
     array=0
     saveasarray=1
     topicid=-999
    
     rawdataoutput=1
     asynctimeout=120
     timedelay=0

     jsoncriteria='uid=metadata.dsn,filter:allrecords~\
subtopics=metadata.property_name~\
values=datapoint.value~\
identifiers=metadata.display_name~\
datetime=datapoint.updated_at~\
msgid=datapoint.id~\
latlong=lat:long'     

     tmlfilepath=''
     usemysql=1

     streamstojoin="" 
     identifier = "IoT device performance and failures"

     # if dataage - use:dataage_utcoffset_timetype
     preprocesslogic='anomprob,trend,avg'

     pathtotmlattrs='oem=n/a,lat=n/a,long=n/a,location=n/a,identifier=n/a'          
     try:
        result=maadstml.viperpreprocesscustomjson(VIPERTOKEN,VIPERHOST,VIPERPORT,topic,producerid,offset,jsoncriteria,rawdataoutput,maxrows,enabletls,delay,brokerhost,
                                          brokerport,microserviceid,topicid,streamstojoin,preprocesslogic,preprocessconditions,identifier,
                                          preprocesstopic,array,saveasarray,timedelay,asynctimeout,usemysql,tmlfilepath,pathtotmlattrs)
        #print(result)
        return result
     except Exception as e:
        print(e)
        return e
     

#############################################################################################################
#                                     SETUP THE TOPIC DATA STREAMS FOR WALMART EXAMPLE

maintopic='iot-mainstream'
preprocesstopic='iot-preprocess'
maintopic,producerid=datasetup(maintopic,preprocesstopic)
print("Started Preprocessing: ", maintopic,producerid)

async def startviper():

        print("Start Preprocess-iot-monitor-customdata Request:",datetime.datetime.now())
        while True:
          try:   
            sendtransactiondata(maintopic,producerid,VIPERPORT,-1,preprocesstopic)            
            time.sleep(1)
          except Exception as e:
            print("ERROR:",e)
            continue
   
async def spawnvipers():

    loop.run_until_complete(startviper())
  
loop = asyncio.new_event_loop()
loop.create_task(spawnvipers())
asyncio.set_event_loop(loop)

loop.run_forever()
    
  readdata(gettmlsystemsparams())
    

dag = startproducingtotopic()
