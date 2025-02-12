import maadstml
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from datetime import datetime
from airflow.decorators import dag, task
import sys
import tsslogging
import os
import subprocess
import random
import time

sys.dont_write_bytecode = True
######################################## USER CHOOSEN PARAMETERS ########################################
default_args = {
  'myname' : 'Sebastian Maurice',   # <<< *** Change as needed      
  'enabletls': '1',   # <<< *** 1=connection is encrypted, 0=no encryption
  'microserviceid' : '', # <<< *** leave blank
  'producerid' : 'iotsolution',    # <<< *** Change as needed   
  'preprocess_data_topic' : 'iot-preprocess', # << *** data for the independent variables - You created this in STEP 2
  'ml_prediction_topic' : 'iot-ml-prediction-results-output', # topic to store the predictions - You created this in STEP 2
  'description' : 'TML solution',    # <<< *** Change as needed   
  'companyname' : 'Otics', # <<< *** Change as needed      
  'myemail' : 'Your email', # <<< *** Change as needed      
  'mylocation' : 'Your location', # <<< *** Change as needed      
  'brokerhost' : '', # <<< *** Leave as is 
  'brokerport' : '-999', # <<< *** Leave as is
  'streamstojoin' : 'Power_preprocessed_AnomProb', # << ** These are the streams in the preprocess_data_topic for these independent variables
  'inputdata' : '', # << ** You can specify independent variables manually - rather than consuming from the preprocess_data_topic stream
  'consumefrom' : 'ml-data', # << This is ml_data_topic in STEP 5 that contains the estimated parameters
  'mainalgokey' : '', # leave blank
  'offset' : '-1', # << ** input data will start from the end of the preprocess_data_topic and rollback maxrows
  'delay' : '60', # << network delay parameter 
  'usedeploy' : '1', # << 1=use algorithms in ./deploy folder, 0=use ./models folder
  'networktimeout' : '6000', # << additional network parameter 
  'maxrows' : '50',  # << ** the number of offsets to rollback - For example, if 50, you will get 50 predictions continuously 
  'produceridhyperprediction' : '',  # << leave blank
  'consumeridtraininedparams' : '',  # << leave blank
  'groupid' : '',  # << leave blank
  'topicid' : '-1',   # << leave as is
  'pathtoalgos' : '/Viper-ml/viperlogs/iotlogistic', # << this is specified in fullpathtotrainingdata in STEP 5
  'array' : '0', # 0=do not save as array, 1=save as array   
  'HPDEADDR' : 'http://' # Do not modify
}
######################################## DO NOT MODIFY BELOW #############################################

VIPERTOKEN=""
VIPERHOST=""
VIPERPORT=""
HPDEHOSTPREDICT=''
HPDEPORTPREDICT=''
HTTPADDR=""    

# that is a change 2
# Set Global variable for Viper confifuration file - change the folder path for your computer
viperconfigfile="/Viper-predict/viper.env"

mainproducerid = default_args['producerid']     
maintopic=default_args['preprocess_data_topic']
predictiontopic=default_args['ml_prediction_topic']


def performPrediction():

        
      # Set personal data
      companyname=default_args['companyname']
      myname=default_args['myname']
      myemail=default_args['myemail']
      mylocation=default_args['mylocation']

      # Enable SSL/TLS communication with Kafka
      enabletls=int(default_args['enabletls'])
      # If brokerhost is empty then this function will use the brokerhost address in your
      # VIPER.ENV in the field 'KAFKA_CONNECT_BOOTSTRAP_SERVERS'
      brokerhost=default_args['brokerhost']
      # If this is -999 then this function uses the port address for Kafka in VIPER.ENV in the
      # field 'KAFKA_CONNECT_BOOTSTRAP_SERVERS'
      brokerport=int(default_args['brokerport'])
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
      offset=int(default_args['offset']) #-1
      # wait 60 seconds for Kafka - if exceeded then VIPER will backout
      delay=int(default_args['delay'])
      # use the deployed algorithm - must exist in ./deploy folder
      usedeploy=int(default_args['usedeploy'])
      # Network timeout
      networktimeout=int(default_args['networktimeout'])
      # maxrows - this is percentage to rollback stream

      if 'step6maxrows' in os.environ:
        maxrows=int(os.environ['step6maxrows'])
      else:
        maxrows=int(default_args['maxrows'])
      #Start predicting with new data streams
      produceridhyperprediction=default_args['produceridhyperprediction']
      consumeridtraininedparams=default_args['consumeridtraininedparams']
      groupid=default_args['groupid']
      topicid=int(default_args['topicid'])  # -1 to predict for current topicids in the stream

      # Path where the trained algorithms are stored in the machine learning python file
      pathtoalgos=default_args['pathtoalgos'] #'/Viper-tml/viperlogs/iotlogistic'
      array=int(default_args['array'])
      ml_prediction_topic = default_args['ml_prediction_topic']    
    
      result6=maadstml.viperhpdepredict(VIPERTOKEN,VIPERHOST,VIPERPORT,consumefrom,ml_prediction_topic,
                                     companyname,consumeridtraininedparams,
                                     produceridhyperprediction, HPDEHOSTPREDICT,inputdata,maxrows,mainalgokey,
                                     -1,offset,enabletls,delay,HPDEPORTPREDICT,
                                     brokerhost,brokerport,networktimeout,usedeploy,microserviceid,
                                     topicid,maintopic,streamstojoin,array,pathtoalgos)



