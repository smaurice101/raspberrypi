from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from datetime import datetime
from airflow.decorators import dag, task
import sys
import maadstml
import tsslogging
import os
import subprocess
import time
import random

sys.dont_write_bytecode = True
######################################## USER CHOOSEN PARAMETERS ########################################
default_args = {
  'owner' : 'Sebastian Maurice',  # <<< *** Change as needed      
  'enabletls': '1', # <<< *** 1=connection is encrypted, 0=no encryption
  'microserviceid' : '',  # <<< *** leave blank
  'producerid' : 'iotsolution',   # <<< *** Change as needed   
  'raw_data_topic' : 'iot-raw-data', # *************** INCLUDE ONLY ONE TOPIC - This is one of the topic you created in SYSTEM STEP 2
  'preprocess_data_topic' : 'iot-preprocess', # *************** INCLUDE ONLY ONE TOPIC - This is one of the topic you created in SYSTEM STEP 2
  'maxrows' : '800', # <<< ********** Number of offsets to rollback the data stream -i.e. rollback stream by 500 offsets
  'offset' : '-1', # <<< Rollback from the end of the data streams  
  'brokerhost' : '',   # <<< *** Leave as is
  'brokerport' : '-999',  # <<< *** Leave as is   
  'preprocessconditions' : '', ## <<< Leave blank      
  'delay' : '70', # Add a 70 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic     
  'array' : '0', # do not modify
  'saveasarray' : '1', # do not modify
  'topicid' : '-999', # do not modify
  'rawdataoutput' : '1', # <<< 1 to output raw data used in the preprocessing, 0 do not output
  'asynctimeout' : '120', # <<< 120 seconds for connection timeout 
  'timedelay' : '0', # <<< connection delay
  'tmlfilepath' : '', # leave blank
  'usemysql' : '1', # do not modify
  'streamstojoin' : '', # leave blank
  'identifier' : 'IoT device performance and failures', # <<< ** Change as needed
  'preprocesstypes' : 'anomprob,trend,avg', # <<< **** MAIN PREPROCESS TYPES CHNAGE AS NEEDED refer to https://tml-readthedocs.readthedocs.io/en/latest/
  'pathtotmlattrs' : 'oem=n/a,lat=n/a,long=n/a,location=n/a,identifier=n/a', # Change as needed     
  'jsoncriteria' : 'uid=metadata.dsn,filter:allrecords~\
subtopics=metadata.property_name~\
values=datapoint.value~\
identifiers=metadata.display_name~\
datetime=datapoint.updated_at~\
msgid=datapoint.id~\
latlong=lat:long', # <<< **** Specify your json criteria. Here is an example of a multiline json --  refer to https://tml-readthedocs.readthedocs.io/en/latest/
}

######################################## DO NOT MODIFY BELOW #############################################

# Instantiate your DAG
@dag(dag_id="tml_system_step_4_kafka_preprocess_dag", default_args=default_args, tags=["tml_system_step_4_kafka_preprocess_dag"], start_date=datetime(2023, 1, 1),schedule=None,catchup=False)
def startprocessing():
  def empty():
     pass
dag = startprocessing()

VIPERTOKEN=""
VIPERHOST=""
VIPERPORT=""
HTTPADDR=""

def processtransactiondata():
 global VIPERTOKEN
 global VIPERHOST
 global VIPERPORT   
 global HTTPADDR
 preprocesstopic = default_args['preprocess_data_topic']
 maintopic =  default_args['raw_data_topic']  
 mainproducerid = default_args['producerid']     
  
#############################################################################################################
  #                                    PREPROCESS DATA STREAMS


  # Roll back each data stream by 10 percent - change this to a larger number if you want more data
  # For supervised machine learning you need a minimum of 30 data points in each stream
 maxrows=int(default_args['maxrows'])

  # Go to the last offset of each stream: If lastoffset=500, then this function will rollback the 
  # streams to offset=500-50=450
 offset=int(default_args['offset'])
  # Max wait time for Kafka to response on milliseconds - you can increase this number if
  #maintopic to produce the preprocess data to
 topic=maintopic
  # producerid of the topic
 producerid=mainproducerid
  # use the host in Viper.env file
 brokerhost=default_args['brokerhost']
  # use the port in Viper.env file
 brokerport=int(default_args['brokerport'])
  #if load balancing enter the microsericeid to route the HTTP to a specific machine
 microserviceid=default_args['microserviceid']


  # You can preprocess with the following functions: MAX, MIN, SUM, AVG, COUNT, DIFF,OUTLIERS
  # here we will take max values of the arcturus-humidity, we will Diff arcturus-temperature, and average arcturus-Light_Intensity
  # NOTE: The number of process logic functions MUST match the streams - the operations will be applied in the same order
