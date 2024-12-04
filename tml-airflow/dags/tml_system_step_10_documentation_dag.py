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
import time
sys.dont_write_bytecode = True

######################################################USER CHOSEN PARAMETERS ###########################################################
default_args = {    
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
    def empty():
        pass
dag = startdocumentation()

def triggerbuild(sname):

        URL = "https://readthedocs.org/api/v3/projects/{}/versions/latest/builds/".format(sname)
        TOKEN = os.environ['READTHEDOCS']
        HEADERS = {'Authorization': f'token {TOKEN}'}
        response = requests.post(URL, headers=HEADERS)
        print(response.json())

def updatebranch(sname,branch):
    
        URL = "https://readthedocs.org/api/v3/projects/{}/".format(sname)
        TOKEN = os.environ['READTHEDOCS']
        HEADERS = {'Authorization': f'token {TOKEN}'}
        data={
            "name": "{}".format(sname),
            "repository": {
                "url": "https://github.com/{}/{}".format(os.environ['GITUSERNAME'],sname),
                "type": "git"
            },
            "default_branch": "{}".format(branch),
            "homepage": "http://template.readthedocs.io/",
            "programming_language": "py",
            "language": "en",
            "privacy_level": "public",
            "external_builds_privacy_level": "public",
            "tags": [
                "automation",
                "sphinx"
            ]
        }
        response = requests.patch(
            URL,
            json=data,
            headers=HEADERS,
        )
    
    
def doparse(fname,farr):
      data = ''
      try:  
       with open(fname, 'r', encoding='utf-8') as file: 
        data = file.readlines() 
        r=0
        for d in data:        
            for f in farr:
                fs = f.split(";")
                if fs[0] in d:
                    data[r] = d.replace(fs[0],fs[1])
            r += 1  
       with open(fname, 'w', encoding='utf-8') as file: 
        file.writelines(data)
      except Exception as e:
         pass
    
def generatedoc(**context):    
    istss1=1
    if 'TSS' in os.environ:
      if os.environ['TSS'] == "1":
        istss1=1
      else:
        istss1=0
       
    if 'tssdoc' in os.environ:
        if os.environ['tssdoc']=="1":
            return
    tsslogging.locallogs("INFO", "STEP 10: Started to build the documentation")
    
    sd = context['dag'].dag_id
    sname=context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_solutionname".format(sd))

    kube=0
    if "KUBE" in os.environ:
          if os.environ["KUBE"] == "1":
             kube=1
           
    producinghost = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERHOSTPRODCE".format(sname))
    producingport = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERPORTPRODUCE".format(sname))
    preprocesshost = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERHOSTPREPROCESS".format(sname))
    preprocessport = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERPORTPREPROCESS".format(sname))
    preprocesshost2 = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERHOSTPREPROCESS2".format(sname))
    preprocessport2 = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERPORTPREPROCESS2".format(sname))

    mlhost = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERHOSTML".format(sname))
    mlport = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERPORTML".format(sname))
    predictionhost = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERHOSTPREDICT".format(sname))
    predictionport = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERHOSTPREDICT".format(sname))
    dashboardhtml = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_dashboardhtml".format(sname))
    vipervizport = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERVIZPORT".format(sname))
    solutionvipervizport = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_SOLUTIONVIPERVIZPORT".format(sname))
    airflowport = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_AIRFLOWPORT".format(sname))
    mqttusername = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_MQTTUSERNAME".format(sname))
    kafkacloudusername = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_KAFKACLOUDUSERNAME".format(sname))
    
    externalport = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_EXTERNALPORT".format(sname))
    solutionexternalport = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_SOLUTIONEXTERNALPORT".format(sname))
    
    solutionairflowport = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_SOLUTIONAIRFLOWPORT".format(sname))
    
    hpdehost = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_HPDEHOST".format(sname))
    hpdeport = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_HPDEPORT".format(sname))

    hpdepredicthost = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_HPDEHOSTPREDICT".format(sname))
    hpdepredictport = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_HPDEPORTPREDICT".format(sname))
    
    subprocess.call(["sed", "-i", "-e",  "s/--project--/{}/g".format(default_args['conf_project']), "/{}/docs/source/conf.py".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--copyright--/{}/g".format(default_args['conf_copyright']), "/{}/docs/source/conf.py".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--author--/{}/g".format(default_args['conf_author']), "/{}/docs/source/conf.py".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--release--/{}/g".format(default_args['conf_release']), "/{}/docs/source/conf.py".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--version--/{}/g".format(default_args['conf_version']), "/{}/docs/source/conf.py".format(sname)])
    
    stitle = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_solutiontitle".format(sname))
    sdesc = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_solutiondescription".format(sname))
    brokerhost = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_brokerhost".format(sname))
    brokerport = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_brokerport".format(sname))
    cloudusername = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_cloudusername".format(sname))
    cloudpassword = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_cloudpassword".format(sname))

    subprocess.call(["sed", "-i", "-e",  "s/--solutionname--/{}/g".format(sname), "/{}/docs/source/index.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--solutiontitle--/{}/g".format(stitle), "/{}/docs/source/index.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--solutiondescription--/{}/g".format(sdesc), "/{}/docs/source/index.rst".format(sname)])

    subprocess.call(["sed", "-i", "-e",  "s/--solutionname--/{}/g".format(sname), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--sname--/{}/g".format(sname), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--stitle--/{}/g".format(stitle), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--sdesc--/{}/g".format(sdesc), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--brokerhost--/{}/g".format(brokerhost), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--brokerport--/{}/g".format(brokerport[1:]), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--cloudusername--/{}/g".format(cloudusername), "/{}/docs/source/details.rst".format(sname)])

    subprocess.call(["sed", "-i", "-e",  "s/--solutiontitle--/{}/g".format(stitle), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--solutiondescription--/{}/g".format(sdesc), "/{}/docs/source/details.rst".format(sname)])

    
    companyname = context['ti'].xcom_pull(task_ids='step_2_solution_task_createtopic',key="{}_companyname".format(sname))
    myname = context['ti'].xcom_pull(task_ids='step_2_solution_task_createtopic',key="{}_myname".format(sname))
    myemail = context['ti'].xcom_pull(task_ids='step_2_solution_task_createtopic',key="{}_myemail".format(sname))
    mylocation = context['ti'].xcom_pull(task_ids='step_2_solution_task_createtopic',key="{}_mylocation".format(sname))
    replication = context['ti'].xcom_pull(task_ids='step_2_solution_task_createtopic',key="{}_replication".format(sname))
    numpartitions = context['ti'].xcom_pull(task_ids='step_2_solution_task_createtopic',key="{}_numpartitions".format(sname))
    enabletls = context['ti'].xcom_pull(task_ids='step_2_solution_task_createtopic',key="{}_enabletls".format(sname))
    microserviceid = context['ti'].xcom_pull(task_ids='step_2_solution_task_createtopic',key="{}_microserviceid".format(sname))
    raw_data_topic = context['ti'].xcom_pull(task_ids='step_2_solution_task_createtopic',key="{}_raw_data_topic".format(sname))
    preprocess_data_topic = context['ti'].xcom_pull(task_ids='step_2_solution_task_createtopic',key="{}_preprocess_data_topic".format(sname))
    ml_data_topic = context['ti'].xcom_pull(task_ids='step_2_solution_task_createtopic',key="{}_ml_data_topic".format(sname))
    prediction_data_topic = context['ti'].xcom_pull(task_ids='step_2_solution_task_createtopic',key="{}_prediction_data_topic".format(sname))

    subprocess.call(["sed", "-i", "-e",  "s/--companyname--/{}/g".format(companyname), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--myname--/{}/g".format(myname), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--myemail--/{}/g".format(myemail), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--mylocation--/{}/g".format(mylocation), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--replication--/{}/g".format(replication[1:]), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--numpartitions--/{}/g".format(numpartitions[1:]), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--enabletls--/{}/g".format(enabletls[1:]), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--microserviceid--/{}/g".format(microserviceid), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--raw_data_topic--/{}/g".format(raw_data_topic), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--preprocess_data_topic--/{}/g".format(preprocess_data_topic), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--ml_data_topic--/{}/g".format(ml_data_topic), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--prediction_data_topic--/{}/g".format(prediction_data_topic), "/{}/docs/source/details.rst".format(sname)])
    
    PRODUCETYPE = ""  
    TOPIC = ""
    PORT = ""
    IDENTIFIER = ""
    HTTPADDR = ""
    FROMHOST = ""
    TOHOST = ""    
    CLIENTPORT = ""
    
    PRODUCETYPE = context['ti'].xcom_pull(task_ids='step_3_solution_task_producetotopic',key="{}_PRODUCETYPE".format(sname))
    TOPIC = context['ti'].xcom_pull(task_ids='step_3_solution_task_producetotopic',key="{}_TOPIC".format(sname))
    PORT = context['ti'].xcom_pull(task_ids='step_3_solution_task_producetotopic',key="{}_PORT".format(sname))
    IDENTIFIER = context['ti'].xcom_pull(task_ids='step_3_solution_task_producetotopic',key="{}_IDENTIFIER".format(sname))
    HTTPADDR = context['ti'].xcom_pull(task_ids='step_3_solution_task_producetotopic',key="{}_HTTPADDR".format(sname))  
    FROMHOST = context['ti'].xcom_pull(task_ids='step_3_solution_task_producetotopic',key="{}_FROMHOST".format(sname))  
    TOHOST = context['ti'].xcom_pull(task_ids='step_3_solution_task_producetotopic',key="{}_TOHOST".format(sname))  
    
    CLIENTPORT = context['ti'].xcom_pull(task_ids='step_3_solution_task_producetotopic',key="{}_CLIENTPORT".format(sname))              
    TSSCLIENTPORT = context['ti'].xcom_pull(task_ids='step_3_solution_task_producetotopic',key="{}_TSSCLIENTPORT".format(sname))              
    TMLCLIENTPORT = context['ti'].xcom_pull(task_ids='step_3_solution_task_producetotopic',key="{}_TMLCLIENTPORT".format(sname))              

    subprocess.call(["sed", "-i", "-e",  "s/--PRODUCETYPE--/{}/g".format(PRODUCETYPE), "/{}/docs/source/details.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--TOPIC--/{}/g".format(TOPIC), "/{}/docs/source/details.rst".format(sname)])
    doparse("/{}/docs/source/details.rst".format(sname), ["--PORT--;{}".format(PORT[1:])])
    doparse("/{}/docs/source/details.rst".format(sname), ["--HTTPADDR--;{}".format(HTTPADDR)])
    doparse("/{}/docs/source/details.rst".format(sname), ["--FROMHOST--;{}".format(FROMHOST)])
    doparse("/{}/docs/source/details.rst".format(sname), ["--TOHOST--;{}".format(TOHOST)])

    doparse("/{}/docs/source/details.rst".format(sname), ["--datetime--;{}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))])
    doparse("/{}/docs/source/index.rst".format(sname), ["--datetime--;{}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))])
    doparse("/{}/docs/source/operating.rst".format(sname), ["--datetime--;{}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))])
    doparse("/{}/docs/source/logs.rst".format(sname), ["--datetime--;{}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))])
    doparse("/{}/docs/source/kube.rst".format(sname), ["--datetime--;{}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))])

    if len(CLIENTPORT) > 1:
      doparse("/{}/docs/source/details.rst".format(sname), ["--CLIENTPORT--;{}".format(CLIENTPORT[1:])])
      doparse("/{}/docs/source/details.rst".format(sname), ["--TSSCLIENTPORT--;{}".format(TSSCLIENTPORT[1:])])
      doparse("/{}/docs/source/details.rst".format(sname), ["--TMLCLIENTPORT--;{}".format(TMLCLIENTPORT[1:])])
    else:
      doparse("/{}/docs/source/details.rst".format(sname), ["--CLIENTPORT--;Not Applicable"])
      doparse("/{}/docs/source/details.rst".format(sname), ["--TSSCLIENTPORT--;Not Applicable"])
      doparse("/{}/docs/source/details.rst".format(sname), ["--TMLCLIENTPORT--;Not Applicable"])
    
    doparse("/{}/docs/source/details.rst".format(sname), ["--IDENTIFIER--;{}".format(IDENTIFIER)])
    
    subprocess.call(["sed", "-i", "-e",  "s/--ingestdatamethod--/{}/g".format(PRODUCETYPE), "/{}/docs/source/details.rst".format(sname)])
            
    raw_data_topic = context['ti'].xcom_pull(task_ids='step_4_solution_task_preprocess',key="{}_raw_data_topic".format(sname))
    preprocess_data_topic = context['ti'].xcom_pull(task_ids='step_4_solution_task_preprocess',key="{}_preprocess_data_topic".format(sname))    
    preprocessconditions = context['ti'].xcom_pull(task_ids='step_4_solution_task_preprocess',key="{}_preprocessconditions".format(sname))
    delay = context['ti'].xcom_pull(task_ids='step_4_solution_task_preprocess',key="{}_delay".format(sname))
    array = context['ti'].xcom_pull(task_ids='step_4_solution_task_preprocess',key="{}_array".format(sname))
    saveasarray = context['ti'].xcom_pull(task_ids='step_4_solution_task_preprocess',key="{}_saveasarray".format(sname))
    topicid = context['ti'].xcom_pull(task_ids='step_4_solution_task_preprocess',key="{}_topicid".format(sname))
    rawdataoutput = context['ti'].xcom_pull(task_ids='step_4_solution_task_preprocess',key="{}_rawdataoutput".format(sname))
    asynctimeout = context['ti'].xcom_pull(task_ids='step_4_solution_task_preprocess',key="{}_asynctimeout".format(sname))
    timedelay = context['ti'].xcom_pull(task_ids='step_4_solution_task_preprocess',key="{}_timedelay".format(sname))
    usemysql = context['ti'].xcom_pull(task_ids='step_4_solution_task_preprocess',key="{}_usemysql".format(sname))
    preprocesstypes = context['ti'].xcom_pull(task_ids='step_4_solution_task_preprocess',key="{}_preprocesstypes".format(sname))
    pathtotmlattrs = context['ti'].xcom_pull(task_ids='step_4_solution_task_preprocess',key="{}_pathtotmlattrs".format(sname))
    identifier = context['ti'].xcom_pull(task_ids='step_4_solution_task_preprocess',key="{}_identifier".format(sname))
    jsoncriteria = context['ti'].xcom_pull(task_ids='step_4_solution_task_preprocess',key="{}_jsoncriteria".format(sname))

    if preprocess_data_topic:
        subprocess.call(["sed", "-i", "-e",  "s/--raw_data_topic--/{}/g".format(raw_data_topic), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--preprocess_data_topic--/{}/g".format(preprocess_data_topic), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--preprocessconditions--/{}/g".format(preprocessconditions), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--delay--/{}/g".format(delay[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--array--/{}/g".format(array[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--saveasarray--/{}/g".format(saveasarray[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--topicid--/{}/g".format(topicid[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--rawdataoutput--/{}/g".format(rawdataoutput[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--asynctimeout--/{}/g".format(asynctimeout[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--timedelay--/{}/g".format(timedelay[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--preprocesstypes--/{}/g".format(preprocesstypes), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--pathtotmlattrs--/{}/g".format(pathtotmlattrs), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--identifier--/{}/g".format(identifier), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--jsoncriteria--/{}/g".format(jsoncriteria), "/{}/docs/source/details.rst".format(sname)])

    raw_data_topic = context['ti'].xcom_pull(task_ids='step_4b_solution_task_preprocess',key="{}_raw_data_topic".format(sname))
    preprocess_data_topic = context['ti'].xcom_pull(task_ids='step_4b_solution_task_preprocess',key="{}_preprocess_data_topic".format(sname))    
    preprocessconditions = context['ti'].xcom_pull(task_ids='step_4b_solution_task_preprocess',key="{}_preprocessconditions".format(sname))
    delay = context['ti'].xcom_pull(task_ids='step_4b_solution_task_preprocess',key="{}_delay".format(sname))
    array = context['ti'].xcom_pull(task_ids='step_4b_solution_task_preprocess',key="{}_array".format(sname))
    saveasarray = context['ti'].xcom_pull(task_ids='step_4b_solution_task_preprocess',key="{}_saveasarray".format(sname))
    topicid = context['ti'].xcom_pull(task_ids='step_4b_solution_task_preprocess',key="{}_topicid".format(sname))
    rawdataoutput = context['ti'].xcom_pull(task_ids='step_4b_solution_task_preprocess',key="{}_rawdataoutput".format(sname))
    asynctimeout = context['ti'].xcom_pull(task_ids='step_4b_solution_task_preprocess',key="{}_asynctimeout".format(sname))
    timedelay = context['ti'].xcom_pull(task_ids='step_4b_solution_task_preprocess',key="{}_timedelay".format(sname))
    usemysql = context['ti'].xcom_pull(task_ids='step_4b_solution_task_preprocess',key="{}_usemysql".format(sname))
    preprocesstypes = context['ti'].xcom_pull(task_ids='step_4b_solution_task_preprocess',key="{}_preprocesstypes".format(sname))
    pathtotmlattrs = context['ti'].xcom_pull(task_ids='step_4b_solution_task_preprocess',key="{}_pathtotmlattrs".format(sname))
    identifier = context['ti'].xcom_pull(task_ids='step_4b_solution_task_preprocess',key="{}_identifier".format(sname))
    jsoncriteria = context['ti'].xcom_pull(task_ids='step_4b_solution_task_preprocess',key="{}_jsoncriteria".format(sname))

    if preprocess_data_topic:
        subprocess.call(["sed", "-i", "-e",  "s/--raw_data_topic2--/{}/g".format(raw_data_topic), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--preprocess_data_topic2--/{}/g".format(preprocess_data_topic), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--preprocessconditions2--/{}/g".format(preprocessconditions), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--delay2--/{}/g".format(delay[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--array2--/{}/g".format(array[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--saveasarray2--/{}/g".format(saveasarray[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--topicid2--/{}/g".format(topicid[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--rawdataoutput2--/{}/g".format(rawdataoutput[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--asynctimeout2--/{}/g".format(asynctimeout[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--timedelay2--/{}/g".format(timedelay[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--preprocesstypes2--/{}/g".format(preprocesstypes), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--pathtotmlattrs2--/{}/g".format(pathtotmlattrs), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--identifier2--/{}/g".format(identifier), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--jsoncriteria2--/{}/g".format(jsoncriteria), "/{}/docs/source/details.rst".format(sname)])
        
    preprocess_data_topic = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_preprocess_data_topic".format(sname))
    ml_data_topic = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_ml_data_topic".format(sname))
    modelruns = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_modelruns".format(sname))
    offset = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_offset".format(sname))
    islogistic = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_islogistic".format(sname))
    networktimeout = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_networktimeout".format(sname))
    modelsearchtuner = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_modelsearchtuner".format(sname))
    dependentvariable = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_dependentvariable".format(sname))
    independentvariables = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_independentvariables".format(sname))
    rollbackoffsets = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_rollbackoffsets".format(sname))
    topicid = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_topicid".format(sname))
    consumefrom = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_consumefrom".format(sname))
    fullpathtotrainingdata = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_fullpathtotrainingdata".format(sname))
    transformtype = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_transformtype".format(sname))
    sendcoefto = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_sendcoefto".format(sname))
    coeftoprocess = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_coeftoprocess".format(sname))
    coefsubtopicnames = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_coefsubtopicnames".format(sname))
    processlogic = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_processlogic".format(sname))

    if modelruns: 
        subprocess.call(["sed", "-i", "-e",  "s/--preprocess_data_topic--/{}/g".format(preprocess_data_topic), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--ml_data_topic--/{}/g".format(ml_data_topic), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--modelruns--/{}/g".format(modelruns[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--offset--/{}/g".format(offset[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--islogistic--/{}/g".format(islogistic[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--networktimeout--/{}/g".format(networktimeout[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--modelsearchtuner--/{}/g".format(modelsearchtuner[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--dependentvariable--/{}/g".format(dependentvariable), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--independentvariables--/{}/g".format(independentvariables), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--rollbackoffsets--/{}/g".format(rollbackoffsets[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--topicid--/{}/g".format(topicid[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--consumefrom--/{}/g".format(consumefrom), "/{}/docs/source/details.rst".format(sname)])
        doparse("/{}/docs/source/details.rst".format(sname), ["--fullpathtotrainingdata--;{}".format(fullpathtotrainingdata)])
        doparse("/{}/docs/source/details.rst".format(sname), ["--processlogic--;{}".format(processlogic)])
        
        subprocess.call(["sed", "-i", "-e",  "s/--transformtype--/{}/g".format(transformtype), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--sendcoefto--/{}/g".format(sendcoefto), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--coeftoprocess--/{}/g".format(coeftoprocess), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--coefsubtopicnames--/{}/g".format(coefsubtopicnames), "/{}/docs/source/details.rst".format(sname)])
    
    preprocess_data_topic = context['ti'].xcom_pull(task_ids='step_6_solution_task_prediction',key="{}_preprocess_data_topic".format(sname))
    ml_prediction_topic = context['ti'].xcom_pull(task_ids='step_6_solution_task_prediction',key="{}_ml_prediction_topic".format(sname))
    streamstojoin = context['ti'].xcom_pull(task_ids='step_6_solution_task_prediction',key="{}_streamstojoin".format(sname))
    inputdata = context['ti'].xcom_pull(task_ids='step_6_solution_task_prediction',key="{}_inputdata".format(sname))
    consumefrom2 = context['ti'].xcom_pull(task_ids='step_6_solution_task_prediction',key="{}_consumefrom".format(sname))
    offset = context['ti'].xcom_pull(task_ids='step_6_solution_task_prediction',key="{}_offset".format(sname))
    delay = context['ti'].xcom_pull(task_ids='step_6_solution_task_prediction',key="{}_delay".format(sname))
    usedeploy = context['ti'].xcom_pull(task_ids='step_6_solution_task_prediction',key="{}_usedeploy".format(sname))
    networktimeout = context['ti'].xcom_pull(task_ids='step_6_solution_task_prediction',key="{}_networktimeout".format(sname))
    maxrows = context['ti'].xcom_pull(task_ids='step_6_solution_task_prediction',key="{}_maxrows".format(sname))
    topicid = context['ti'].xcom_pull(task_ids='step_6_solution_task_prediction',key="{}_topicid".format(sname))
    pathtoalgos = context['ti'].xcom_pull(task_ids='step_6_solution_task_prediction',key="{}_pathtoalgos".format(sname))

    if ml_prediction_topic:
        subprocess.call(["sed", "-i", "-e",  "s/--preprocess_data_topic--/{}/g".format(preprocess_data_topic), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--ml_prediction_topic--/{}/g".format(ml_prediction_topic), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--streamstojoin--/{}/g".format(streamstojoin), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--inputdata--/{}/g".format(inputdata), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--consumefrom2--/{}/g".format(consumefrom2), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--offset--/{}/g".format(offset[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--delay--/{}/g".format(delay[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--usedeploy--/{}/g".format(usedeploy[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--networktimeout--/{}/g".format(networktimeout[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--maxrows--/{}/g".format(maxrows[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--topicid--/{}/g".format(topicid[1:]), "/{}/docs/source/details.rst".format(sname)])
        doparse("/{}/docs/source/details.rst".format(sname), ["--pathtoalgos--;{}".format(pathtoalgos)])
        
    topic = context['ti'].xcom_pull(task_ids='step_7_solution_task_visualization',key="{}_topic".format(sname))
    secure = context['ti'].xcom_pull(task_ids='step_7_solution_task_visualization',key="{}_secure".format(sname))
    offset = context['ti'].xcom_pull(task_ids='step_7_solution_task_visualization',key="{}_offset".format(sname))
    append = context['ti'].xcom_pull(task_ids='step_7_solution_task_visualization',key="{}_append".format(sname))
    chip = context['ti'].xcom_pull(task_ids='step_7_solution_task_visualization',key="{}_chip".format(sname))
    rollbackoffset = context['ti'].xcom_pull(task_ids='step_7_solution_task_visualization',key="{}_rollbackoffset".format(sname))
    dashboardhtml = context['ti'].xcom_pull(task_ids='step_7_solution_task_visualization',key="{}_dashboardhtml".format(sname))

    containername = context['ti'].xcom_pull(task_ids='step_8_solution_task_containerize',key="{}_containername".format(sname))
    if containername:
        hcname = containername.split('/')[1]
        huser = containername.split('/')[0]
        hurl = "https://hub.docker.com/r/{}/{}".format(huser,hcname)
    else:    
        containername="TBD"
    
    if vipervizport:
        subprocess.call(["sed", "-i", "-e",  "s/--vipervizport--/{}/g".format(vipervizport[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--topic--/{}/g".format(topic), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--dashboardhtml--/{}/g".format(dashboardhtml), "/{}/docs/source/details.rst".format(sname)])        
        subprocess.call(["sed", "-i", "-e",  "s/--secure--/{}/g".format(secure[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--offset--/{}/g".format(offset[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--append--/{}/g".format(append[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--chip--/{}/g".format(chip), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--rollbackoffset--/{}/g".format(rollbackoffset[1:]), "/{}/docs/source/details.rst".format(sname)])
    
    
    repo = tsslogging.getrepo() 
    gitrepo="https://github.com/{}/{}/tree/main/tml-airflow/dags/tml-solutions/{}".format(os.environ['GITUSERNAME'],repo,sname)
   # gitrepo = "\/{}\/tml-airflow\/dags\/tml-solutions\/{}".format(repo,sname)
    
    v=subprocess.call(["sed", "-i", "-e",  "s/--gitrepo--/{}/g".format(gitrepo), "/{}/docs/source/operating.rst".format(sname)])
    print("V=",v)
    doparse("/{}/docs/source/operating.rst".format(sname), ["--gitrepo--;{}".format(gitrepo)])
    
    subprocess.call(["sed", "-i", "-e",  "s/--solutionname--/{}/g".format(sname), "/{}/docs/source/operating.rst".format(sname)])
    subprocess.call(["sed", "-i", "-e",  "s/--dockercontainer--/{}\n\n{}/g".format(containername,hurl), "/{}/docs/source/operating.rst".format(sname)])
       
    chipmain = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_chip".format(sname))  
    
    doparse("/{}/docs/source/operating.rst".format(sname), ["--justcontainer--;{}".format(containername)])
    
    doparse("/{}/docs/source/operating.rst".format(sname), ["--tsscontainer--;maadsdocker/tml-solution-studio-with-airflow-{}".format(chip)])
    
    doparse("/{}/docs/source/operating.rst".format(sname), ["--chip--;{}".format(chipmain)])
    if istss1==0:
      doparse("/{}/docs/source/operating.rst".format(sname), ["--solutionairflowport--;{}".format(solutionairflowport[1:])])
    else:
      doparse("/{}/docs/source/operating.rst".format(sname), ["--solutionairflowport--;{}".format("TBD")])
     
    doparse("/{}/docs/source/operating.rst".format(sname), ["--externalport--;{}".format(externalport[1:])])
    if istss1==0:
      doparse("/{}/docs/source/operating.rst".format(sname), ["--solutionexternalport--;{}".format(solutionexternalport[1:])])
    else: 
      doparse("/{}/docs/source/operating.rst".format(sname), ["--solutionexternalport--;{}".format("TBD")])
    
    pconsumefrom = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_consumefrom".format(sname))
    pgpt_data_topic = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_pgpt_data_topic".format(sname))
    pgptcontainername = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_pgptcontainername".format(sname))
    poffset = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_offset".format(sname))
    prollbackoffset = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_rollbackoffset".format(sname))
    ptopicid = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_topicid".format(sname))
    penabletls = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_enabletls".format(sname))
    ppartition = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_partition".format(sname))
    pprompt = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_prompt".format(sname))
    pcontext = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_context".format(sname))
    pjsonkeytogather = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_jsonkeytogather".format(sname))
    pkeyattribute = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_keyattribute".format(sname))
    pconcurrency = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_concurrency".format(sname))
    pcuda = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_cuda".format(sname))
    pcollection = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_vectordbcollectionname".format(sname))    
    pgpthost = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_pgpthost".format(sname))
    pgptport = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_pgptport".format(sname))
    pprocesstype = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_keyprocesstype".format(sname))
    hyperbatch = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_hyperbatch".format(sname))
          
    if len(CLIENTPORT) > 1:
      doparse("/{}/docs/source/operating.rst".format(sname), ["--clientport--;{}".format(TMLCLIENTPORT[1:])])
      dockerrun = """docker run -d -p {}:{} -p {}:{} -p {}:{} -p {}:{} \\
          --env TSS=0 \\
          --env SOLUTIONNAME={} \\
          --env SOLUTIONDAG={} \\
          --env GITUSERNAME={} \\
          --env GITREPOURL={} \\
          --env SOLUTIONEXTERNALPORT={} \\
          -v /var/run/docker.sock:/var/run/docker.sock:z  \\
          --env CHIP={} \\
          --env SOLUTIONAIRFLOWPORT={}  \\
          --env SOLUTIONVIPERVIZPORT={} \\
          --env DOCKERUSERNAME='{}' \\
          --env CLIENTPORT={}  \\
          --env EXTERNALPORT={} \\
          --env KAFKACLOUDUSERNAME='{}' \\
          --env VIPERVIZPORT={} \\
          --env MQTTUSERNAME='{}' \\
          --env AIRFLOWPORT={}  \\
          --env GITPASSWORD='<Enter Github Password>' \\
          --env KAFKACLOUDPASSWORD='<Enter API secret>' \\
          --env MQTTPASSWORD='<Enter mqtt password>' \\
          --env READTHEDOCS='<Enter Readthedocs token>' \\
          {}""".format(solutionexternalport[1:],solutionexternalport[1:],
                          solutionairflowport[1:],solutionairflowport[1:],solutionvipervizport[1:],solutionvipervizport[1:],
                          TMLCLIENTPORT[1:],TMLCLIENTPORT[1:],sname,sd,os.environ['GITUSERNAME'],
                          os.environ['GITREPOURL'],solutionexternalport[1:],chipmain,
                          solutionairflowport[1:],solutionvipervizport[1:],os.environ['DOCKERUSERNAME'],TMLCLIENTPORT[1:],
                          externalport[1:],kafkacloudusername,vipervizport[1:],mqttusername,airflowport[1:],containername)       
    else:
      doparse("/{}/docs/source/operating.rst".format(sname), ["--clientport--;Not Applicable"])
      dockerrun = """docker run -d -p {}:{} -p {}:{} -p {}:{} \\
          --env TSS=0 \\
          --env SOLUTIONNAME={} \\
          --env SOLUTIONDAG={} \\
          --env GITUSERNAME={}  \\
          --env GITREPOURL={} \\
          --env SOLUTIONEXTERNALPORT={} \\
          -v /var/run/docker.sock:/var/run/docker.sock:z \\
          --env CHIP={} \\
          --env SOLUTIONAIRFLOWPORT={} \\
          --env SOLUTIONVIPERVIZPORT={} \\
          --env DOCKERUSERNAME='{}' \\
          --env EXTERNALPORT={} \\
          --env KAFKACLOUDUSERNAME='{}' \\
          --env VIPERVIZPORT={} \\
          --env MQTTUSERNAME='{}' \\
          --env AIRFLOWPORT={} \\
          --env MQTTPASSWORD='<Enter mqtt password>' \\
          --env KAFKACLOUDPASSWORD='<Enter API secret>' \\
          --env GITPASSWORD='<Enter Github Password>' \\
          --env READTHEDOCS='<Enter Readthedocs token>' \\
          {}""".format(solutionexternalport[1:],solutionexternalport[1:],
                          solutionairflowport[1:],solutionairflowport[1:],solutionvipervizport[1:],solutionvipervizport[1:],
                          sname,sd,os.environ['GITUSERNAME'],
                          os.environ['GITREPOURL'],solutionexternalport[1:],chipmain,
                          solutionairflowport[1:],solutionvipervizport[1:],os.environ['DOCKERUSERNAME'],
                          externalport[1:],kafkacloudusername,vipervizport[1:],mqttusername,airflowport[1:],containername)
        
   # dockerrun = re.escape(dockerrun) 
    v=subprocess.call(["sed", "-i", "-e",  "s/--dockerrun--/{}/g".format(dockerrun), "/{}/docs/source/operating.rst".format(sname)])
    
    doparse("/{}/docs/source/operating.rst".format(sname), ["--dockerrun--;{}".format(dockerrun),"--dockercontainer--;{} ({})".format(containername, hurl)])
    doparse("/{}/docs/source/details.rst".format(sname), ["--dockerrun--;{}".format(dockerrun),"--dockercontainer--;{} ({})".format(containername, hurl)])
    
    if pgptcontainername != None:
        privategptrun = "docker run -d -p {}:{} --net=host --gpus all --env PORT={} --env GPU=1 --env COLLECTION={} --env WEB_CONCURRENCY={} --env CUDA_VISIBLE_DEVICES={} {}".format(pgptport[1:],pgptport[1:],pgptport[1:],pcollection,pconcurrency[1:],pcuda[1:],pgptcontainername)

        doparse("/{}/docs/source/details.rst".format(sname), ["--pgptcontainername--;{}".format(pgptcontainername),"--privategptrun--;{}".format(privategptrun)])

        qdrantcontainer = "qdrant/qdrant"
        qdrantrun = "docker run -d -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage:z qdrant/qdrant"
        doparse("/{}/docs/source/details.rst".format(sname), ["--qdrantcontainer--;{}".format(qdrantcontainer),"--qdrantrun--;{}".format(qdrantrun)])

        doparse("/{}/docs/source/details.rst".format(sname), ["--consumefrom--;{}".format(pconsumefrom)])
        doparse("/{}/docs/source/details.rst".format(sname), ["--pgpt_data_topic--;{}".format(pgpt_data_topic)])
        doparse("/{}/docs/source/details.rst".format(sname), ["--vectordbcollectionname--;{}".format(pcollection)])
        doparse("/{}/docs/source/details.rst".format(sname), ["--offset--;{}".format(poffset[1:])])
        doparse("/{}/docs/source/details.rst".format(sname), ["--rollbackoffset--;{}".format(prollbackoffset[1:])])
        doparse("/{}/docs/source/details.rst".format(sname), ["--topicid--;{}".format(ptopicid[1:])])
        doparse("/{}/docs/source/details.rst".format(sname), ["--enabletls--;{}".format(penabletls[1:])])
        doparse("/{}/docs/source/details.rst".format(sname), ["--partition--;{}".format(ppartition[1:])])
        doparse("/{}/docs/source/details.rst".format(sname), ["--prompt--;{}".format(pprompt)])
        doparse("/{}/docs/source/details.rst".format(sname), ["--context--;{}".format(pcontext)])
        doparse("/{}/docs/source/details.rst".format(sname), ["--jsonkeytogather--;{}".format(pjsonkeytogather)])
        doparse("/{}/docs/source/details.rst".format(sname), ["--keyattribute--;{}".format(pkeyattribute)])
        doparse("/{}/docs/source/details.rst".format(sname), ["--concurrency--;{}".format(pconcurrency[1:])])
        doparse("/{}/docs/source/details.rst".format(sname), ["--cuda--;{}".format(pcuda[1:])])
        if kube == 1:
            doparse("/{}/docs/source/details.rst".format(sname), ["--pgpthost--;{}".format('privategpt-service')])
        else:   
            doparse("/{}/docs/source/details.rst".format(sname), ["--pgpthost--;{}".format(pgpthost)])

        doparse("/{}/docs/source/details.rst".format(sname), ["--pgptport--;{}".format(pgptport[1:])])
        doparse("/{}/docs/source/details.rst".format(sname), ["--keyprocesstype--;{}".format(pprocesstype)])
        doparse("/{}/docs/source/details.rst".format(sname), ["--hyperbatch--;{}".format(hyperbatch[1:])])
    
    
    rbuf = "https://{}.readthedocs.io".format(sname)
    doparse("/{}/docs/source/details.rst".format(sname), ["--readthedocs--;{}".format(rbuf)])
    
    ############# VIZ URLS
    
    vizurl = "http:\/\/localhost:{}\/{}?topic={}\&offset={}\&groupid=\&rollbackoffset={}\&topictype=prediction\&append={}\&secure={}".format(solutionvipervizport[1:],dashboardhtml,topic,offset[1:],rollbackoffset[1:],append[1:],secure[1:])
    vizurlkube = "http://localhost:{}/{}?topic={}&offset={}&groupid=&rollbackoffset={}&topictype=prediction&append={}&secure={}".format(solutionvipervizport[1:],dashboardhtml,topic,offset[1:],rollbackoffset[1:],append[1:],secure[1:])

    if istss1==0:
      subprocess.call(["sed", "-i", "-e",  "s/--visualizationurl--/{}/g".format(vizurl), "/{}/docs/source/operating.rst".format(sname)])
    else: 
      subprocess.call(["sed", "-i", "-e",  "s/--visualizationurl--/{}/g".format("This will appear AFTER you run Your Solution Docker Container"), "/{}/docs/source/operating.rst".format(sname)])

    tssvizurl = "http:\/\/localhost:{}\/{}?topic={}\&offset={}\&groupid=\&rollbackoffset={}\&topictype=prediction\&append={}\&secure={}".format(vipervizport[1:],dashboardhtml,topic,offset[1:],rollbackoffset[1:],append[1:],secure[1:])
    subprocess.call(["sed", "-i", "-e",  "s/--tssvisualizationurl--/{}/g".format(tssvizurl), "/{}/docs/source/operating.rst".format(sname)])

    tsslogfile = "http:\/\/localhost:{}\/viperlogs.html?topic=viperlogs\&append=0".format(vipervizport[1:])
    subprocess.call(["sed", "-i", "-e",  "s/--tsslogfile--/{}/g".format(tsslogfile), "/{}/docs/source/operating.rst".format(sname)])

    solutionlogfile = "http:\/\/localhost:{}\/viperlogs.html?topic=viperlogs\&append=0".format(solutionvipervizport[1:])
    if istss1==0:
      subprocess.call(["sed", "-i", "-e",  "s/--solutionlogfile--/{}/g".format(solutionlogfile), "/{}/docs/source/operating.rst".format(sname)])
    else:
      subprocess.call(["sed", "-i", "-e",  "s/--solutionlogfile--/{}/g".format("This will appear AFTER you run Your Solution Docker Container"), "/{}/docs/source/operating.rst".format(sname)])
     
    githublogs = "https:\/\/github.com\/{}\/{}\/blob\/main\/tml-airflow\/logs\/logs.txt".format(os.environ['GITUSERNAME'],repo)
    subprocess.call(["sed", "-i", "-e",  "s/--githublogs--/{}/g".format(githublogs), "/{}/docs/source/operating.rst".format(sname)])
    #-----------------------
    subprocess.call(["sed", "-i", "-e",  "s/--githublogs--/{}/g".format(githublogs), "/{}/docs/source/logs.rst".format(sname)])
    tsslogging.locallogs("INFO", "STEP 10: Documentation successfully built on GitHub..Readthedocs build in process and should complete in few seconds")
    try:
       sf = "" 
       with open('/dagslocalbackup/logs.txt', "r") as f:
            sf=f.read()
       doparse("/{}/docs/source/logs.rst".format(sname), ["--logs--;{}".format(sf)])
    except Exception as e:
      print("Cannot open file - ",e)  
      pass        
    
    #-------------------    
    airflowurl = "http:\/\/localhost:{}".format(airflowport[1:])
    subprocess.call(["sed", "-i", "-e",  "s/--airflowurl--/{}/g".format(airflowurl), "/{}/docs/source/operating.rst".format(sname)])
    
    readthedocs = "https:\/\/{}.readthedocs.io".format(sname)
    subprocess.call(["sed", "-i", "-e",  "s/--readthedocs--/{}/g".format(readthedocs), "/{}/docs/source/operating.rst".format(sname)])
    
    triggername = sd
    print("triggername=",triggername)
    doparse("/{}/docs/source/operating.rst".format(sname), ["--triggername--;{}".format(sd)])
    doparse("/{}/docs/source/operating.rst".format(sname), ["--airflowport--;{}".format(airflowport[1:])])
    doparse("/{}/docs/source/operating.rst".format(sname), ["--vipervizport--;{}".format(vipervizport[1:])])
    if istss1==0:
      doparse("/{}/docs/source/operating.rst".format(sname), ["--solutionvipervizport--;{}".format(solutionvipervizport[1:])])
    else: 
      doparse("/{}/docs/source/operating.rst".format(sname), ["--solutionvipervizport--;{}".format("TBD")])

    tssdockerrun = ("docker run -d \-\-net=host \-\-env AIRFLOWPORT={} " \
                    " -v <change to your local folder>:/dagslocalbackup:z " \
                    " -v /var/run/docker.sock:/var/run/docker.sock:z " \
                    " \-\-env GITREPOURL={} " \
                    " \-\-env CHIP={} \-\-env TSS=1 \-\-env SOLUTIONNAME=TSS " \
                    " \-\-env EXTERNALPORT={} " \
                    " \-\-env VIPERVIZPORT={} " \
                    " \-\-env GITUSERNAME='{}' " \
                    " \-\-env DOCKERUSERNAME='{}' " \
                    " \-\-env MQTTUSERNAME='{}' " \
                    " \-\-env KAFKACLOUDUSERNAME='{}' " \
                    " \-\-env KAFKACLOUDPASSWORD='<Enter your API secret>' " \
                    " \-\-env READTHEDOCS='<Enter your readthedocs token>' " \
                    " \-\-env GITPASSWORD='<Enter personal access token>' " \
                    " \-\-env DOCKERPASSWORD='<Enter your docker hub password>' " \
                    " \-\-env MQTTPASSWORD='<Enter your mqtt password>' " \
                    " maadsdocker/tml-solution-studio-with-airflow-{}".format(airflowport[1:],os.environ['GITREPOURL'],
                            chip,externalport[1:],vipervizport[1:],
                            os.environ['GITUSERNAME'],os.environ['DOCKERUSERNAME'],mqttusername,kafkacloudusername,chip))
    
    doparse("/{}/docs/source/operating.rst".format(sname), ["--tssdockerrun--;{}".format(tssdockerrun)])
    
    producinghost = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERHOSTPRODUCE".format(sname))
    producingport = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_SOLUTIONEXTERNALPORT".format(sname))
    preprocesshost = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERHOSTPREPROCESS".format(sname))
    preprocessport = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERPORTPREPROCESS".format(sname))
    preprocesshost2 = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERHOSTPREPROCESS2".format(sname))
    preprocessport2 = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERPORTPREPROCESS2".format(sname))

    preprocesshostpgpt = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERHOSTPREPROCESSPGPT".format(sname))
    preprocessportpgpt = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERPORTPREPROCESSPGPT".format(sname))
    
    mlhost = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERHOSTML".format(sname))
    mlport = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERPORTML".format(sname))
    predictionhost = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERHOSTPREDICT".format(sname))
    predictionport = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERPORTPREDICT".format(sname))

    hpdehost = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_HPDEHOST".format(sname))
    hpdeport = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_HPDEPORT".format(sname))

    hpdepredicthost = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_HPDEHOSTPREDICT".format(sname))
    hpdepredictport = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_HPDEPORTPREDICT".format(sname))
        
    tmlbinaries = ("VIPERHOST_PRODUCE={}, VIPERPORT_PRODUCE={}, "
                       "VIPERHOST_PREPOCESS={}, VIPERPORT_PREPROCESS={}, "
                       "VIPERHOST_PREPOCESS2={}, VIPERPORT_PREPROCESS2={}, "                   
                       "VIPERHOST_PREPOCESS_PGPT={}, VIPERPORT_PREPROCESS_PGPT={}, "                   
                       "VIPERHOST_ML={}, VIPERPORT_ML={}, "
                       "VIPERHOST_PREDCT={}, VIPERPORT_PREDICT={}, "
                       "HPDEHOST={}, HPDEPORT={}, "
                       "HPDEHOST_PREDICT={}, HPDEPORT_PREDICT={}".format(producinghost,producingport[1:],preprocesshost,preprocessport[1:],
                                                                            preprocesshost2,preprocessport2[1:],
                                                                             preprocesshostpgpt,preprocessportpgpt[1:],
                                                                              mlhost,mlport[1:],predictionhost,predictionport[1:],
                                                                              hpdehost,hpdeport[1:],hpdepredicthost,hpdepredictport[1:] ))
 
    
    subprocess.call(["sed", "-i", "-e",  "s/--tmlbinaries--/{}/g".format(tmlbinaries), "/{}/docs/source/operating.rst".format(sname)])
    ########################## Kubernetes
   
    doparse("/{}/docs/source/kube.rst".format(sname), ["--solutionnamefile--;{}.yml".format(sname)])
    doparse("/{}/docs/source/kube.rst".format(sname), ["--solutionname--;{}".format(sname)])
    if pgptcontainername == None:
            kcmd = "kubectl create -f mysql-storage.yml -f mysql-db-deployment.yml -f {}.yml".format(sname)
            doparse("/{}/docs/source/kube.rst".format(sname), ["--kubectl--;{}".format(kcmd)])
    else:
            kcmd = "kubectl create -f mysql-storage.yml -f mysql-db-deployment.yml -f qdrant.yml -f privategpt.yml -f {}.yml".format(sname)
            doparse("/{}/docs/source/kube.rst".format(sname), ["--kubectl--;{}".format(kcmd)])
    
    kcmd2=tsslogging.genkubeyaml(sname,containername,TMLCLIENTPORT[1:],solutionairflowport[1:],solutionvipervizport[1:],solutionexternalport[1:],
                       sd,os.environ['GITUSERNAME'],os.environ['GITREPOURL'],chipmain,os.environ['DOCKERUSERNAME'],
                       externalport[1:],kafkacloudusername,mqttusername,airflowport[1:],vipervizport[1:])

    doparse("/{}/docs/source/kube.rst".format(sname), ["--solutionnamecode--;{}".format(kcmd2)])

    kpfwd="kubectl port-forward deployment/{} {}:{}".format(sname,solutionvipervizport[1:],solutionvipervizport[1:])
    doparse("/{}/docs/source/kube.rst".format(sname), ["--kube-portforward--;{}".format(kpfwd)])
    doparse("/{}/docs/source/kube.rst".format(sname), ["--visualizationurl--;{}".format(vizurlkube)])
        
    ###########################
    try:
      tmuxwindows = "None"  
      with open("/tmux/pythonwindows_{}.txt".format(sname), 'r', encoding='utf-8') as file: 
        data = file.readlines() 
        data.append("viper-produce")
        data.append("viper-preprocess")
        data.append("viper-preprocess-pgpt")
        data.append("viper-ml")
        data.append("viper-predict")
        tmuxwindows = ", ".join(data)
        tmuxwindows = tmuxwindows.replace("\n","")
        print("tmuxwindows=",tmuxwindows)
    except Exception as e:
       pass 

    doparse("/{}/docs/source/operating.rst".format(sname), ["--tmuxwindows--;{}".format(tmuxwindows)])
    try:
     if os.environ['TSS'] == "1":
      doparse("/{}/docs/source/operating.rst".format(sname), ["--tssgen--;TSS Development Environment Container"])
     else:
       if "KUBE" not in os.environ:
         doparse("/{}/docs/source/operating.rst".format(sname), ["--tssgen--;TML Solution Container"])
       else:
         if os.environ["KUBE"] == "0":
           doparse("/{}/docs/source/operating.rst".format(sname), ["--tssgen--;TML Solution Container"])
         else: 
           doparse("/{}/docs/source/operating.rst".format(sname), ["--tssgen--;TML Solution Container (RUNNING IN KUBERNETES)"])
           
    # Kick off shell script 
    #tsslogging.git_push("/{}".format(sname),"For solution details GOTO: https://{}.readthedocs.io".format(sname),sname)
    
     subprocess.call("/tmux/gitp.sh {} 'For solution details GOTO: https://{}.readthedocs.io'".format(sname,sname), shell=True)
    
     rtd = context['ti'].xcom_pull(task_ids='step_10_solution_task_document',key="{}_RTD".format(sname))

     if rtd == None: 
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
            "language": "en",
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
     time.sleep(10)
     updatebranch(sname,"main")
     triggerbuild(sname)
     ti = context['task_instance']
     ti.xcom_push(key="{}_RTD".format(sname), value="DONE")
    except Exception as e:
     print("ERROR=",e)
