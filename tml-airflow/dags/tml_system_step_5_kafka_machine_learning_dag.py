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

sys.dont_write_bytecode = True
######################################## USER CHOOSEN PARAMETERS ########################################
default_args = {
  'myname' : 'Sebastian Maurice',   # <<< *** Change as needed      
  'enabletls': '1',   # <<< *** 1=connection is encrypted, 0=no encryption
  'microserviceid' : '', # <<< *** leave blank
  'producerid' : 'iotsolution',    # <<< *** Change as needed   
  'preprocess_data_topic' : 'iot-preprocess-data', # << *** topic/data to use for training datasets - You created this in STEP 2
  'ml_data_topic' : 'ml-data', # topic to store the trained algorithms  - You created this in STEP 2
  'identifier' : 'TML solution',    # <<< *** Change as needed   
  'companyname' : 'Your company', # <<< *** Change as needed      
  'myemail' : 'Your email', # <<< *** Change as needed      
  'mylocation' : 'Your location', # <<< *** Change as needed      
  'brokerhost' : '', # <<< *** Leave as is   
  'brokerport' : '-999', # <<< *** Leave as is
  'deploy' : '1', # <<< *** do not modofy
  'modelruns': '100', # <<< *** Change as needed      
  'offset' : '-1', # <<< *** Do not modify
  'islogistic' : '0',  # <<< *** Change as needed, 1=logistic, 0=not logistic
  'networktimeout' : '600', # <<< *** Change as needed      
  'modelsearchtuner' : '90', # <<< *This parameter will attempt to fine tune the model search space - A number close to 100 means you will have fewer models but their predictive quality will be higher.      
  'dependentvariable' : '', # <<< *** Change as needed, 
  'independentvariables': '', # <<< *** Change as needed, 
  'rollbackoffsets' : '500', # <<< *** Change as needed, 
  'consumeridtrainingdata2': '', # leave blank
  'partition_training' : '',  # leave blank
  'consumefrom' : '',  # leave blank
  'topicid' : '-1',  # leave as is
  'fullpathtotrainingdata' : '/Viper-ml/viperlogs/<choose foldername>',  #  # <<< *** Change as needed - add name for foldername that stores the training datasets
  'processlogic' : '',  # <<< *** Change as needed, i.e. classification_name=failure_prob:Voltage_preprocessed_AnomProb=55,n:Current_preprocessed_AnomProb=55,n
  'array' : '0',  # leave as is
  'transformtype' : '', # Sets the model to: log-lin,lin-log,log-log
  'sendcoefto' : '',  # you can send coefficients to another topic for further processing -- MUST BE SET IN STEP 2
  'coeftoprocess' : '', # indicate the index of the coefficients to process i.e. 0,1,2 For example, for a 3 estimated parameters 0=constant, 1,2 are the other estmated paramters
  'coefsubtopicnames' : '',  # Give the coefficients a name: constant,elasticity,elasticity2    
}

######################################## DO NOT MODIFY BELOW #############################################

# Instantiate your DAG
@dag(dag_id="tml_system_step_5_kafka_machine_learning_dag", default_args=default_args, tags=["tml_system_step_5_kafka_machine_learning_dag"], schedule=None,catchup=False)
def startmachinelearning():
  def empty():
      pass
dag = startmachinelearning()

# This sets the lat/longs for the IoT devices so it can be map
VIPERTOKEN=""
VIPERHOST=""
VIPERPORT=""
HPDEHOST = ''    
HPDEPORT = ''
HTTPADDR=""
maintopic =  default_args['preprocess_data_topic']  
mainproducerid = default_args['producerid']                     
        
def performSupervisedMachineLearning():
      
        
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

      #############################################################################################################
      #                         VIPER CALLS HPDE TO PERFORM REAL_TIME MACHINE LEARNING ON TRAINING DATA 


      # deploy the algorithm to ./deploy folder - otherwise it will be in ./models folder
      deploy=int(default_args['deploy'])
      # number of models runs to find the best algorithm
      modelruns=int(default_args['modelruns'])
      # Go to the last offset of the partition in partition_training variable
      offset=int(default_args['offset'])
      # If 0, this is not a logistic model where dependent variable is discreet
      islogistic=int(default_args['islogistic'])
      # set network timeout for communication between VIPER and HPDE in seconds
      # increase this number if you timeout
      networktimeout=int(default_args['networktimeout'])

      # This parameter will attempt to fine tune the model search space - a number close to 0 means you will have lots of
      # models but their quality may be low.  A number close to 100 means you will have fewer models but their predictive
      # quality will be higher.
      modelsearchtuner=int(default_args['modelsearchtuner'])

      #this is the dependent variable
      dependentvariable=default_args['dependentvariable']
      # Assign the independentvariable streams
      independentvariables=default_args['independentvariables'] #"Voltage_preprocessed_AnomProb,Current_preprocessed_AnomProb"
            
      rollbackoffsets=int(default_args['rollbackoffsets'])
      consumeridtrainingdata2=default_args['consumeridtrainingdata2']
      partition_training=default_args['partition_training']
      producerid=default_args['producerid']
      consumefrom=default_args['consumefrom']

      topicid=int(default_args['mylocation'])      
      fullpathtotrainingdata=default_args['fullpathtotrainingdata']

     # These are the conditions that sets the dependent variable to a 1 - if condition not met it will be 0
      processlogic=default_args['processlogic'] #'classification_name=failure_prob:Voltage_preprocessed_AnomProb=55,n:Current_preprocessed_AnomProb=55,n'
      
      identifier=default_args['identifier']

      producetotopic = default_args['ml_data_topic']
        
      array=int(default_args['array'])
      transformtype=default_args['transformtype'] # Sets the model to: log-lin,lin-log,log-log
      sendcoefto=default_args['sendcoefto']  # you can send coefficients to another topic for further processing
      coeftoprocess=default_args['coeftoprocess']  # indicate the index of the coefficients to process i.e. 0,1,2
      coefsubtopicnames=default_args['coefsubtopicnames']  # Give the coefficients a name: constant,elasticity,elasticity2

    
     # Call HPDE to train the model
      result=maadstml.viperhpdetraining(VIPERTOKEN,VIPERHOST,VIPERPORT,consumefrom,producetotopic,
                                      companyname,consumeridtrainingdata2,producerid, HPDEHOST,
                                      viperconfigfile,enabletls,partition_training,
                                      deploy,modelruns,modelsearchtuner,HPDEPORT,offset,islogistic,
                                      brokerhost,brokerport,networktimeout,microserviceid,topicid,maintopic,
                                      independentvariables,dependentvariable,rollbackoffsets,fullpathtotrainingdata,processlogic,identifier)    
 