#
 preprocessconditions=default_args['preprocessconditions']

 # Add a 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic 
 delay=int(default_args['delay'])
 # USE TLS encryption when sending to Kafka Cloud (GCP/AWS/Azure)
 enabletls=int(default_args['enabletls'])
 array=int(default_args['array'])
 saveasarray=int(default_args['saveasarray'])
 topicid=int(default_args['topicid'])

 rawdataoutput=int(default_args['rawdataoutput'])
 asynctimeout=int(default_args['asynctimeout'])
 timedelay=int(default_args['timedelay'])

 jsoncriteria = default_args['jsoncriteria']

 tmlfilepath=default_args['tmlfilepath']
 usemysql=int(default_args['usemysql'])

 streamstojoin=default_args['streamstojoin']
 identifier = default_args['identifier']

 # if dataage - use:dataage_utcoffset_timetype
 preprocesstypes=default_args['preprocesstypes']

 pathtotmlattrs=default_args['pathtotmlattrs']       
 raw_data_topic = default_args['raw_data_topic']  
 preprocess_data_topic = default_args['preprocess_data_topic']  
    
 try:
    result=maadstml.viperpreprocesscustomjson(VIPERTOKEN,VIPERHOST,VIPERPORT,topic,producerid,offset,jsoncriteria,rawdataoutput,maxrows,enabletls,delay,brokerhost,
                                      brokerport,microserviceid,topicid,streamstojoin,preprocesstypes,preprocessconditions,identifier,
                                      preprocesstopic,array,saveasarray,timedelay,asynctimeout,usemysql,tmlfilepath,pathtotmlattrs)
    #print(result)
    return result
 except Exception as e:
    print(e)
    return e

def windowname(wtype,sname,dagname):
    randomNumber = random.randrange(10, 9999)
    wn = "python-{}-{}-{},{}".format(wtype,randomNumber,sname,dagname)
    with open("/tmux/pythonwindows_{}.txt".format(sname), 'a', encoding='utf-8') as file: 
      file.writelines("{}\n".format(wn))
    
    return wn

def dopreprocessing(**context):
       tsslogging.locallogs("INFO", "STEP 4: Preprocessing started")
       sd = context['dag'].dag_id
       sname=context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_solutionname".format(sd))
       
       VIPERTOKEN = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERTOKEN".format(sname))
       VIPERHOST = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERHOSTPREPROCESS".format(sname))
       VIPERPORT = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERPORTPREPROCESS".format(sname))
       HTTPADDR = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_HTTPADDR".format(sname))

       chip = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_chip".format(sname)) 
                
       ti = context['task_instance']    
       ti.xcom_push(key="{}_raw_data_topic".format(sname), value=default_args['raw_data_topic'])
       ti.xcom_push(key="{}_preprocess_data_topic".format(sname), value=default_args['preprocess_data_topic'])
       ti.xcom_push(key="{}_preprocessconditions".format(sname), value=default_args['preprocessconditions'])
       ti.xcom_push(key="{}_delay".format(sname), value="_{}".format(default_args['delay']))
       ti.xcom_push(key="{}_array".format(sname), value="_{}".format(default_args['array']))
       ti.xcom_push(key="{}_saveasarray".format(sname), value="_{}".format(default_args['saveasarray']))
       ti.xcom_push(key="{}_topicid".format(sname), value="_{}".format(default_args['topicid']))
       ti.xcom_push(key="{}_rawdataoutput".format(sname), value="_{}".format(default_args['rawdataoutput']))
       ti.xcom_push(key="{}_asynctimeout".format(sname), value="_{}".format(default_args['asynctimeout']))
       ti.xcom_push(key="{}_timedelay".format(sname), value="_{}".format(default_args['timedelay']))
       ti.xcom_push(key="{}_usemysql".format(sname), value="_{}".format(default_args['usemysql']))
       ti.xcom_push(key="{}_preprocesstypes".format(sname), value=default_args['preprocesstypes'])
       ti.xcom_push(key="{}_pathtotmlattrs".format(sname), value=default_args['pathtotmlattrs'])
       ti.xcom_push(key="{}_identifier".format(sname), value=default_args['identifier'])
       ti.xcom_push(key="{}_jsoncriteria".format(sname), value=default_args['jsoncriteria'])
        
       repo=tsslogging.getrepo() 
       if sname != '_mysolution_':
        fullpath="/{}/tml-airflow/dags/tml-solutions/{}/{}".format(repo,sname,os.path.basename(__file__))  
       else:
         fullpath="/{}/tml-airflow/dags/{}".format(repo,os.path.basename(__file__))  
            
       wn = windowname('preprocess',sname,sd)     
       subprocess.run(["tmux", "new", "-d", "-s", "{}".format(wn)])
       subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "cd /Viper-preprocess", "ENTER"])
       subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "python {} 1 {} {}{} {}".format(fullpath,VIPERTOKEN,HTTPADDR,VIPERHOST,VIPERPORT[1:]), "ENTER"])        

if __name__ == '__main__':
    if len(sys.argv) > 1:
       if sys.argv[1] == "1": 
        repo=tsslogging.getrepo()
        try:            
          tsslogging.tsslogit("Preprocessing DAG in {}".format(os.path.basename(__file__)), "INFO" )                     
          tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")    
        except Exception as e:
            #git push -f origin main
            os.chdir("/{}".format(repo))
            subprocess.call("git push -f origin main", shell=True)
        
        VIPERTOKEN = sys.argv[2]
        VIPERHOST = sys.argv[3] 
        VIPERPORT = sys.argv[4]                  
        tsslogging.locallogs("INFO", "STEP 4: Preprocessing started")
                     
        while True:
          try: 
            processtransactiondata()
            time.sleep(1)
          except Exception as e:    
           tsslogging.locallogs("ERROR", "STEP 4: Preprocessing DAG in {} {}".format(os.path.basename(__file__),e))
           tsslogging.tsslogit("Preprocessing DAG in {} {}".format(os.path.basename(__file__),e), "ERROR" )                     
           tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")    
           break