def windowname(wtype,sname,dagname):
    randomNumber = random.randrange(10, 9999)
    wn = "python-{}-{}-{},{}".format(wtype,randomNumber,sname,dagname)
    with open("/tmux/pythonwindows_{}.txt".format(sname), 'a', encoding='utf-8') as file: 
      file.writelines("{}\n".format(wn))
    
    return wn

def startpredictions(**context):
    
       sd = context['dag'].dag_id
       sname=context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_solutionname".format(sd))
       pname=context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_projectname".format(sd))
       
       VIPERTOKEN = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERTOKEN".format(sname))
       VIPERHOST = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERHOSTPREDICT".format(sname))
       VIPERPORT = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERPORTPREDICT".format(sname))
       HTTPADDR = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_HTTPADDR".format(sname))
       HPDEADDR = default_args['HPDEADDR']

       HPDEHOSTPREDICT = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_HPDEHOSTPREDICT".format(sname))
       HPDEPORTPREDICT = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_HPDEPORTPREDICT".format(sname))
        
       chip = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_chip".format(sname)) 
       ti = context['task_instance']
       ti.xcom_push(key="{}_preprocess_data_topic".format(sname),value=default_args['preprocess_data_topic'])
       ti.xcom_push(key="{}_ml_prediction_topic".format(sname),value=default_args['ml_prediction_topic'])
       ti.xcom_push(key="{}_streamstojoin".format(sname),value=default_args['streamstojoin'])
       ti.xcom_push(key="{}_inputdata".format(sname),value=default_args['inputdata'])
       ti.xcom_push(key="{}_consumefrom".format(sname),value=default_args['consumefrom'])
       ti.xcom_push(key="{}_offset".format(sname),value="_{}".format(default_args['offset']))
       ti.xcom_push(key="{}_delay".format(sname),value="_{}".format(default_args['delay']))
       ti.xcom_push(key="{}_usedeploy".format(sname),value="_{}".format(default_args['usedeploy']))
       ti.xcom_push(key="{}_networktimeout".format(sname),value="_{}".format(default_args['networktimeout']))

       maxrows=default_args['maxrows']
       if 'step6maxrows' in os.environ:
          ti.xcom_push(key="{}_maxrows".format(sname),value="_{}".format(os.environ['step6maxrows']))
          maxrows=os.environ['step6maxrows']
       else:  
         ti.xcom_push(key="{}_maxrows".format(sname),value="_{}".format(default_args['maxrows']))
       ti.xcom_push(key="{}_topicid".format(sname),value="_{}".format(default_args['topicid']))
       ti.xcom_push(key="{}_pathtoalgos".format(sname),value=default_args['pathtoalgos'])
       ti.xcom_push(key="{}_HPDEADDR".format(sname), value=HPDEADDR)
    
       repo=tsslogging.getrepo() 
       if sname != '_mysolution_':
        fullpath="/{}/tml-airflow/dags/tml-solutions/{}/{}".format(repo,pname,os.path.basename(__file__))  
       else:
         fullpath="/{}/tml-airflow/dags/{}".format(repo,os.path.basename(__file__))  
            
       wn = windowname('predict',sname,sd)     
       subprocess.run(["tmux", "new", "-d", "-s", "{}".format(wn)])
       subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "cd /Viper-predict", "ENTER"])
       subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "python {} 1 {} {}{} {} {}{} {} {}".format(fullpath,VIPERTOKEN,HTTPADDR,VIPERHOST,VIPERPORT[1:],HPDEADDR,HPDEHOSTPREDICT,HPDEPORTPREDICT[1:],maxrows), "ENTER"])        

if __name__ == '__main__':
    if len(sys.argv) > 1:
       if sys.argv[1] == "1":          
         repo=tsslogging.getrepo()
         try:   
           tsslogging.tsslogit("Predictions DAG in {}".format(os.path.basename(__file__)), "INFO" )                     
           tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")            
         except Exception as e:
            #git push -f origin main
            os.chdir("/{}".format(repo))
            subprocess.call("git push -f origin main", shell=True)
    
         VIPERTOKEN=sys.argv[2]
         VIPERHOST=sys.argv[3]
         VIPERPORT=sys.argv[4]
         HPDEHOSTPREDICT=sys.argv[5]
         HPDEPORTPREDICT=sys.argv[6]    
         maxrows =  sys.argv[7]
         default_args['maxrows'] = maxrows
         
         tsslogging.locallogs("INFO", "STEP 6: Predictions started")
         while True:
          try:              
            performPrediction()      
            time.sleep(1)
          except Exception as e:
            tsslogging.locallogs("ERROR", "STEP 6: Predictions DAG in {} {}".format(os.path.basename(__file__),e))
            tsslogging.tsslogit("Predictions DAG in {} {}".format(os.path.basename(__file__),e), "ERROR" )                     
            tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")
            break
