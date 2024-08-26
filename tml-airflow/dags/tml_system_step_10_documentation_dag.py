from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime
from airflow.decorators import dag, task
import os 
import sys
import requests
import json
import subprocess
import tsslogging
import shutil
from git import Repo

sys.dont_write_bytecode = True

######################################################USER CHOSEN PARAMETERS ###########################################################
default_args = {    
 'start_date': datetime (2023, 1, 1),   # <<< *** Change as needed   
 'retries': 1,   # <<< *** Change as needed   
 'conf_project' : 'Transactional Machine Learning (TML)',
 'conf_copyright' : '2024, Otics Advanced Analytics, Incorporated - For Support email support@otics.ca',
 'conf_author' : 'Sebastian Maurice',
 'conf_release' : '0.1',
 'conf_version' : '0.1.0'
}

############################################################### DO NOT MODIFY BELOW ####################################################
# Instantiate your DAG
@dag(dag_id="tml_system_step_10_documentation_dag", default_args=default_args, tags=["tml_system_step_10_documentation_dag"], start_date=datetime(2023, 1, 1), schedule=None,  catchup=False)
def startdocumentation():
    # Define tasks
    def empty():
        pass
dag = startdocumentation()

def generatedoc(**context):    
    
    if 'tssdoc' in os.environ:
        if os.environ['tssdoc']==1:
            return
    
    sname = context['ti'].xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="solutionname")
    shutil.copytree('/tss_readthedocs', "/{}".format(sname), dirs_exist_ok=True) 

    subprocess.call(["sed", "-i", "-e",  "s/--project--/{}/g".format(default_args['conf_project']), "/{}/docs/source/conf.py".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--copyright--/{}/g".format(default_args['conf_copyright']), "/{}/docs/source/conf.py".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--author--/{}/g".format(default_args['conf_author']), "/{}/docs/source/conf.py".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--release--/{}/g".format(default_args['conf_release']), "/{}/docs/source/conf.py".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--version--/{}/g".format(default_args['conf_version']), "/{}/docs/source/conf.py".format(sname)])
    
    stitle = context['ti'].xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="solutiontitle")
    sdesc = context['ti'].xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="solutiondescription")
    brokerhost = context['ti'].xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="brokerhost")
    brokerport = context['ti'].xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="brokerport")
    cloudusername = context['ti'].xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="cloudusername")
    cloudpassword = context['ti'].xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="cloudpassword")
    ingestdatamethod = context['ti'].xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="ingestdatamethod")

    subprocess.call(["sed", "-i", "-e",  "s/--solutionname--/{}/g".format(sname), "/{}/docs/source/index.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--solutiontitle--/{}/g".format(stitle), "/{}/docs/source/index.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--solutiondescription--/{}/g".format(sdesc), "/{}/docs/source/index.rst".format(sname)])

    subprocess.call(["sed", "-i", "-e",  "s/--solutionname--/{}/g".format(sname), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--sname--/{}/g".format(sname), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--stitle--/{}/g".format(stitle), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--sdesc--/{}/g".format(sdesc), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--brokerhost--/{}/g".format(brokerhost), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--brokerport--/{}/g".format(brokerport), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--cloudusername--/{}/g".format(cloudusername), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--ingestdatamethod--/{}/g".format(ingestdatamethod), "/{}/docs/source/details.rst".format(sname)])

    
    companyname = context['ti'].xcom_pull(dag_id='tml_system_step_2_kafka_createtopic_dag',task_ids='setupkafkatopics',key="companyname")
    myname = context['ti'].xcom_pull(dag_id='tml_system_step_2_kafka_createtopic_dag',task_ids='setupkafkatopics',key="myname")
    myemail = context['ti'].xcom_pull(dag_id='tml_system_step_2_kafka_createtopic_dag',task_ids='setupkafkatopics',key="myemail")
    mylocation = context['ti'].xcom_pull(dag_id='tml_system_step_2_kafka_createtopic_dag',task_ids='setupkafkatopics',key="mylocation")
    replication = context['ti'].xcom_pull(dag_id='tml_system_step_2_kafka_createtopic_dag',task_ids='setupkafkatopics',key="replication")
    numpartitions = context['ti'].xcom_pull(dag_id='tml_system_step_2_kafka_createtopic_dag',task_ids='setupkafkatopics',key="numpartitions")
    enabletls = context['ti'].xcom_pull(dag_id='tml_system_step_2_kafka_createtopic_dag',task_ids='setupkafkatopics',key="enabletls")
    microserviceid = context['ti'].xcom_pull(dag_id='tml_system_step_2_kafka_createtopic_dag',task_ids='setupkafkatopics',key="microserviceid")
    raw_data_topic = context['ti'].xcom_pull(dag_id='tml_system_step_2_kafka_createtopic_dag',task_ids='setupkafkatopics',key="raw_data_topic")
    preprocess_data_topic = context['ti'].xcom_pull(dag_id='tml_system_step_2_kafka_createtopic_dag',task_ids='setupkafkatopics',key="preprocess_data_topic")
    ml_data_topic = context['ti'].xcom_pull(dag_id='tml_system_step_2_kafka_createtopic_dag',task_ids='setupkafkatopics',key="ml_data_topic")
    prediction_data_topic = context['ti'].xcom_pull(dag_id='tml_system_step_2_kafka_createtopic_dag',task_ids='setupkafkatopics',key="prediction_data_topic")

    subprocess.call(["sed", "-i", "-e",  "s/--companyname--/{}/g".format(companyname), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--myname--/{}/g".format(myname), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--myemail--/{}/g".format(myemail), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--mylocation--/{}/g".format(mylocation), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--replication--/{}/g".format(replication), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--numpartitions--/{}/g".format(numpartitions), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--enabletls--/{}/g".format(enabletls), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--microserviceid--/{}/g".format(microserviceid), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--raw_data_topic--/{}/g".format(raw_data_topic), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--preprocess_data_topic--/{}/g".format(preprocess_data_topic), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--ml_data_topic--/{}/g".format(ml_data_topic), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--prediction_data_topic--/{}/g".format(prediction_data_topic), "/{}/docs/source/details.rst".format(sname)])
    
    PRODUCETYPE = ""  
    TOPIC = ""
    PORT = ""
    IDENTIFIER = ""
    if ingestdatamethod == "localfile":
            PRODUCETYPE = context['ti'].xcom_pull(dag_id='tml_localfile_step_3_kafka_producetotopic_dag',task_ids='gettmlsystemsparams',key="PRODUCETYPE")
            TOPIC = context['ti'].xcom_pull(dag_id='tml_localfile_step_3_kafka_producetotopic_dag',task_ids='gettmlsystemsparams',key="TOPIC")
            PORT = context['ti'].xcom_pull(dag_id='tml_localfile_step_3_kafka_producetotopic_dag',task_ids='gettmlsystemsparams',key="PORT")
            IDENTIFIER = context['ti'].xcom_pull(dag_id='tml_localfile_step_3_kafka_producetotopic_dag',task_ids='gettmlsystemsparams',key="IDENTIFIER")   
    elif ingestdatamethod == "mqtt":
            PRODUCETYPE = context['ti'].xcom_pull(dag_id='tml_mqtt_step_3_kafka_producetotopic_dag',task_ids='mqttserverconnect',key="PRODUCETYPE")
            TOPIC = context['ti'].xcom_pull(dag_id='tml_mqtt_step_3_kafka_producetotopic_dag',task_ids='mqttserverconnect',key="TOPIC")
            PORT = context['ti'].xcom_pull(dag_id='tml_mqtt_step_3_kafka_producetotopic_dag',task_ids='mqttserverconnect',key="PORT")
            IDENTIFIER = context['ti'].xcom_pull(dag_id='tml_mqtt_step_3_kafka_producetotopic_dag',task_ids='mqttserverconnect',key="IDENTIFIER")
    elif ingestdatamethod == "rest":
            PRODUCETYPE = context['ti'].xcom_pull(dag_id='tml_read_RESTAPI_step_3_kafka_producetotopic_dag',task_ids='gettmlsystemsparams',key="PRODUCETYPE")
            TOPIC = context['ti'].xcom_pull(dag_id='tml_read_RESTAPI_step_3_kafka_producetotopic_dag',task_ids='gettmlsystemsparams',key="TOPIC")
            PORT = context['ti'].xcom_pull(dag_id='tml_read_RESTAPI_step_3_kafka_producetotopic_dag',task_ids='gettmlsystemsparams',key="PORT")
            IDENTIFIER = context['ti'].xcom_pull(dag_id='tml_read_RESTAPI_step_3_kafka_producetotopic_dag',task_ids='gettmlsystemsparams',key="IDENTIFIER")
    elif ingestdatamethod == "grpc":
            PRODUCETYPE = context['ti'].xcom_pull(dag_id='tml_read_gRPC_step_3_kafka_producetotopic_dag',task_ids='serve',key="PRODUCETYPE")
            TOPIC = context['ti'].xcom_pull(dag_id='tml_read_gRPC_step_3_kafka_producetotopic_dag',task_ids='serve',key="TOPIC")
            PORT = context['ti'].xcom_pull(dag_id='tml_read_gRPC_step_3_kafka_producetotopic_dag',task_ids='serve',key="PORT")
            IDENTIFIER = context['ti'].xcom_pull(dag_id='tml_read_gRPC_step_3_kafka_producetotopic_dag',task_ids='serve',key="IDENTIFIER")

    subprocess.call(["sed", "-i", "-e",  "s/--PRODUCETYPE--/{}/g".format(PRODUCETYPE), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--TOPIC--/{}/g".format(TOPIC), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--PORT--/{}/g".format(PORT), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--IDENTIFIER--/{}/g".format(IDENTIFIER), "/{}/docs/source/details.rst".format(sname)])
            
    raw_data_topic = context['ti'].xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="raw_data_topic")
    preprocess_data_topic = context['ti'].xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="preprocess_data_topic")    
    preprocessconditions = context['ti'].xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="preprocessconditions")
    delay = context['ti'].xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="delay")
    array = context['ti'].xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="array")
    saveasarray = context['ti'].xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="saveasarray")
    topicid = context['ti'].xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="topicid")
    rawdataoutput = context['ti'].xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="rawdataoutput")
    asynctimeout = context['ti'].xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="asynctimeout")
    timedelay = context['ti'].xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="timedelay")
    usemysql = context['ti'].xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="usemysql")
    preprocesstypes = context['ti'].xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="preprocesstypes")
    pathtotmlattrs = context['ti'].xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="pathtotmlattrs")
    identifier = context['ti'].xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="identifier")
    jsoncriteria = context['ti'].xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="jsoncriteria")

    subprocess.call(["sed", "-i", "-e",  "s/--raw_data_topic--/{}/g".format(raw_data_topic), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--preprocess_data_topic--/{}/g".format(preprocess_data_topic), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--preprocessconditions--/{}/g".format(preprocessconditions), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--delay--/{}/g".format(delay), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--array--/{}/g".format(array), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--saveasarray--/{}/g".format(saveasarray), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--topicid--/{}/g".format(topicid), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--rawdataoutput--/{}/g".format(rawdataoutput), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--asynctimeout--/{}/g".format(asynctimeout), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--timedelay--/{}/g".format(timedelay), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--preprocesstypes--/{}/g".format(preprocesstypes), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--pathtotmlattrs--/{}/g".format(pathtotmlattrs), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--identifier--/{}/g".format(identifier), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--jsoncriteria--/{}/g".format(jsoncriteria), "/{}/docs/source/details.rst".format(sname)])
    
    preprocess_data_topic = context['ti'].xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="preprocess_data_topic")
    ml_data_topic = context['ti'].xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="ml_data_topic")
    modelruns = context['ti'].xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="modelruns")
    offset = context['ti'].xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="offset")
    islogistic = context['ti'].xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="islogistic")
    networktimeout = context['ti'].xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="networktimeout")
    modelsearchtuner = context['ti'].xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="modelsearchtuner")
    dependentvariable = context['ti'].xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="dependentvariable")
    independentvariables = context['ti'].xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="independentvariables")
    rollbackoffsets = context['ti'].xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="rollbackoffsets")
    topicid = context['ti'].xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="topicid")
    consumefrom = context['ti'].xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="consumefrom")
    fullpathtotrainingdata = context['ti'].xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="fullpathtotrainingdata")
    transformtype = context['ti'].xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="transformtype")
    sendcoefto = context['ti'].xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="sendcoefto")
    coeftoprocess = context['ti'].xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="coeftoprocess")
    coefsubtopicnames = context['ti'].xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="coefsubtopicnames")

    subprocess.call(["sed", "-i", "-e",  "s/--preprocess_data_topic--/{}/g".format(preprocess_data_topic), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--ml_data_topic--/{}/g".format(ml_data_topic), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--modelruns--/{}/g".format(modelruns), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--offset--/{}/g".format(offset), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--islogistic--/{}/g".format(islogistic), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--networktimeout--/{}/g".format(networktimeout), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--modelsearchtuner--/{}/g".format(modelsearchtuner), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--dependentvariable--/{}/g".format(dependentvariable), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--independentvariables--/{}/g".format(independentvariables), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--rollbackoffsets--/{}/g".format(rollbackoffsets), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--topicid--/{}/g".format(topicid), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--consumefrom--/{}/g".format(consumefrom), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--fullpathtotrainingdata--/{}/g".format(fullpathtotrainingdata), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--transformtype--/{}/g".format(transformtype), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--sendcoefto--/{}/g".format(sendcoefto), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--coeftoprocess--/{}/g".format(coeftoprocess), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--coefsubtopicnames--/{}/g".format(coefsubtopicnames), "/{}/docs/source/details.rst".format(sname)])
    
    preprocess_data_topic = context['ti'].xcom_pull(dag_id='tml-system-step-6-kafka-predictions-dag',task_ids='performPredictions',key="preprocess_data_topic")
    ml_prediction_topic = context['ti'].xcom_pull(dag_id='tml-system-step-6-kafka-predictions-dag',task_ids='performPredictions',key="ml_prediction_topic")
    streamstojoin = context['ti'].xcom_pull(dag_id='tml-system-step-6-kafka-predictions-dag',task_ids='performPredictions',key="streamstojoin")
    inputdata = context['ti'].xcom_pull(dag_id='tml-system-step-6-kafka-predictions-dag',task_ids='performPredictions',key="inputdata")
    consumefrom = context['ti'].xcom_pull(dag_id='tml-system-step-6-kafka-predictions-dag',task_ids='performPredictions',key="consumefrom")
    offset = context['ti'].xcom_pull(dag_id='tml-system-step-6-kafka-predictions-dag',task_ids='performPredictions',key="offset")
    delay = context['ti'].xcom_pull(dag_id='tml-system-step-6-kafka-predictions-dag',task_ids='performPredictions',key="delay")
    usedeploy = context['ti'].xcom_pull(dag_id='tml-system-step-6-kafka-predictions-dag',task_ids='performPredictions',key="usedeploy")
    networktimeout = context['ti'].xcom_pull(dag_id='tml-system-step-6-kafka-predictions-dag',task_ids='performPredictions',key="networktimeout")
    maxrows = context['ti'].xcom_pull(dag_id='tml-system-step-6-kafka-predictions-dag',task_ids='performPredictions',key="maxrows")
    topicid = context['ti'].xcom_pull(dag_id='tml-system-step-6-kafka-predictions-dag',task_ids='performPredictions',key="topicid")
    pathtoalgos = context['ti'].xcom_pull(dag_id='tml-system-step-6-kafka-predictions-dag',task_ids='performPredictions',key="pathtoalgos")

    subprocess.call(["sed", "-i", "-e",  "s/--preprocess_data_topic--/{}/g".format(preprocess_data_topic), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--ml_prediction_topic--/{}/g".format(ml_prediction_topic), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--streamstojoin--/{}/g".format(streamstojoin), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--inputdata--/{}/g".format(inputdata), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--consumefrom--/{}/g".format(consumefrom), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--offset--/{}/g".format(offset), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--delay--/{}/g".format(delay), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--usedeploy--/{}/g".format(usedeploy), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--networktimeout--/{}/g".format(networktimeout), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--maxrows--/{}/g".format(maxrows), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--topicid--/{}/g".format(topicid), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--pathtoalgos--/{}/g".format(pathtoalgos), "/{}/docs/source/details.rst".format(sname)])

    
    vipervizport = context['ti'].xcom_pull(dag_id='tml-system-step-7-kafka-visualization-dag',task_ids='startstreamingengine',key="VIPERVIZPORT")
    topic = context['ti'].xcom_pull(dag_id='tml-system-step-7-kafka-visualization-dag',task_ids='startstreamingengine',key="topic")
    secure = context['ti'].xcom_pull(dag_id='tml-system-step-7-kafka-visualization-dag',task_ids='startstreamingengine',key="secure")
    offset = context['ti'].xcom_pull(dag_id='tml-system-step-7-kafka-visualization-dag',task_ids='startstreamingengine',key="offset")
    append = context['ti'].xcom_pull(dag_id='tml-system-step-7-kafka-visualization-dag',task_ids='startstreamingengine',key="append")
    chip = context['ti'].xcom_pull(dag_id='tml-system-step-7-kafka-visualization-dag',task_ids='startstreamingengine',key="chip")
    rollbackoffset = context['ti'].xcom_pull(dag_id='tml-system-step-7-kafka-visualization-dag',task_ids='startstreamingengine',key="rollbackoffset")

    if 'CHIP' in os.environ:
         chip = os.environ['CHIP']
    else:
         chip=""
    if chip.lower() == "arm64":  
        containername = os.environ['DOCKERUSERNAME']  + "/{}-{}".format(sname,chip)          
    else:    
        containername = os.environ['DOCKERUSERNAME']  + "/{}".format(sname)
    
    subprocess.call(["sed", "-i", "-e",  "s/--vipervizport--/{}/g".format(vipervizport), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--topic--/{}/g".format(topic), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--secure--/{}/g".format(secure), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--offset--/{}/g".format(offset), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--append--/{}/g".format(append), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--chip--/{}/g".format(chip), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--rollbackoffset--/{}/g".format(rollbackoffset), "/{}/docs/source/details.rst".format(sname)])

    cname = context['ti'].xcom_pull(dag_id='tml_system_step_8_deploy_solution_to_docker_dag',task_ids='dockerit',key="containername")
    key="DOCKERRUN-{}".format(sname)    
    dockerrun=os.environ[key]
    dockerrun=dockerrun.replace(",","\n\n")
    subprocess.call(["sed", "-i", "-e",  "s/--dockercontainer--/{}/g".format(containername), "/{}/docs/source/operating.rst".format(sname)])

    subprocess.call(["sed", "-i", "-e",  "s/--dockerrun--/{}/g".format(dockerrun), "/{}/docs/source/operating.rst".format(sname)])
    
    key="VISUALRUN-{}".format(sname)    
    visualrun=os.environ[key]
    visualrun=visualrun.replace(",","\n\n")
    subprocess.call(["sed", "-i", "-e",  "s/--visualizationurl--/{}/g".format(visualrun), "/{}/docs/source/operating.rst".format(sname)])

    key="AIRFLOWRUN-{}".format(sname)    
    airflowrun=os.environ[key]
    airflowrun=visualrun.replace(",","\n\n")
    subprocess.call(["sed", "-i", "-e",  "s/--airflowurl--/{}/g".format(visualrun), "/{}/docs/source/operating.rst".format(sname)])
    
    repo = tsslogging.getrepo() 
    gitrepo = "/{}/tml-airflow/dags/tml-solutions/{}".format(repo,sname)
    
    subprocess.call(["sed", "-i", "-e",  "s/--gitrepo--/{}/g".format(gitrepo), "/{}/docs/source/operating.rst".format(sname)])
    readthedocs = "https://{}.readthedocs.io".format(sname)
    subprocess.call(["sed", "-i", "-e",  "s/--readthedocs--/{}/g".format(readthedocs), "/{}/docs/source/operating.rst".format(sname)])
    
    key = "trigger-{}".format(sname)
    triggername=os.environ[key]
    subprocess.call(["sed", "-i", "-e",  "s/--triggername--/{}/g".format(triggername), "/{}/docs/source/operating.rst".format(sname)])
    
    # Kick off shell script 
    tsslogging.git_push("/{}".format(sname),"{}-readthedocs".format(sname),sname)
    
    URL = 'https://readthedocs.org/api/v3/projects/'
    TOKEN = os.environ['READTHEDOCS']
    HEADERS = {'Authorization': f'token {TOKEN}'}
    data={
        "name": "{}".format(sname),
        "repository": {
            "url": "https://github.com/{}/{}".format(os.environ['GITUSERNAME'],sname),
            "type": "git"
        },
        "homepage": "http://template.readthedocs.io/",
        "programming_language": "py",
        "language": "es",
        "privacy_level": "public",
        "external_builds_privacy_level": "public",
        "tags": [
            "automation",
            "sphinx"
        ]
    }
    response = requests.post(
        URL,
        json=data,
        headers=HEADERS,
    )
    print(response.json())
    tsslogging.tsslogit(response.json())
    os.environ['tssdoc']="1"