def windowname(wtype,sname):
    randomNumber = random.randrange(10, 9999)
    wn = "python-{}-{}-{}".format(wtype,randomNumber,sname)
    with open("/tmux/pythonwindows_{}.txt".format(sname), 'a', encoding='utf-8') as file: 
      file.writelines("{}\n".format(wn))
    
    return wn

def startml(**context):
       VIPERTOKEN = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="VIPERTOKEN")
       VIPERHOST = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="VIPERHOSTML")
       VIPERPORT = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="VIPERPORTML")
       HTTPADDR = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="HTTPADDR")

       HPDEHOST = ti.xcom_pull(task_ids='step_1_solution_task_getparams',key="HPDEHOST")
       HPDEPORT = ti.xcom_pull(task_ids='step_1_solution_task_getparams',key="HPDEPORT")
       chip = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="chip") 
       ti = context['task_instance']
       ti.xcom_push(key="preprocess_data_topic", value=preprocess_data_topic)
       ti.xcom_push(key="ml_data_topic", value=ml_data_topic)
       ti.xcom_push(key="modelruns", value="_{}".format(modelruns))
       ti.xcom_push(key="offset", value="_{}".format(offset))
       ti.xcom_push(key="islogistic", value="_{}".format(islogistic))
       ti.xcom_push(key="networktimeout", value="_{}".format(networktimeout))
       ti.xcom_push(key="modelsearchtuner", value="_{}".format(modelsearchtuner))
       ti.xcom_push(key="dependentvariable", value=dependentvariable)
       ti.xcom_push(key="independentvariables", value=independentvariables)
       ti.xcom_push(key="rollbackoffsets", value="_{}".format(rollbackoffsets))
       ti.xcom_push(key="topicid", value="_{}".format(topicid))
       ti.xcom_push(key="consumefrom", value=consumefrom)
       ti.xcom_push(key="fullpathtotrainingdata", value=fullpathtotrainingdata)
       ti.xcom_push(key="transformtype", value=transformtype)
       ti.xcom_push(key="sendcoefto", value=sendcoefto)
       ti.xcom_push(key="coeftoprocess", value=coeftoprocess)
       ti.xcom_push(key="coefsubtopicnames", value=coefsubtopicnames)

       repo=tsslogging.getrepo() 
       sname = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="solutionname")
       if sname != '_mysolution_':
        fullpath="/{}/tml-airflow/dags/tml-solutions/{}/{}".format(repo,sname,os.path.basename(__file__))  
       else:
         fullpath="/{}/tml-airflow/dags/{}".format(repo,os.path.basename(__file__))  
            
       wn = windowname('ml',sname)     
       subprocess.run(["tmux", "new", "-d", "-s", "{}".format(wn)])
       subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "cd /Viper-ml", "ENTER"])
       subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "python {} 1 {} {}{} {} {} {}".format(fullpath,VIPERTOKEN, HTTPADDR, VIPERHOST, VIPERPORT[1:], HPDEHOST, HPDEPORT[1:]), "ENTER"])        

if __name__ == '__main__':
    if len(sys.argv) > 1:
       if sys.argv[1] == "1":          
        repo=tsslogging.getrepo()
        tsslogging.tsslogit("Machine Learning DAG in {}".format(os.path.basename(__file__)), "INFO" )                     
        tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")    
    
        while True:
         try:     
          VIPERTOKEN = sys.argv[2]
          VIPERHOST = sys.argv[3]
          VIPERPORT = sys.argv[4]
          HPDEHOST = sys.argv[5]
          HPDEPORT = sys.argv[6]
        
          performSupervisedMachineLearning()
         except Exception as e:
          tsslogging.tsslogit("Machine Learning DAG in {} {}".format(os.path.basename(__file__),e), "ERROR" )                     
          tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")    
          break
