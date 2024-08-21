from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime
from airflow.decorators import dag, task
import os 
import sys
import requests
import json

sys.dont_write_bytecode = True

######################################################USER CHOSEN PARAMETERS ###########################################################
default_args = {    
 'start_date': datetime (2024, 6, 29),   # <<< *** Change as needed   
 'retries': 1,   # <<< *** Change as needed   
 'conf_project' : 'Transactional Machine Learning (TML)',
 'conf_copyright' : '2024, Otics Advanced Analytics, Incorporated - For Support email support@otics.ca',
 'conf_author' : 'Sebastian Maurice',
 'conf_release' : '0.1',
 'conf_version' : '0.1.0'
}

############################################################### DO NOT MODIFY BELOW ####################################################
# Instantiate your DAG
@dag(dag_id="tml_system_step_10_documentation_dag", default_args=default_args, tags=["tml_system_step_10_documentation_dag"], schedule=None,  catchup=False)
def startdocumentation():
    # Define tasks

  @task(task_id="getparams")
  def generatedoc():    
    
    sname = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="solutionname")
    stitle = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="solutiontitle")
    sdesc = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="solutiondescription")
    brokerhost = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="brokerhost")
    brokerport = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="brokerport")
    cloudusername = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="cloudusername")
    cloudpassword = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="cloudpassword")
    ingestdatamethod = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="ingestdatamethod")
    
    companyname = ti.xcom_pull(dag_id='tml_system_step_2_kafka_createtopic_dag',task_ids='setupkafkatopics',key="companyname")
    myname = ti.xcom_pull(dag_id='tml_system_step_2_kafka_createtopic_dag',task_ids='setupkafkatopics',key="myname")
    myemail = ti.xcom_pull(dag_id='tml_system_step_2_kafka_createtopic_dag',task_ids='setupkafkatopics',key="myemail")
    mylocation = ti.xcom_pull(dag_id='tml_system_step_2_kafka_createtopic_dag',task_ids='setupkafkatopics',key="mylocation")
    replication = ti.xcom_pull(dag_id='tml_system_step_2_kafka_createtopic_dag',task_ids='setupkafkatopics',key="replication")
    numpartitions = ti.xcom_pull(dag_id='tml_system_step_2_kafka_createtopic_dag',task_ids='setupkafkatopics',key="numpartitions")
    enabletls = ti.xcom_pull(dag_id='tml_system_step_2_kafka_createtopic_dag',task_ids='setupkafkatopics',key="enabletls")
    microserviceid = ti.xcom_pull(dag_id='tml_system_step_2_kafka_createtopic_dag',task_ids='setupkafkatopics',key="microserviceid")
    raw_data_topic = ti.xcom_pull(dag_id='tml_system_step_2_kafka_createtopic_dag',task_ids='setupkafkatopics',key="raw_data_topic")
    preprocess_data_topic = ti.xcom_pull(dag_id='tml_system_step_2_kafka_createtopic_dag',task_ids='setupkafkatopics',key="preprocess_data_topic")
    ml_data_topic = ti.xcom_pull(dag_id='tml_system_step_2_kafka_createtopic_dag',task_ids='setupkafkatopics',key="ml_data_topic")
    prediction_data_topic = ti.xcom_pull(dag_id='tml_system_step_2_kafka_createtopic_dag',task_ids='setupkafkatopics',key="prediction_data_topic")

    PRODUCETYPE = ""  
    TOPIC = ""
    PORT = ""
    IDENTIFIER = ""
    if ingestdatamethod == "localfile":
            PRODUCETYPE = ti.xcom_pull(dag_id='tml_localfile_step_3_kafka_producetotopic_dag',task_ids='gettmlsystemsparams',key="PRODUCETYPE")
            TOPIC = ti.xcom_pull(dag_id='tml_localfile_step_3_kafka_producetotopic_dag',task_ids='gettmlsystemsparams',key="TOPIC")
            PORT = ti.xcom_pull(dag_id='tml_localfile_step_3_kafka_producetotopic_dag',task_ids='gettmlsystemsparams',key="PORT")
            IDENTIFIER = ti.xcom_pull(dag_id='tml_localfile_step_3_kafka_producetotopic_dag',task_ids='gettmlsystemsparams',key="IDENTIFIER")   
    elif ingestdatamethod == "mqtt":
            PRODUCETYPE = ti.xcom_pull(dag_id='tml_mqtt_step_3_kafka_producetotopic_dag',task_ids='mqttserverconnect',key="PRODUCETYPE")
            TOPIC = ti.xcom_pull(dag_id='tml_mqtt_step_3_kafka_producetotopic_dag',task_ids='mqttserverconnect',key="TOPIC")
            PORT = ti.xcom_pull(dag_id='tml_mqtt_step_3_kafka_producetotopic_dag',task_ids='mqttserverconnect',key="PORT")
            IDENTIFIER = ti.xcom_pull(dag_id='tml_mqtt_step_3_kafka_producetotopic_dag',task_ids='mqttserverconnect',key="IDENTIFIER")
    elif ingestdatamethod == "rest":
            PRODUCETYPE = ti.xcom_pull(dag_id='tml_read_RESTAPI_step_3_kafka_producetotopic_dag',task_ids='gettmlsystemsparams',key="PRODUCETYPE")
            TOPIC = ti.xcom_pull(dag_id='tml_read_RESTAPI_step_3_kafka_producetotopic_dag',task_ids='gettmlsystemsparams',key="TOPIC")
            PORT = ti.xcom_pull(dag_id='tml_read_RESTAPI_step_3_kafka_producetotopic_dag',task_ids='gettmlsystemsparams',key="PORT")
            IDENTIFIER = ti.xcom_pull(dag_id='tml_read_RESTAPI_step_3_kafka_producetotopic_dag',task_ids='gettmlsystemsparams',key="IDENTIFIER")
    elif ingestdatamethod == "grpc":
            PRODUCETYPE = ti.xcom_pull(dag_id='tml_read_gRPC_step_3_kafka_producetotopic_dag',task_ids='serve',key="PRODUCETYPE")
            TOPIC = ti.xcom_pull(dag_id='tml_read_gRPC_step_3_kafka_producetotopic_dag',task_ids='serve',key="TOPIC")
            PORT = ti.xcom_pull(dag_id='tml_read_gRPC_step_3_kafka_producetotopic_dag',task_ids='serve',key="PORT")
            IDENTIFIER = ti.xcom_pull(dag_id='tml_read_gRPC_step_3_kafka_producetotopic_dag',task_ids='serve',key="IDENTIFIER")
    
    raw_data_topic = ti.xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="raw_data_topic")
    preprocess_data_topic = ti.xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="preprocess_data_topic")    
    preprocessconditions = ti.xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="preprocessconditions")
    delay = ti.xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="delay")
    array = ti.xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="array")
    saveasarray = ti.xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="saveasarray")
    topicid = ti.xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="topicid")
    rawdataoutput = ti.xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="rawdataoutput")
    asynctimeout = ti.xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="asynctimeout")
    timedelay = ti.xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="timedelay")
    usemysql = ti.xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="usemysql")
    preprocesstypes = ti.xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="preprocesstypes")
    pathtotmlattrs = ti.xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="pathtotmlattrs")
    identifier = ti.xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="identifier")
    jsoncriteria = ti.xcom_pull(dag_id='tml-system-step-4-kafka-preprocess-dag',task_ids='processtransactiondata',key="jsoncriteria")
    
    preprocess_data_topic = ti.xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="preprocess_data_topic")
    ml_data_topic = ti.xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="ml_data_topic")
    modelruns = ti.xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="modelruns")
    offset = ti.xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="offset")
    islogistic = ti.xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="islogistic")
    networktimeout = ti.xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="networktimeout")
    modelsearchtuner = ti.xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="modelsearchtuner")
    dependentvariable = ti.xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="dependentvariable")
    independentvariables = ti.xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="independentvariables")
    rollbackoffsets = ti.xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="rollbackoffsets")
    topicid = ti.xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="topicid")
    consumefrom = ti.xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="consumefrom")
    fullpathtotrainingdata = ti.xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="fullpathtotrainingdata")
    transformtype = ti.xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="transformtype")
    sendcoefto = ti.xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="sendcoefto")
    coeftoprocess = ti.xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="coeftoprocess")
    coefsubtopicnames = ti.xcom_pull(dag_id='tml-system-step-5-kafka-machine-learning-dag',task_ids='performSupervisedMachineLearning',key="coefsubtopicnames")

    preprocess_data_topic = ti.xcom_pull(dag_id='tml-system-step-6-kafka-predictions-dag',task_ids='performPredictions',key="preprocess_data_topic")
    ml_prediction_topic = ti.xcom_pull(dag_id='tml-system-step-6-kafka-predictions-dag',task_ids='performPredictions',key="ml_prediction_topic")
    streamstojoin = ti.xcom_pull(dag_id='tml-system-step-6-kafka-predictions-dag',task_ids='performPredictions',key="streamstojoin")
    inputdata = ti.xcom_pull(dag_id='tml-system-step-6-kafka-predictions-dag',task_ids='performPredictions',key="inputdata")
    consumefrom = ti.xcom_pull(dag_id='tml-system-step-6-kafka-predictions-dag',task_ids='performPredictions',key="consumefrom")
    offset = ti.xcom_pull(dag_id='tml-system-step-6-kafka-predictions-dag',task_ids='performPredictions',key="offset")
    delay = ti.xcom_pull(dag_id='tml-system-step-6-kafka-predictions-dag',task_ids='performPredictions',key="delay")
    usedeploy = ti.xcom_pull(dag_id='tml-system-step-6-kafka-predictions-dag',task_ids='performPredictions',key="usedeploy")
    networktimeout = ti.xcom_pull(dag_id='tml-system-step-6-kafka-predictions-dag',task_ids='performPredictions',key="networktimeout")
    maxrows = ti.xcom_pull(dag_id='tml-system-step-6-kafka-predictions-dag',task_ids='performPredictions',key="maxrows")
    topicid = ti.xcom_pull(dag_id='tml-system-step-6-kafka-predictions-dag',task_ids='performPredictions',key="topicid")
    pathtoalgos = ti.xcom_pull(dag_id='tml-system-step-6-kafka-predictions-dag',task_ids='performPredictions',key="pathtoalgos")
    
    
    vipervizport = ti.xcom_pull(dag_id='tml-system-step-7-kafka-visualization-dag',task_ids='startstreamingengine',key="VIPERVIZPORT")
    topic = ti.xcom_pull(dag_id='tml-system-step-7-kafka-visualization-dag',task_ids='startstreamingengine',key="topic")
    secure = ti.xcom_pull(dag_id='tml-system-step-7-kafka-visualization-dag',task_ids='startstreamingengine',key="secure")
    offset = ti.xcom_pull(dag_id='tml-system-step-7-kafka-visualization-dag',task_ids='startstreamingengine',key="offset")
    append = ti.xcom_pull(dag_id='tml-system-step-7-kafka-visualization-dag',task_ids='startstreamingengine',key="append")
    chip = ti.xcom_pull(dag_id='tml-system-step-7-kafka-visualization-dag',task_ids='startstreamingengine',key="chip")
    rollbackoffset = ti.xcom_pull(dag_id='tml-system-step-7-kafka-visualization-dag',task_ids='startstreamingengine',key="rollbackoffset")

    # Kick off shell script 
    
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
    
dag = startdocumentation()
