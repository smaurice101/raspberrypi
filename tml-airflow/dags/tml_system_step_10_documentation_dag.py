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
 'conf_version' : '0.1.0',
 'dockerenv': '', # add any environmental variables for docker must be: variable1=value1, variable2=value2
 'dockerinstructions': '', # add instructions on how to run the docker container
}

############################################################### DO NOT MODIFY BELOW ####################################################

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
    
def setupurls(projectname,producetype,sname):

    ptype=""
    if producetype=="LOCALFILE":
      ptype=producetype
    elif producetype=="REST":
      ptype="RESTAPI"
    elif producetype=="MQTT":
      ptype=producetype
    elif producetype=="gRPC":
      ptype=producetype

    
    stepurl1="https://github.com/{}/{}/tree/main/tml-airflow/dags/tml-solutions/{}/tml_system_step_1_getparams_dag-{}.py".format(os.environ['GITUSERNAME'],tsslogging.getrepo(),projectname,projectname)
    stepurl2="https://github.com/{}/{}/tree/main/tml-airflow/dags/tml-solutions/{}/tml_system_step_2_kafka_createtopic_dag-{}.py".format(os.environ['GITUSERNAME'],tsslogging.getrepo(),projectname,projectname)
    stepurl3="https://github.com/{}/{}/tree/main/tml-airflow/dags/tml-solutions/{}/tml_read_{}_step_3_kafka_producetotopic_dag-{}.py".format(os.environ['GITUSERNAME'],tsslogging.getrepo(),projectname,ptype,projectname)
    stepurl4="https://github.com/{}/{}/tree/main/tml-airflow/dags/tml-solutions/{}/tml_system_step_4_kafka_preprocess_dag-{}.py".format(os.environ['GITUSERNAME'],tsslogging.getrepo(),projectname,projectname)
    stepurl4a="https://github.com/{}/{}/tree/main/tml-airflow/dags/tml-solutions/{}/tml_system_step_4a_kafka_preprocess_dag-{}.py".format(os.environ['GITUSERNAME'],tsslogging.getrepo(),projectname,projectname)
    stepurl4b="https://github.com/{}/{}/tree/main/tml-airflow/dags/tml-solutions/{}/tml_system_step_4b_kafka_preprocess_dag-{}.py".format(os.environ['GITUSERNAME'],tsslogging.getrepo(),projectname,projectname)
    stepurl4c="https://github.com/{}/{}/tree/main/tml-airflow/dags/tml-solutions/{}/tml_system_step_4c_kafka_preprocess_dag-{}.py".format(os.environ['GITUSERNAME'],tsslogging.getrepo(),projectname,projectname)
    stepurl5="https://github.com/{}/{}/tree/main/tml-airflow/dags/tml-solutions/{}/tml_system_step_5_kafka_machine_learning_dag-{}.py".format(os.environ['GITUSERNAME'],tsslogging.getrepo(),projectname,projectname)
    stepurl6="https://github.com/{}/{}/tree/main/tml-airflow/dags/tml-solutions/{}/tml_system_step_6_kafka_predictions_dag-{}.py".format(os.environ['GITUSERNAME'],tsslogging.getrepo(),projectname,projectname)
    stepurl7="https://github.com/{}/{}/tree/main/tml-airflow/dags/tml-solutions/{}/tml_system_step_7_kafka_visualization_dag-{}.py".format(os.environ['GITUSERNAME'],tsslogging.getrepo(),projectname,projectname)
    stepurl8="https://github.com/{}/{}/tree/main/tml-airflow/dags/tml-solutions/{}/tml_system_step_8_deploy_solution_to_docker_dag-{}.py".format(os.environ['GITUSERNAME'],tsslogging.getrepo(),projectname,projectname)
    stepurl9="https://github.com/{}/{}/tree/main/tml-airflow/dags/tml-solutions/{}/tml_system_step_9_privategpt_qdrant_dag-{}.py".format(os.environ['GITUSERNAME'],tsslogging.getrepo(),projectname,projectname)
    stepurl9b="https://github.com/{}/{}/tree/main/tml-airflow/dags/tml-solutions/{}/tml_system_step_9b_agenticai_dag-{}.py".format(os.environ['GITUSERNAME'],tsslogging.getrepo(),projectname,projectname)
    stepurl10="https://github.com/{}/{}/tree/main/tml-airflow/dags/tml-solutions/{}/tml_system_step_10_documentation_dag_tml-multi-agenticai-iot-3f10-{}.py".format(os.environ['GITUSERNAME'],tsslogging.getrepo(),projectname,projectname)

    print("stepurl1=",stepurl1)
    
    doparse("/{}/docs/source/details.rst".format(sname), ["--step1url--;{}".format(stepurl1)])
    doparse("/{}/docs/source/details.rst".format(sname), ["--step2url--;{}".format(stepurl2)])
    doparse("/{}/docs/source/details.rst".format(sname), ["--step3url--;{}".format(stepurl3)])
    doparse("/{}/docs/source/details.rst".format(sname), ["--step4url--;{}".format(stepurl4)])
    doparse("/{}/docs/source/details.rst".format(sname), ["--step4aurl--;{}".format(stepurl4a)])
    doparse("/{}/docs/source/details.rst".format(sname), ["--step4burl--;{}".format(stepurl4b)])
    doparse("/{}/docs/source/details.rst".format(sname), ["--step4curl--;{}".format(stepurl4c)])
    doparse("/{}/docs/source/details.rst".format(sname), ["--step5url--;{}".format(stepurl5)])
    doparse("/{}/docs/source/details.rst".format(sname), ["--step6url--;{}".format(stepurl6)])
    doparse("/{}/docs/source/details.rst".format(sname), ["--step7url--;{}".format(stepurl7)])
    doparse("/{}/docs/source/details.rst".format(sname), ["--step8url--;{}".format(stepurl8)])
    doparse("/{}/docs/source/details.rst".format(sname), ["--step9url--;{}".format(stepurl9)])
    doparse("/{}/docs/source/details.rst".format(sname), ["--step9burl--;{}".format(stepurl9b)]) 
    doparse("/{}/docs/source/details.rst".format(sname), ["--step10url--;{}".format(stepurl10)])
    
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

def updateollamaandpgpt(op,ollamacontainername,concurrency,collection,temp,rollback,ollama,deletevector,vectordbpath,topicid,enabletls,partition,mainip,
                       mainport,embedding,agents_topic_prompt,teamlead_topic,teamleadprompt,supervisor_topic,supervisorprompt,agenttoolfunctions,agent_team_supervisor_topic,
                       pvectorsearchtype,ptemperature,pcollection,pconcurrency,pvectordimension,pcontextwindowsize,mainmodel,mainembedding,pgptcontainername):
      print("update==",op)
      if ollamacontainername != None:
       doparse("/{}/ollama.yml".format(op), ["--ollamacontainername--;{}".format(ollamacontainername)])
       doparse("/{}/ollama.yml".format(op), ["--agenticai-kubeconcur--;{}".format(concurrency[1:])])
       doparse("/{}/ollama.yml".format(op),  ["--agenticai-kubecollection--;{}".format(collection)])
       doparse("/{}/ollama.yml".format(op),  ["--agenticai-kubetemperature--;{}".format(temp[1:])])
       doparse("/{}/ollama.yml".format(op),  ["--agenticai-rollbackoffset--;{}".format(rollback[1:])])
       doparse("/{}/ollama.yml".format(op),  ["--agenticai-ollama-model--;{}".format(ollama)])
       doparse("/{}/ollama.yml".format(op),  ["--agenticai-deletevectordbcount--;{}".format(deletevector[1:])])
       doparse("/{}/ollama.yml".format(op),  ["--agenticai-vectordbpath--;{}".format(vectordbpath)])
       doparse("/{}/ollama.yml".format(op),  ["--agenticai-topicid--;{}".format(topicid[1:])])
       doparse("/{}/ollama.yml".format(op),  ["--agenticai-enabletls--;{}".format(enabletls[1:])])
       doparse("/{}/ollama.yml".format(op),  ["--agenticai-partition--;{}".format(partition[1:])])
       doparse("/{}/ollama.yml".format(op),  ["--agenticai-vectordbcollectionname--;{}".format(collection)])
       doparse("/{}/ollama.yml".format(op),  ["--agenticai-ollamacontainername--;{}".format(ollamacontainername)])
       doparse("/{}/ollama.yml".format(op),  ["--agenticai-mainip--;{}".format(mainip)])
       doparse("/{}/ollama.yml".format(op),  ["--agenticai-mainport--;{}".format(mainport[1:])])
       doparse("/{}/ollama.yml".format(op),  ["--agenticai-embedding--;{}".format(embedding)])
       doparse("/{}/ollama.yml".format(op),  ["--agenticai-agents_topic_prompt--;{}".format(agents_topic_prompt.strip().replace('\n','').replace("\\n","").replace("'","").replace(";",","))])
       doparse("/{}/ollama.yml".format(op),  ["--agenticai-teamlead_topic--;{}".format(teamlead_topic)])
       doparse("/{}/ollama.yml".format(op),  ["--agenticai-teamleadprompt--;{}".format(teamleadprompt.strip().replace('\n','').replace("\\n","").replace("'","").replace(";",","))])
       doparse("/{}/ollama.yml".format(op),  ["--agenticai-supervisor_topic--;{}".format(supervisor_topic)])
       doparse("/{}/ollama.yml".format(op),  ["--agenticai-supervisorprompt--;{}".format(supervisorprompt.strip().replace('\n','').replace("\\n","").replace("'","").replace(";",","))])
       doparse("/{}/ollama.yml".format(op),  ["--agenticai-agenttoolfunctions--;{}".format(agenttoolfunctions.strip().replace('\n','').replace("\\n","").replace("'","").replace(";","=="))])
       doparse("/{}/ollama.yml".format(op),  ["--agenticai-agent_team_supervisor_topic--;{}".format(agent_team_supervisor_topic)])

      if pgptcontainername != None:
       doparse("/{}/privategpt.yml".format(op), ["--kubevectorsearchtype--;{}".format(pvectorsearchtype)])
       doparse("/{}/privategpt.yml".format(op), ["--kubetemperature--;{}".format(ptemperature[1:])])
       doparse("/{}/privategpt.yml".format(op), ["--kubecollection--;{}".format(pcollection)])
       doparse("/{}/privategpt.yml".format(op), ["--kubeconcur--;{}".format(pconcurrency[1:])])
       doparse("/{}/privategpt.yml".format(op), ["--kubevectordimension--;{}".format(pvectordimension[1:])])
       doparse("/{}/privategpt.yml".format(op), ["--kubecontextwindowsize--;{}".format(pcontextwindowsize[1:])])
       doparse("/{}/privategpt.yml".format(op), ["--kubemainmodel--;{}".format(mainmodel)])
       doparse("/{}/privategpt.yml".format(op), ["--kubemainembedding--;{}".format(mainembedding)])
       doparse("/{}/privategpt.yml".format(op), ["--kubeprivategpt--;{}".format(pgptcontainername)])

def copyymls(projectname,sname,ingressyml,solutionyml):
    orepo=tsslogging.getrepo()
    op=f"/{orepo}/tml-airflow/dags/tml-solutions/{projectname}/ymls" 
    os.makedirs(op, exist_ok=True) 
    op=f"/{orepo}/tml-airflow/dags/tml-solutions/{projectname}/ymls/{sname}" 
    os.makedirs(op, exist_ok=True) 

    tsslogging.writeoutymls(op,ingressyml,solutionyml,sname)
    return op
  
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
    
    sd = context['dag'].dag_id
    sname=context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_solutionname".format(sd))
#    rtdsname = tsslogging.rtdprojects(sname,sd)

    kube=0
    step9prompt=''
    step9context=''
    step9keyattribute=''
    step9keyprocesstype=''
    step9hyperbatch=''
    step9vectordbcollectionname=''
    step9concurrency=''
    cudavisibledevices=''
    step9docfolder=''
    step9docfolderingestinterval=''
    step9useidentifierinprompt=''
    step5processlogic=''
    step5independentvariables=''
    step9searchterms=''
    step9streamall=''
    step9temperature=''
    step9vectorsearchtype=''
    step9pcontextwindowsize=''
    step9pgptcontainername=''
    step9pgpthost=''
    step9pgptport=''
    step9vectordimension=''
    step4crawdatatopic=''
    step4csearchterms=''
    step4crememberpastwindows=''
    step4cpatternwindowthreshold=''
    step4crtmsstream=''
    step4crtmsscorethreshold=''
    step4cattackscorethreshold=''
    step4cpatternscorethreshold=''
    step4clocalsearchtermfolder=''
    step4clocalsearchtermfolderinterval=''
    step4crtmsfoldername=''
    step3localfileinputfile=''
    step3localfiledocfolder=''
    step4crtmsmaxwindows=''
    rtmsoutputurl=""
    mloutputurl=""

    step2raw_data_topic=""
    step2preprocess_data_topic=""
    step4raw_data_topic=""
    step4preprocess_data_topic=''
    step4preprocesstypes=""
    step4jsoncriteria=""
    step4ajsoncriteria=""
    step4amaxrows=""
    step4apreprocesstypes=""
    step4araw_data_topic=""
    step4apreprocess_data_topic=""
    step4bpreprocesstypes=""
    step4bjsoncriteria=""
    step4bmaxrows=""
    step4braw_data_topic=""
    step4bpreprocess_data_topic=""

    step9brollback=""
    step9bdeletevectordbcount=""
    step9bvectordbpath=""
    step9btemperature=""
    step9bvectordbcollectionname=""
    step9bollamacontainername=""
    step9bCUDA_VISIBLE_DEVICES=""
    step9bmainip=""
    step9bmainport=""
    step9bembedding=""
    step9bagents_topic_prompt=""
    step9bteamlead_topic=""
    step9bteamleadprompt=""
    step9bsupervisor_topic=""
    step9bagenttoolfunctions=""
    step9bagent_team_supervisor_topic=""
    step9bconcurrency=""
    if "KUBE" in os.environ:
          if os.environ["KUBE"] == "1":
             kube=1
             return
    
    tsslogging.locallogs("INFO", "STEP 10: Started to build the documentation")
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
    projectname = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_projectname".format(sd))
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
 
    projecturl="https://github.com/{}/{}/tree/main/tml-airflow/dags/tml-solutions/{}".format(os.environ['GITUSERNAME'],tsslogging.getrepo(),projectname)
 
    doparse("/{}/docs/source/index.rst".format(sname), ["--projectname--;{}".format(projectname)])

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
    step2raw_data_topic=raw_data_topic
    preprocess_data_topic = context['ti'].xcom_pull(task_ids='step_2_solution_task_createtopic',key="{}_preprocess_data_topic".format(sname))
    step2preprocess_data_topic=preprocess_data_topic
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
    snamertd = sname.replace("_", "-")
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

    setupurls(projectname,PRODUCETYPE,sname)

    if PRODUCETYPE=='LOCALFILE':
      inputfile = context['ti'].xcom_pull(task_ids='step_3_solution_task_producetotopic',key="{}_inputfile".format(sname))
      step3localfileinputfile=inputfile
      docfolderprocess = context['ti'].xcom_pull(task_ids='step_3_solution_task_producetotopic',key="{}_docfolder".format(sname))
      step3localfiledocfolder=docfolderprocess
      doctopic = context['ti'].xcom_pull(task_ids='step_3_solution_task_producetotopic',key="{}_doctopic".format(sname))
      chunks = context['ti'].xcom_pull(task_ids='step_3_solution_task_producetotopic',key="{}_chunks".format(sname))
      docingestinterval = context['ti'].xcom_pull(task_ids='step_3_solution_task_producetotopic',key="{}_docingestinterval".format(sname))
      doparse("/{}/docs/source/details.rst".format(sname), ["--docfolderprocess--;{}".format(docfolderprocess)])
      doparse("/{}/docs/source/details.rst".format(sname), ["--doctopic--;{}".format(doctopic)])
      doparse("/{}/docs/source/details.rst".format(sname), ["--chunks--;{}".format(chunks[1:])])
      doparse("/{}/docs/source/details.rst".format(sname), ["--docingestinterval--;{}".format(docingestinterval[1:])])
      doparse("/{}/docs/source/details.rst".format(sname), ["--inputfile--;{}".format(inputfile)])
     
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
    if raw_data_topic:
      step4raw_data_topic=raw_data_topic
    preprocess_data_topic = context['ti'].xcom_pull(task_ids='step_4_solution_task_preprocess',key="{}_preprocess_data_topic".format(sname))    
    if preprocess_data_topic:
      step4preprocess_data_topic=preprocess_data_topic
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
    if preprocesstypes:
      step4preprocesstypes=preprocesstypes
    pathtotmlattrs = context['ti'].xcom_pull(task_ids='step_4_solution_task_preprocess',key="{}_pathtotmlattrs".format(sname))
    identifier = context['ti'].xcom_pull(task_ids='step_4_solution_task_preprocess',key="{}_identifier".format(sname))
    jsoncriteria = context['ti'].xcom_pull(task_ids='step_4_solution_task_preprocess',key="{}_jsoncriteria".format(sname))
    if jsoncriteria:
      step4jsoncriteria=jsoncriteria
    maxrows4 = context['ti'].xcom_pull(task_ids='step_4_solution_task_preprocess',key="{}_maxrows".format(sname))
    if maxrows4:
      step4maxrows=maxrows4

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
        subprocess.call(["sed", "-i", "-e",  "s/--maxrows--/{}/g".format(maxrows4[1:]), "/{}/docs/source/details.rst".format(sname)])

    raw_data_topic = context['ti'].xcom_pull(task_ids='step_4a_solution_task_preprocess',key="{}_raw_data_topic".format(sname))
    if raw_data_topic:
      step4araw_data_topic=raw_data_topic
    preprocess_data_topic = context['ti'].xcom_pull(task_ids='step_4a_solution_task_preprocess',key="{}_preprocess_data_topic".format(sname))    
    if preprocess_data_topic:
      step4apreprocess_data_topic=preprocess_data_topic
    preprocessconditions = context['ti'].xcom_pull(task_ids='step_4a_solution_task_preprocess',key="{}_preprocessconditions".format(sname))
    delay = context['ti'].xcom_pull(task_ids='step_4a_solution_task_preprocess',key="{}_delay".format(sname))
    array = context['ti'].xcom_pull(task_ids='step_4a_solution_task_preprocess',key="{}_array".format(sname))
    saveasarray = context['ti'].xcom_pull(task_ids='step_4a_solution_task_preprocess',key="{}_saveasarray".format(sname))
    topicid = context['ti'].xcom_pull(task_ids='step_4a_solution_task_preprocess',key="{}_topicid".format(sname))
    rawdataoutput = context['ti'].xcom_pull(task_ids='step_4a_solution_task_preprocess',key="{}_rawdataoutput".format(sname))
    asynctimeout = context['ti'].xcom_pull(task_ids='step_4a_solution_task_preprocess',key="{}_asynctimeout".format(sname))
    timedelay = context['ti'].xcom_pull(task_ids='step_4a_solution_task_preprocess',key="{}_timedelay".format(sname))
    usemysql = context['ti'].xcom_pull(task_ids='step_4a_solution_task_preprocess',key="{}_usemysql".format(sname))
    preprocesstypes = context['ti'].xcom_pull(task_ids='step_4a_solution_task_preprocess',key="{}_preprocesstypes".format(sname))
    if preprocesstypes:
      step4apreprocesstypes=preprocesstypes
    pathtotmlattrs = context['ti'].xcom_pull(task_ids='step_4a_solution_task_preprocess',key="{}_pathtotmlattrs".format(sname))
    identifier = context['ti'].xcom_pull(task_ids='step_4a_solution_task_preprocess',key="{}_identifier".format(sname))
    jsoncriteria = context['ti'].xcom_pull(task_ids='step_4a_solution_task_preprocess',key="{}_jsoncriteria".format(sname))
    if jsoncriteria:
     step4ajsoncriteria=jsoncriteria
    maxrows4 = context['ti'].xcom_pull(task_ids='step_4a_solution_task_preprocess',key="{}_maxrows".format(sname))
    if maxrows4:
      step4amaxrows=maxrows4

    if preprocess_data_topic:
        subprocess.call(["sed", "-i", "-e",  "s/--raw_data_topic1--/{}/g".format(raw_data_topic), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--preprocess_data_topic1--/{}/g".format(preprocess_data_topic), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--preprocessconditions1--/{}/g".format(preprocessconditions), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--delay1--/{}/g".format(delay[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--array1--/{}/g".format(array[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--saveasarray1--/{}/g".format(saveasarray[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--topicid1--/{}/g".format(topicid[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--rawdataoutput1--/{}/g".format(rawdataoutput[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--asynctimeout1--/{}/g".format(asynctimeout[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--timedelay1--/{}/g".format(timedelay[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--preprocesstypes1--/{}/g".format(preprocesstypes), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--pathtotmlattrs1--/{}/g".format(pathtotmlattrs), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--identifier1--/{}/g".format(identifier), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--jsoncriteria1--/{}/g".format(jsoncriteria), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--maxrows1--/{}/g".format(maxrows4[1:]), "/{}/docs/source/details.rst".format(sname)])

    raw_data_topic = context['ti'].xcom_pull(task_ids='step_4b_solution_task_preprocess',key="{}_raw_data_topic".format(sname))
    if raw_data_topic:
       step4braw_data_topic=raw_data_topic
    preprocess_data_topic = context['ti'].xcom_pull(task_ids='step_4b_solution_task_preprocess',key="{}_preprocess_data_topic".format(sname))    
    if preprocess_data_topic:
        step4bpreprocess_data_topic=preprocess_data_topic
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
    if preprocesstypes:
       step4bpreprocesstypes=preprocesstypes
    pathtotmlattrs = context['ti'].xcom_pull(task_ids='step_4b_solution_task_preprocess',key="{}_pathtotmlattrs".format(sname))
    identifier = context['ti'].xcom_pull(task_ids='step_4b_solution_task_preprocess',key="{}_identifier".format(sname))
    jsoncriteria = context['ti'].xcom_pull(task_ids='step_4b_solution_task_preprocess',key="{}_jsoncriteria".format(sname))
    if jsoncriteria:
       step4bjsoncriteria=jsoncriteria
    maxrows4b = context['ti'].xcom_pull(task_ids='step_4b_solution_task_preprocess',key="{}_maxrows".format(sname))
    if maxrows4b:
       step4bmaxrows=maxrows4b

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
        subprocess.call(["sed", "-i", "-e",  "s/--maxrows2--/{}/g".format(maxrows4b[1:]), "/{}/docs/source/details.rst".format(sname)])


    raw_data_topic = context['ti'].xcom_pull(task_ids='step_4c_solution_task_preprocess',key="{}_raw_data_topic".format(sname))
    preprocess_data_topic = context['ti'].xcom_pull(task_ids='step_4c_solution_task_preprocess',key="{}_preprocess_data_topic".format(sname))    
    delay = context['ti'].xcom_pull(task_ids='step_4c_solution_task_preprocess',key="{}_delay".format(sname))
    array = context['ti'].xcom_pull(task_ids='step_4c_solution_task_preprocess',key="{}_array".format(sname))
    saveasarray = context['ti'].xcom_pull(task_ids='step_4c_solution_task_preprocess',key="{}_saveasarray".format(sname))
    topicid = context['ti'].xcom_pull(task_ids='step_4c_solution_task_preprocess',key="{}_topicid".format(sname))
    rawdataoutput = context['ti'].xcom_pull(task_ids='step_4c_solution_task_preprocess',key="{}_rawdataoutput".format(sname))
    asynctimeout = context['ti'].xcom_pull(task_ids='step_4c_solution_task_preprocess',key="{}_asynctimeout".format(sname))
    timedelay = context['ti'].xcom_pull(task_ids='step_4c_solution_task_preprocess',key="{}_timedelay".format(sname))
    usemysql = context['ti'].xcom_pull(task_ids='step_4c_solution_task_preprocess',key="{}_usemysql".format(sname))
    searchterms = context['ti'].xcom_pull(task_ids='step_4c_solution_task_preprocess',key="{}_searchterms".format(sname))
    rememberpastwindows = context['ti'].xcom_pull(task_ids='step_4c_solution_task_preprocess',key="{}_rememberpastwindows".format(sname))
    identifier = context['ti'].xcom_pull(task_ids='step_4c_solution_task_preprocess',key="{}_identifier".format(sname))
    patternwindowthreshold = context['ti'].xcom_pull(task_ids='step_4c_solution_task_preprocess',key="{}_patternwindowthreshold".format(sname))
    maxrows4c = context['ti'].xcom_pull(task_ids='step_4c_solution_task_preprocess',key="{}_maxrows".format(sname))
    rtmsstream = context['ti'].xcom_pull(task_ids='step_4c_solution_task_preprocess',key="{}_rtmsstream".format(sname))
    rtmsscorethresholdtopic = context['ti'].xcom_pull(task_ids='step_4c_solution_task_preprocess',key="{}_rtmsscorethresholdtopic".format(sname))
    attackscorethresholdtopic = context['ti'].xcom_pull(task_ids='step_4c_solution_task_preprocess',key="{}_attackscorethresholdtopic".format(sname))
    patternscorethresholdtopic = context['ti'].xcom_pull(task_ids='step_4c_solution_task_preprocess',key="{}_patternscorethresholdtopic".format(sname))
    rtmsscorethreshold = context['ti'].xcom_pull(task_ids='step_4c_solution_task_preprocess',key="{}_rtmsscorethreshold".format(sname))
    attackscorethreshold = context['ti'].xcom_pull(task_ids='step_4c_solution_task_preprocess',key="{}_attackscorethreshold".format(sname))
    patternscorethreshold = context['ti'].xcom_pull(task_ids='step_4c_solution_task_preprocess',key="{}_patternscorethreshold".format(sname))
    rtmsmaxwindows = context['ti'].xcom_pull(task_ids='step_4c_solution_task_preprocess',key="{}_rtmsmaxwindows".format(sname))
    if rtmsmaxwindows:
      step4crtmsmaxwindows=rtmsmaxwindows
      subprocess.call(["sed", "-i", "-e",  "s/--rtmsmaxwindows--/{}/g".format(rtmsmaxwindows[1:]), "/{}/docs/source/details.rst".format(sname)])

    localsearchtermfolder = context['ti'].xcom_pull(task_ids='step_4c_solution_task_preprocess',key="{}_localsearchtermfolder".format(sname))
    localsearchtermfolderinterval = context['ti'].xcom_pull(task_ids='step_4c_solution_task_preprocess',key="{}_localsearchtermfolderinterval".format(sname))
    rtmsfoldername = context['ti'].xcom_pull(task_ids='step_4c_solution_task_preprocess',key="{}_rtmsfoldername".format(sname))

    if searchterms:
        doparse("/{}/docs/source/details.rst".format(sname), ["--rtmsscorethresholdtopic--;{}".format(rtmsscorethresholdtopic)])
        doparse("/{}/docs/source/details.rst".format(sname), ["--attackscorethresholdtopic--;{}".format(attackscorethresholdtopic)])
        doparse("/{}/docs/source/details.rst".format(sname), ["--patternscorethresholdtopic--;{}".format(patternscorethresholdtopic)])
        doparse("/{}/docs/source/details.rst".format(sname), ["--rtmsfoldername--;{}".format(rtmsfoldername)])

        doparse("/{}/docs/source/details.rst".format(sname), ["--rtmsscorethreshold--;{}".format(rtmsscorethreshold[1:])])
        doparse("/{}/docs/source/details.rst".format(sname), ["--attackscorethreshold--;{}".format(attackscorethreshold[1:])])
        doparse("/{}/docs/source/details.rst".format(sname), ["--patternscorethreshold--;{}".format(patternscorethreshold[1:])])
        subprocess.call(["sed", "-i", "-e",  "s/--raw_data_topic3--/{}/g".format(raw_data_topic), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--preprocess_data_topic3--/{}/g".format(preprocess_data_topic), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--rtmsstream--/{}/g".format(rtmsstream), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--delay3--/{}/g".format(delay[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--array3--/{}/g".format(array[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--saveasarray3--/{}/g".format(saveasarray[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--topicid3--/{}/g".format(topicid[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--rawdataoutput3--/{}/g".format(rawdataoutput[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--asynctimeout3--/{}/g".format(asynctimeout[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--timedelay3--/{}/g".format(timedelay[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--rememberpastwindows--/{}/g".format(rememberpastwindows[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--patternwindowthreshold--/{}/g".format(patternwindowthreshold[1:]), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--identifier3--/{}/g".format(identifier), "/{}/docs/source/details.rst".format(sname)])
        subprocess.call(["sed", "-i", "-e",  "s/--maxrows3--/{}/g".format(maxrows4c[1:]), "/{}/docs/source/details.rst".format(sname)])
        doparse("/{}/docs/source/details.rst".format(sname), ["--rtmssearchterms--;{}".format(searchterms)])
        rtmsoutputurl="https:\/\/github.com/{}/{}/tree/main/tml-airflow/dags/tml-solutions/{}/{}".format(os.environ["GITUSERNAME"], tsslogging.getrepo(),projectname,rtmsfoldername)
        doparse("/{}/docs/source/details.rst".format(sname), ["--rtmsoutputurl--;{}".format(rtmsoutputurl)])
        doparse("/{}/docs/source/details.rst".format(sname), ["--localsearchtermfolder--;{}".format(localsearchtermfolder)])
        doparse("/{}/docs/source/details.rst".format(sname), ["--localsearchtermfolderinterval--;{}".format(localsearchtermfolderinterval[1:])])
        doparse("/{}/docs/source/details.rst".format(sname), ["--rtmsfoldername--;{}".format(rtmsfoldername)])

        step4crawdatatopic=raw_data_topic
        step4csearchterms=searchterms
        step4crememberpastwindows=rememberpastwindows
        step4cpatternwindowthreshold=patternwindowthreshold
        step4crtmsstream=rtmsstream
        step4crtmsscorethreshold=rtmsscorethreshold
        step4cattackscorethreshold=attackscorethreshold
        step4cpatternscorethreshold=patternscorethreshold
        step4clocalsearchtermfolder=localsearchtermfolder
        step4clocalsearchtermfolderinterval=localsearchtermfolderinterval
        step4crtmsfoldername=rtmsfoldername
 
    preprocess_data_topic = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_preprocess_data_topic".format(sname))
    ml_data_topic = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_ml_data_topic".format(sname))
    modelruns = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_modelruns".format(sname))
    offset = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_offset".format(sname))
    islogistic = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_islogistic".format(sname))
    networktimeout = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_networktimeout".format(sname))
    modelsearchtuner = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_modelsearchtuner".format(sname))
    dependentvariable = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_dependentvariable".format(sname))
    independentvariables = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_independentvariables".format(sname))
    if independentvariables:
      step5independentvariables = independentvariables

    rollbackoffsets = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_rollbackoffsets".format(sname))
    topicid = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_topicid".format(sname))
    consumefrom = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_consumefrom".format(sname))
    fullpathtotrainingdata = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_fullpathtotrainingdata".format(sname))
    transformtype = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_transformtype".format(sname))
    sendcoefto = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_sendcoefto".format(sname))
    coeftoprocess = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_coeftoprocess".format(sname))
    coefsubtopicnames = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_coefsubtopicnames".format(sname))
    processlogic = context['ti'].xcom_pull(task_ids='step_5_solution_task_ml',key="{}_processlogic".format(sname))
    if fullpathtotrainingdata:
         step5sp=fullpathtotrainingdata.split("/")
         if len(step5sp)>0:
           mloutputurl="https:\/\/github.com/{}/{}/tree/main/tml-airflow/dags/tml-solutions/{}/mldata/{}".format(os.environ["GITUSERNAME"], tsslogging.getrepo(),projectname,step5sp[-1])
           doparse("/{}/docs/source/details.rst".format(sname), ["--mloutputurl--;{}".format(mloutputurl)])
     
    if processlogic:
      step5processlogic = processlogic
     
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
    gitrepo="https://github.com/{}/{}/tree/main/tml-airflow/dags/tml-solutions/{}".format(os.environ['GITUSERNAME'],repo,projectname)
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
    pmainmodel=""
    pmainembedding=""
    if pgptcontainername != None:
      step9pgptcontainername=pgptcontainername
      doparse("/{}/docs/source/kube.rst".format(sname), ["--kubeprivategpt--;{}".format(pgptcontainername)])
      mainmodel = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_mainmodel".format(sname))
      pmainmodel=mainmodel
      mainembedding = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_mainembedding".format(sname))
      pmainembedding=mainembedding
      doparse("/{}/docs/source/kube.rst".format(sname), ["--kubemainmodel--;{}".format(mainmodel)])
      doparse("/{}/docs/source/kube.rst".format(sname), ["--kubemainembedding--;{}".format(mainembedding)])
     
    poffset = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_offset".format(sname))
    prollbackoffset = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_rollbackoffset".format(sname))
    ptopicid = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_topicid".format(sname))
    penabletls = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_enabletls".format(sname))
    ppartition = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_partition".format(sname))
    pprompt = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_prompt".format(sname))
    pcontextwindowsize = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_contextwindowsize".format(sname))
    pvectordimension = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_vectordimension".format(sname))
    pmitrejson = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_mitrejson".format(sname))

    if pmitrejson:
       doparse("/{}/docs/source/details.rst".format(sname), ["--mitrejson--;{}".format(pmitrejson)])

    if pcontextwindowsize:
       step9pcontextwindowsize=pcontextwindowsize
       doparse("/{}/docs/source/details.rst".format(sname), ["--contextwindowsize--;{}".format(pcontextwindowsize[1:])])
       doparse("/{}/docs/source/kube.rst".format(sname), ["--kubecontextwindowsize--;{}".format(pcontextwindowsize[1:])])

    if pvectordimension:
       step9vectordimension=pvectordimension
       doparse("/{}/docs/source/details.rst".format(sname), ["--vectordimension--;{}".format(pvectordimension[1:])])
       doparse("/{}/docs/source/kube.rst".format(sname), ["--kubevectordimension--;{}".format(pvectordimension[1:])])
     
    if pprompt:
      step9prompt=pprompt
      step9prompt=step9prompt.strip().replace('\n','').replace("\\n","").replace(";",",").replace("''","")

    pdocfolder = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_docfolder".format(sname))
    if pdocfolder:
      step9docfolder=pdocfolder
      doparse("/{}/docs/source/details.rst".format(sname), ["--docfolder--;{}".format(pdocfolder)])
 
    pdocfolderingestinterval = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_docfolderingestinterval".format(sname))
    if pdocfolderingestinterval:
      step9docfolderingestinterval=pdocfolderingestinterval
      doparse("/{}/docs/source/details.rst".format(sname), ["--docfolderingestinterval--;{}".format(pdocfolderingestinterval[1:])])
 
    puseidentifierinprompt = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_useidentifierinprompt".format(sname))
    if puseidentifierinprompt:
      step9useidentifierinprompt=puseidentifierinprompt
      doparse("/{}/docs/source/details.rst".format(sname), ["--useidentifierinprompt--;{}".format(puseidentifierinprompt[1:])])
 
    pcontext = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_context".format(sname))
    if pcontext:
       step9context=pcontext
    pjsonkeytogather = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_jsonkeytogather".format(sname)) 
    pkeyattribute = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_keyattribute".format(sname))
    if pkeyattribute:
      step9keyattribute=pkeyattribute
    pconcurrency = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_concurrency".format(sname))
    if pconcurrency:
      step9concurrency=pconcurrency     
      doparse("/{}/docs/source/kube.rst".format(sname), ["--kubeconcur--;{}".format(pconcurrency[1:])])
     
    pcuda = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_cuda".format(sname))
    if pcuda:
     cudavisibledevices=pcuda     
    pcollection = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_vectordbcollectionname".format(sname))    
    if pcollection:
      step9vectordbcollectionname=pcollection     
      doparse("/{}/docs/source/kube.rst".format(sname), ["--kubecollection--;{}".format(pcollection)])

    pgpthost = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_pgpthost".format(sname))
    if pgpthost:
      step9pgpthost=pgpthost

    pgptport = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_pgptport".format(sname))
    if pgptport:
      step9pgptport=pgptport
 
    pprocesstype = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_keyprocesstype".format(sname))
    if pprocesstype:
      step9keyprocesstype=pprocesstype 
    hyperbatch = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_hyperbatch".format(sname))
    if hyperbatch:
      step9hyperbatch=hyperbatch
    psearchterms = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_searchterms".format(sname))
    if psearchterms:
      step9searchterms=psearchterms
      doparse("/{}/docs/source/details.rst".format(sname), ["--searchterms--;{}".format(psearchterms)])
    pstreamall = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_streamall".format(sname))
    if pstreamall:
      step9streamall=pstreamall
      doparse("/{}/docs/source/details.rst".format(sname), ["--streamall--;{}".format(pstreamall[1:])])
    ptemperature = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_temperature".format(sname))
    if ptemperature:
      step9temperature=ptemperature
      doparse("/{}/docs/source/details.rst".format(sname), ["--temperature--;{}".format(ptemperature[1:])])
      doparse("/{}/docs/source/kube.rst".format(sname), ["--kubetemperature--;{}".format(ptemperature[1:])])
     
    pvectorsearchtype = context['ti'].xcom_pull(task_ids='step_9_solution_task_ai',key="{}_vectorsearchtype".format(sname))
    if pvectorsearchtype:
      step9vectorsearchtype=pvectorsearchtype
      doparse("/{}/docs/source/details.rst".format(sname), ["--vectorsearchtype--;{}".format(pvectorsearchtype)])
      doparse("/{}/docs/source/kube.rst".format(sname), ["--kubevectorsearchtype--;{}".format(pvectorsearchtype)])

    ollama= context['ti'].xcom_pull(task_ids='step_9b_solution_task_agenticai',key="{}_ollama-model".format(sname))
    if ollama != None: # Step 9b executing
      step9bollama=ollama
      doparse("/{}/docs/source/details.rst".format(sname), ["--agenticai-ollama-model--;{}".format(ollama)])
      rollback= context['ti'].xcom_pull(task_ids='step_9b_solution_task_agenticai',key="{}_rollbackoffset".format(sname))
      doparse("/{}/docs/source/details.rst".format(sname), ["--agenticai-rollbackoffset--;{}".format(rollback[1:])])
      step9brollback=rollback[1:]

      deletevector= context['ti'].xcom_pull(task_ids='step_9b_solution_task_agenticai',key="{}_deletevectordbcount".format(sname))
      doparse("/{}/docs/source/details.rst".format(sname), ["--agenticai-deletevectordbcount--;{}".format(deletevector[1:])])
      step9bdeletevectordbcount=deletevector[1:]

      vectordbpath= context['ti'].xcom_pull(task_ids='step_9b_solution_task_agenticai',key="{}_vectordbpath".format(sname))
      doparse("/{}/docs/source/details.rst".format(sname), ["--agenticai-vectordbpath--;{}".format(vectordbpath)])
      step9bvectordbpath=vectordbpath

      temp= context['ti'].xcom_pull(task_ids='step_9b_solution_task_agenticai',key="{}_temperature".format(sname))
      doparse("/{}/docs/source/details.rst".format(sname), ["--agenticai-temperature--;{}".format(temp[1:])])
      step9btemperature=temp[1:]

      topicid= context['ti'].xcom_pull(task_ids='step_9b_solution_task_agenticai',key="{}_topicid".format(sname))
      doparse("/{}/docs/source/details.rst".format(sname), ["--agenticai-topicid--;{}".format(topicid[1:])])
      step9btopicid=topicid[1:]

      enabletls= context['ti'].xcom_pull(task_ids='step_9b_solution_task_agenticai',key="{}_enabletls".format(sname))
      doparse("/{}/docs/source/details.rst".format(sname), ["--agenticai-enabletls--;{}".format(enabletls[1:])])
      step9benabletls=enabletls[1:]

      partition= context['ti'].xcom_pull(task_ids='step_9b_solution_task_agenticai',key="{}_partition".format(sname))
      doparse("/{}/docs/source/details.rst".format(sname), ["--agenticai-partition--;{}".format(partition[1:])])
      step9bpartition=partition[1:]

      collection= context['ti'].xcom_pull(task_ids='step_9b_solution_task_agenticai',key="{}_vectordbcollectionname".format(sname))
      doparse("/{}/docs/source/details.rst".format(sname), ["--agenticai-vectordbcollectionname--;{}".format(collection)])
      step9bvectordbcollectionname=collection

      ollamacontainername= context['ti'].xcom_pull(task_ids='step_9b_solution_task_agenticai',key="{}_ollamacontainername".format(sname))
      doparse("/{}/docs/source/details.rst".format(sname), ["--agenticai-ollamacontainername--;{}".format(ollamacontainername)])
      step9bollamacontainername=ollamacontainername

      mainip= context['ti'].xcom_pull(task_ids='step_9b_solution_task_agenticai',key="{}_mainip".format(sname))
      doparse("/{}/docs/source/details.rst".format(sname), ["--agenticai-mainip--;{}".format(mainip)])
      step9bmainip=mainip

      mainport= context['ti'].xcom_pull(task_ids='step_9b_solution_task_agenticai',key="{}_mainport".format(sname))
      doparse("/{}/docs/source/details.rst".format(sname), ["--agenticai-mainport--;{}".format(mainport[1:])])
      step9bmainport=mainport[1:]

      embedding= context['ti'].xcom_pull(task_ids='step_9b_solution_task_agenticai',key="{}_embedding".format(sname))
      doparse("/{}/docs/source/details.rst".format(sname), ["--agenticai-embedding--;{}".format(embedding)])
      step9bembedding=embedding

      agents_topic_prompt= context['ti'].xcom_pull(task_ids='step_9b_solution_task_agenticai',key="{}_agents_topic_prompt".format(sname))
      doparse("/{}/docs/source/details.rst".format(sname), ["--agenticai-agents_topic_prompt--;{}".format(agents_topic_prompt)])
      step9bagents_topic_prompt=agents_topic_prompt

      teamlead_topic= context['ti'].xcom_pull(task_ids='step_9b_solution_task_agenticai',key="{}_teamlead_topic".format(sname))
      doparse("/{}/docs/source/details.rst".format(sname), ["--agenticai-teamlead_topic--;{}".format(teamlead_topic)])
      step9bteamlead_topic=teamlead_topic

      teamleadprompt= context['ti'].xcom_pull(task_ids='step_9b_solution_task_agenticai',key="{}_teamleadprompt".format(sname))
      doparse("/{}/docs/source/details.rst".format(sname), ["--agenticai-teamleadprompt--;{}".format(teamleadprompt)])
      step9bteamleadprompt=teamleadprompt
      step9bteamleadprompt=step9bteamleadprompt.replace('\n',' ').replace("\\n","").strip().replace(";",",").replace("''","")

      supervisor_topic= context['ti'].xcom_pull(task_ids='step_9b_solution_task_agenticai',key="{}_supervisor_topic".format(sname))
      doparse("/{}/docs/source/details.rst".format(sname), ["--agenticai-supervisor_topic--;{}".format(supervisor_topic)])
      step9bsupervisor_topic=supervisor_topic

      supervisorprompt= context['ti'].xcom_pull(task_ids='step_9b_solution_task_agenticai',key="{}_supervisorprompt".format(sname))
      doparse("/{}/docs/source/details.rst".format(sname), ["--agenticai-supervisorprompt--;{}".format(supervisorprompt)])
      step9bsupervisorprompt=supervisorprompt
      step9bsupervisorprompt=step9bsupervisorprompt.replace('\n','').replace("\\n","").strip().replace(";",",").replace("''","")

      agenttoolfunctions= context['ti'].xcom_pull(task_ids='step_9b_solution_task_agenticai',key="{}_agenttoolfunctions".format(sname))
      doparse("/{}/docs/source/details.rst".format(sname), ["--agenticai-agenttoolfunctions--;{}".format(agenttoolfunctions)])      
      step9bagenttoolfunctions=agenttoolfunctions
      step9bagenttoolfunctions=step9bagenttoolfunctions.replace('\n','').replace("\\n","").strip().replace(";",",").replace("''","")


      agent_team_supervisor_topic= context['ti'].xcom_pull(task_ids='step_9b_solution_task_agenticai',key="{}_agent_team_supervisor_topic".format(sname))
      doparse("/{}/docs/source/details.rst".format(sname), ["--agenticai-agent_team_supervisor_topic--;{}".format(agent_team_supervisor_topic)])
      step9bagent_team_supervisor_topic=agent_team_supervisor_topic

      agenttopic= context['ti'].xcom_pull(task_ids='step_9b_solution_task_agenticai',key="{}_agenttopic".format(sname))
      doparse("/{}/docs/source/details.rst".format(sname), ["--agenticai-agenttopic--;{}".format(agenttopic)])
     
      concurrency= context['ti'].xcom_pull(task_ids='step_9b_solution_task_agenticai',key="{}_concurrency".format(sname))
      doparse("/{}/docs/source/details.rst".format(sname), ["--agenticai-concurrency--;{}".format(concurrency[1:])])
      step9bconcurrency=concurrency[1:]

      cuda= context['ti'].xcom_pull(task_ids='step_9b_solution_task_agenticai',key="{}_cuda".format(sname))
      doparse("/{}/docs/source/details.rst".format(sname), ["--agenticai-cuda--;{}".format(cuda[1:])])
      step9bCUDA_VISIBLE_DEVICES=cuda[1:]

      doparse("/{}/docs/source/kube.rst".format(sname), ["--ollamacontainername--;{}".format(ollamacontainername)])
      doparse("/{}/docs/source/kube.rst".format(sname), ["--agenticai-kubeconcur--;{}".format(concurrency[1:])])
      doparse("/{}/docs/source/kube.rst".format(sname), ["--agenticai-kubecollection--;{}".format(collection)])
      doparse("/{}/docs/source/kube.rst".format(sname), ["--agenticai-kubetemperature--;{}".format(temp[1:])])
      doparse("/{}/docs/source/kube.rst".format(sname), ["--agenticai-rollbackoffset--;{}".format(rollback[1:])])
      doparse("/{}/docs/source/kube.rst".format(sname), ["--agenticai-ollama-model--;{}".format(ollama)])
      doparse("/{}/docs/source/kube.rst".format(sname), ["--agenticai-deletevectordbcount--;{}".format(deletevector[1:])])
      doparse("/{}/docs/source/kube.rst".format(sname), ["--agenticai-vectordbpath--;{}".format(vectordbpath)])
      doparse("/{}/docs/source/kube.rst".format(sname), ["--agenticai-topicid--;{}".format(topicid[1:])])
      doparse("/{}/docs/source/kube.rst".format(sname), ["--agenticai-enabletls--;{}".format(enabletls[1:])])
      doparse("/{}/docs/source/kube.rst".format(sname), ["--agenticai-partition--;{}".format(partition[1:])])
      doparse("/{}/docs/source/kube.rst".format(sname), ["--agenticai-vectordbcollectionname--;{}".format(collection)])
      doparse("/{}/docs/source/kube.rst".format(sname), ["--agenticai-ollamacontainername--;{}".format(ollamacontainername)])
      doparse("/{}/docs/source/kube.rst".format(sname), ["--agenticai-mainip--;{}".format(mainip)])
      doparse("/{}/docs/source/kube.rst".format(sname), ["--agenticai-mainport--;{}".format(mainport[1:])])
      doparse("/{}/docs/source/kube.rst".format(sname), ["--agenticai-embedding--;{}".format(embedding)])
      doparse("/{}/docs/source/kube.rst".format(sname), ["--agenticai-agents_topic_prompt--;{}".format(agents_topic_prompt.strip().replace('\n','').replace("\\n","").replace("'","").replace(";",","))])
      doparse("/{}/docs/source/kube.rst".format(sname), ["--agenticai-teamlead_topic--;{}".format(teamlead_topic)])
      doparse("/{}/docs/source/kube.rst".format(sname), ["--agenticai-teamleadprompt--;{}".format(teamleadprompt.strip().replace('\n','').replace("\\n","").replace("'","").replace(";",",") )])
      doparse("/{}/docs/source/kube.rst".format(sname), ["--agenticai-supervisor_topic--;{}".format(supervisor_topic)])
      doparse("/{}/docs/source/kube.rst".format(sname), ["--agenticai-supervisorprompt--;{}".format(supervisorprompt.strip().replace('\n','').replace("\\n","").replace("'","").replace(";",","))])
      doparse("/{}/docs/source/kube.rst".format(sname), ["--agenticai-agenttoolfunctions--;{}".format(agenttoolfunctions.strip().replace('\n','').replace("\\n","").replace("'","").replace(";","=="))])
      doparse("/{}/docs/source/kube.rst".format(sname), ["--agenticai-agent_team_supervisor_topic--;{}".format(agent_team_supervisor_topic)])

    ebuf=""
    if 'dockerenv' in default_args:
     if default_args['dockerenv'] != '':
       buf=default_args['dockerenv']
       darr = buf.split("***")
       ebuf="\n"
       for d in darr:          
          v=d.split("=")
          if len(v)>1:
            if 'jsoncriteria' in v[0].strip():
              d=d[d.index("=")+1:]
              ebuf = ebuf + '          --env ' + v[0].strip() + '=\"' + d + '\" \\ \n'             
            else:
              ebuf = ebuf + '          --env ' + v[0].strip() + '=\"' + v[1].strip() + '\" \\ \n'
          else: 
            ebuf = ebuf + '          --env ' + v[0].strip() + '=' + ' \\ \n'
       ebuf = ebuf[:-1]
     if default_args['dockerinstructions'] != '':
       doparse("/{}/docs/source/operating.rst".format(sname), ["--dockerinstructions--;{}".format(default_args['dockerinstructions'])])     
     else:
       doparse("/{}/docs/source/operating.rst".format(sname), ["--dockerinstructions--;{}".format("Please ask the developer of this solution.")])     
     
    if len(CLIENTPORT) > 1:
      doparse("/{}/docs/source/operating.rst".format(sname), ["--clientport--;{}".format(TMLCLIENTPORT[1:])])
      dockerrun = """docker run -d --net=host -p {}:{} -p {}:{} -p {}:{} -p {}:{} \\
          --env TSS=0 \\
          --env SOLUTIONNAME={} \\
          --env SOLUTIONDAG={} \\
          --env GITUSERNAME=<Enter Github Username> \\
          --env GITPASSWORD='<Enter Github Password>' \\          
          --env GITREPOURL=<Enter Github Repo URL> \\
          --env SOLUTIONEXTERNALPORT={} \\
          -v /var/run/docker.sock:/var/run/docker.sock:z  \\
          -v /your_localmachine/foldername:/rawdata:z \\
          --env CHIP={} \\
          --env SOLUTIONAIRFLOWPORT={}  \\
          --env SOLUTIONVIPERVIZPORT={} \\
          --env DOCKERUSERNAME='' \\
          --env CLIENTPORT={}  \\
          --env EXTERNALPORT={} \\
          --env KAFKABROKERHOST=127.0.0.1:9092 \\          
          --env KAFKACLOUDUSERNAME='<Enter API key>' \\
          --env KAFKACLOUDPASSWORD='<Enter API secret>' \\          
          --env SASLMECHANISM=PLAIN \\          
          --env VIPERVIZPORT={} \\
          --env MQTTUSERNAME='' \\
          --env MQTTPASSWORD='' \\          
          --env AIRFLOWPORT={}  \\
          --env READTHEDOCS='<Enter Readthedocs token>' \\{} 
          {}""".format(solutionexternalport[1:],solutionexternalport[1:],
                          solutionairflowport[1:],solutionairflowport[1:],solutionvipervizport[1:],solutionvipervizport[1:],
                          TMLCLIENTPORT[1:],TMLCLIENTPORT[1:],sname,sd,
                          solutionexternalport[1:],chipmain,
                          solutionairflowport[1:],solutionvipervizport[1:],TMLCLIENTPORT[1:],
                          externalport[1:],vipervizport[1:],airflowport[1:],ebuf,containername)       
    else:
      doparse("/{}/docs/source/operating.rst".format(sname), ["--clientport--;Not Applicable"])
      dockerrun = """docker run -d --net=host -p {}:{} -p {}:{} -p {}:{} \\
          --env TSS=0 \\
          --env SOLUTIONNAME={} \\
          --env SOLUTIONDAG={} \\
          --env GITUSERNAME=<Enter Github Username> \\
          --env GITPASSWORD='<Enter Github Password>' \\          
          --env GITREPOURL=<Enter Github Repo URL> \\
          --env SOLUTIONEXTERNALPORT={} \\
          -v /var/run/docker.sock:/var/run/docker.sock:z \\
          -v /your_localmachine/foldername:/rawdata:z \\
          --env CHIP={} \\
          --env SOLUTIONAIRFLOWPORT={} \\
          --env SOLUTIONVIPERVIZPORT={} \\
          --env DOCKERUSERNAME='' \\
          --env EXTERNALPORT={} \\
          --env KAFKABROKERHOST=127.0.0.1:9092 \\                    
          --env KAFKACLOUDUSERNAME='<Enter API key>' \\
          --env KAFKACLOUDPASSWORD='<Enter API secret>' \\          
          --env SASLMECHANISM=PLAIN \\                    
          --env VIPERVIZPORT={} \\
          --env MQTTUSERNAME='' \\
          --env MQTTPASSWORD='' \\          
          --env AIRFLOWPORT={} \\
          --env READTHEDOCS='<Enter Readthedocs token>' \\{} 
          {}""".format(solutionexternalport[1:],solutionexternalport[1:],
                          solutionairflowport[1:],solutionairflowport[1:],solutionvipervizport[1:],solutionvipervizport[1:],
                          sname,sd,solutionexternalport[1:],chipmain,
                          solutionairflowport[1:],solutionvipervizport[1:],
                          externalport[1:],vipervizport[1:],airflowport[1:],ebuf,containername)
        
   # dockerrun = re.escape(dockerrun) 
    v=subprocess.call(["sed", "-i", "-e",  "s/--dockerrun--/{}/g".format(dockerrun), "/{}/docs/source/operating.rst".format(sname)])

    if istss1==1:
      doparse("/{}/docs/source/operating.rst".format(sname), ["--dockerrun--;{}".format(dockerrun),"--dockercontainer--;{} ({})".format(containername, hurl)])
      doparse("/{}/docs/source/details.rst".format(sname), ["--dockerrun--;{}".format(dockerrun),"--dockercontainer--;{} ({})".format(containername, hurl)])   
    else:
      try:
        with open("/tmux/step1solutionold.txt", "r") as f:
          msname=f.read()
          mbuf="Refer to the original solution container and documenation here: https://{}.readthedocs.io/en/latest/operating.html".format(msname.strip())
          doparse("/{}/docs/source/operating.rst".format(sname), ["--dockerrun--;{}".format(dockerrun),"--dockercontainer--;{}".format(mbuf)])
      except Exception as e:
        pass
       
    step9rollbackoffset=-1
    step9llmmodel=''
    step9embedding=''
    step9vectorsize='' 
    if pgptcontainername != None:
        if os.environ['TSS'] == "1":
           privategptrun = "docker run -d -p {}:{} --net=host --gpus all -v /var/run/docker.sock:/var/run/docker.sock:z --env PORT={} --env TSS=1 --env GPU=1 --env COLLECTION={} --env WEB_CONCURRENCY={} --env CUDA_VISIBLE_DEVICES={} --env TOKENIZERS_PARALLELISM=false --env temperature={} --env vectorsearchtype=\"{}\" --env contextwindowsize={} --env vectordimension={} {}".format(pgptport[1:],pgptport[1:],pgptport[1:],pcollection,pconcurrency[1:],pcuda[1:],ptemperature[1:], pvectorsearchtype, pcontextwindowsize[1:], pvectordimension[1:],pgptcontainername)
        else:
           privategptrun = "docker run -d -p {}:{} --net=host --gpus all -v /var/run/docker.sock:/var/run/docker.sock:z --env PORT={} --env TSS=0 --env GPU=1 --env COLLECTION={} --env WEB_CONCURRENCY={} --env CUDA_VISIBLE_DEVICES={} --env TOKENIZERS_PARALLELISM=false --env temperature={} --env vectorsearchtype=\"{}\" --env contextwindowsize={} --env vectordimension={} {}".format(pgptport[1:],pgptport[1:],pgptport[1:],pcollection,pconcurrency[1:],pcuda[1:],ptemperature[1:], pvectorsearchtype, pcontextwindowsize[1:], pvectordimension[1:],pgptcontainername)
         
        step9llmmodel='Refer to: https://tml.readthedocs.io/en/latest/genai.html'
        step9embedding='Refer to: https://tml.readthedocs.io/en/latest/genai.html'
        step9vectorsize='Refer to: https://tml.readthedocs.io/en/latest/genai.html'

        doparse("/{}/docs/source/details.rst".format(sname), ["--llmmodel--;{}".format(step9llmmodel)])
        doparse("/{}/docs/source/details.rst".format(sname), ["--embedding--;{}".format(step9embedding)])
        doparse("/{}/docs/source/details.rst".format(sname), ["--vectorsize--;{}".format(step9vectorsize)])
         
        doparse("/{}/docs/source/details.rst".format(sname), ["--pgptcontainername--;{}".format(pgptcontainername),"--privategptrun--;{}".format(privategptrun)])

        qdrantcontainer = "qdrant/qdrant"
        qdrantrun = "docker run -d -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage:z qdrant/qdrant"
        doparse("/{}/docs/source/details.rst".format(sname), ["--qdrantcontainer--;{}".format(qdrantcontainer),"--qdrantrun--;{}".format(qdrantrun)])

        doparse("/{}/docs/source/details.rst".format(sname), ["--consumefrom--;{}".format(pconsumefrom)])
        doparse("/{}/docs/source/details.rst".format(sname), ["--pgpt_data_topic--;{}".format(pgpt_data_topic)])
        doparse("/{}/docs/source/details.rst".format(sname), ["--vectordbcollectionname--;{}".format(pcollection)])
        doparse("/{}/docs/source/details.rst".format(sname), ["--offset--;{}".format(poffset[1:])])
        doparse("/{}/docs/source/details.rst".format(sname), ["--rollbackoffset--;{}".format(prollbackoffset[1:])])
        step9rollbackoffset=prollbackoffset[1:]
        doparse("/{}/docs/source/details.rst".format(sname), ["--topicid--;{}".format(ptopicid[1:])])
        doparse("/{}/docs/source/details.rst".format(sname), ["--enabletls--;{}".format(penabletls[1:])])
        doparse("/{}/docs/source/details.rst".format(sname), ["--partition--;{}".format(ppartition[1:])])
        pprompt=pprompt.replace("\\n"," ")
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
    
    snamerp=sname.replace("_","-")
    rbuf = "https://{}.readthedocs.io".format(sname)
    doparse("/{}/docs/source/details.rst".format(sname), ["--readthedocs--;{}".format(rbuf)])
    
    ############# VIZ URLS
    
    vizurl = "http:\/\/localhost:{}\/{}?topic={}\&offset={}\&groupid=\&rollbackoffset={}\&topictype=prediction\&append={}\&secure={}".format(solutionvipervizport[1:],dashboardhtml,topic,offset[1:],rollbackoffset[1:],append[1:],secure[1:])
    vizurlkube = "http://localhost:{}/{}?topic={}&offset={}&groupid=&rollbackoffset={}&topictype=prediction&append={}&secure={}".format(solutionvipervizport[1:],dashboardhtml,topic,offset[1:],rollbackoffset[1:],append[1:],secure[1:])
    if 'gRPC' in PRODUCETYPE:
      vizurlkubeing = "http://tml.tss2/viz/{}?topic={}&offset={}&groupid=&rollbackoffset={}&topictype=prediction&append={}&secure={}".format(dashboardhtml,topic,offset[1:],rollbackoffset[1:],append[1:],secure[1:])
    else:
      vizurlkubeing = "http://tml.tss/viz/{}?topic={}&offset={}&groupid=&rollbackoffset={}&topictype=prediction&append={}&secure={}".format(dashboardhtml,topic,offset[1:],rollbackoffset[1:],append[1:],secure[1:])
 
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
                    " -v /your_localmachine/foldername:/rawdata:z " \
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
                    " \-\-env UPDATE=1 " \
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
    if pgptcontainername != None and ollama != None:
            if '127.0.0.1' in brokerhost:            
              kcmd = "kubectl apply -f kafka.yml -f secrets.yml -f mysql-storage.yml -f mysql-db-deployment.yml -f qdrant.yml -f privategpt.yml -f ollama.yml -f {}.yml".format(sname)
            else:
              kcmd = "kubectl apply -f secrets.yml -f mysql-storage.yml -f mysql-db-deployment.yml -f qdrant.yml -f privategpt.yml -f ollama.yml -f {}.yml".format(sname)
             
            doparse("/{}/docs/source/kube.rst".format(sname), ["--kubectl--;{}".format(kcmd)])      
    elif pgptcontainername != None:
            if '127.0.0.1' in brokerhost:            
              kcmd = "kubectl apply -f kafka.yml -f secrets.yml -f mysql-storage.yml -f mysql-db-deployment.yml -f qdrant.yml -f privategpt.yml -f {}.yml".format(sname)
            else:
              kcmd = "kubectl apply -f secrets.yml -f mysql-storage.yml -f mysql-db-deployment.yml -f qdrant.yml -f privategpt.yml -f {}.yml".format(sname)
             
            doparse("/{}/docs/source/kube.rst".format(sname), ["--kubectl--;{}".format(kcmd)])
    elif ollama != None:
            if '127.0.0.1' in brokerhost:
              kcmd = "kubectl apply -f kafka.yml -f secrets.yml -f mysql-storage.yml -f mysql-db-deployment.yml -f {}.yml -f ollama.yml".format(sname)
            else: 
              kcmd = "kubectl apply -f secrets.yml -f mysql-storage.yml -f mysql-db-deployment.yml -f {}.yml -f ollama.yml".format(sname)
            
            doparse("/{}/docs/source/kube.rst".format(sname), ["--kubectl--;{}".format(kcmd)])          
    else:
            if '127.0.0.1' in brokerhost:
              kcmd = "kubectl apply -f kafka.yml -f secrets.yml -f mysql-storage.yml -f mysql-db-deployment.yml -f {}.yml".format(sname)
            else: 
              kcmd = "kubectl apply -f secrets.yml -f mysql-storage.yml -f mysql-db-deployment.yml -f {}.yml".format(sname)
            
            doparse("/{}/docs/source/kube.rst".format(sname), ["--kubectl--;{}".format(kcmd)])
  
      
    if maxrows4:
      step4maxrows=maxrows4[1:]
    else:
      step4maxrows=-1

    if maxrows4b: 
      step4bmaxrows=maxrows4b[1:]
    else: 
      step4bmaxrows=-1 

    if maxrows4c: 
      step4cmaxrows=maxrows4c[1:]
    else: 
      step4cmaxrows=-1 

    if rollbackoffsets:
      step5rollbackoffsets=rollbackoffsets[1:]
    else:
      step5rollbackoffsets=-1

    if maxrows:
      step6maxrows=maxrows[1:]
    else:
      step6maxrows=-1

    kubebroker='kafka-service:9092' 
    if 'KUBEBROKERHOST' in os.environ:
       kubebroker = os.environ['KUBEBROKERHOST']
    kafkabroker='127.0.0.1:9092' 
    if 'KAFKABROKERHOST' in os.environ:
       kafkabroker = os.environ['KAFKABROKERHOST']
     
    step1solutiontitle=stitle
    step1description=sdesc
    try:
      with open("/tmux/cname.txt", "r") as f:
        containername=f.read()
    except Exception as e:   
        pass

#    step9bagenttoolfunctions=""
    step9bagents_topic_prompt=step9bagents_topic_prompt.replace("\\n","").replace('\n','').strip().replace(";","==").replace("'","")
    if len(CLIENTPORT) > 1:
      kcmd2=tsslogging.genkubeyaml(sname,containername,TMLCLIENTPORT[1:],solutionairflowport[1:],solutionvipervizport[1:],solutionexternalport[1:],
                       sd,os.environ['GITUSERNAME'],os.environ['GITREPOURL'],chipmain,os.environ['DOCKERUSERNAME'],
                       externalport[1:],kafkacloudusername,mqttusername,airflowport[1:],vipervizport[1:],
                       step4maxrows,step4bmaxrows,step5rollbackoffsets,step6maxrows,step1solutiontitle,step1description,
                       step9rollbackoffset,kubebroker,kafkabroker,PRODUCETYPE,step9prompt,step9context,step9keyattribute,step9keyprocesstype,
                       step9hyperbatch[1:],step9vectordbcollectionname,step9concurrency[1:],cudavisibledevices[1:],
                       step9docfolder,step9docfolderingestinterval[1:],step9useidentifierinprompt[1:],step5processlogic,
                       step5independentvariables,step9searchterms,step9streamall[1:],step9temperature[1:],step9vectorsearchtype,
                       step9llmmodel,step9embedding,step9vectorsize,step4cmaxrows,step4crawdatatopic,step4csearchterms,step4crememberpastwindows[1:],
                       step4cpatternwindowthreshold[1:],step4crtmsstream,projectname,step4crtmsscorethreshold[1:],step4cattackscorethreshold[1:],
                       step4cpatternscorethreshold[1:],step4clocalsearchtermfolder,step4clocalsearchtermfolderinterval[1:],step4crtmsfoldername,
                       step3localfileinputfile,step3localfiledocfolder,step4crtmsmaxwindows[1:],step9pcontextwindowsize[1:],
                       step9pgptcontainername,step9pgpthost,step9pgptport[1:],step9vectordimension[1:],
                       step2raw_data_topic,step2preprocess_data_topic,step4raw_data_topic,step4preprocesstypes,
                       step4jsoncriteria,step4ajsoncriteria,step4amaxrows[1:],step4apreprocesstypes,step4araw_data_topic,
                       step4apreprocess_data_topic,step4bpreprocesstypes,step4bjsoncriteria,step4braw_data_topic,
                       step4bpreprocess_data_topic,step4preprocess_data_topic,
                       step9brollback,
                       step9bdeletevectordbcount,
                       step9bvectordbpath,
                       step9btemperature,
                       step9bvectordbcollectionname,
                       step9bollamacontainername,
                       step9bCUDA_VISIBLE_DEVICES,
                       step9bmainip,
                       step9bmainport,
                       step9bembedding,
                       step9bagents_topic_prompt,
                       step9bteamlead_topic,
                       step9bteamleadprompt,
                       step9bsupervisor_topic,
                       step9bagenttoolfunctions,
                       step9bagent_team_supervisor_topic)
    else: 
      kcmd2=tsslogging.genkubeyamlnoext(sname,containername,TMLCLIENTPORT[1:],solutionairflowport[1:],solutionvipervizport[1:],solutionexternalport[1:],
                       sd,os.environ['GITUSERNAME'],os.environ['GITREPOURL'],chipmain,os.environ['DOCKERUSERNAME'],
                       externalport[1:],kafkacloudusername,mqttusername,airflowport[1:],vipervizport[1:],
                       step4maxrows,step4bmaxrows,step5rollbackoffsets,step6maxrows,step1solutiontitle,step1description,step9rollbackoffset,
                       kubebroker,kafkabroker,step9prompt,step9context,step9keyattribute,step9keyprocesstype,
                       step9hyperbatch[1:],step9vectordbcollectionname,step9concurrency[1:],cudavisibledevices[1:],
                       step9docfolder,step9docfolderingestinterval[1:],step9useidentifierinprompt[1:],step5processlogic,
                       step5independentvariables,step9searchterms,step9streamall[1:],step9temperature[1:],step9vectorsearchtype,
                       step9llmmodel,step9embedding,step9vectorsize,step4cmaxrows,step4crawdatatopic,step4csearchterms,step4crememberpastwindows[1:],
                       step4cpatternwindowthreshold[1:],step4crtmsstream,projectname,step4crtmsscorethreshold[1:],step4cattackscorethreshold[1:],
                       step4cpatternscorethreshold[1:],step4clocalsearchtermfolder,step4clocalsearchtermfolderinterval[1:],step4crtmsfoldername,
                       step3localfileinputfile,step3localfiledocfolder,step4crtmsmaxwindows[1:],step9pcontextwindowsize[1:],
                       step9pgptcontainername,step9pgpthost,step9pgptport[1:],step9vectordimension[1:],
                       step2raw_data_topic,step2preprocess_data_topic,step4raw_data_topic,step4preprocesstypes,
                       step4jsoncriteria,step4ajsoncriteria,step4amaxrows[1:],step4apreprocesstypes,step4araw_data_topic,
                       step4apreprocess_data_topic,step4bpreprocesstypes,step4bjsoncriteria,step4braw_data_topic,
                       step4bpreprocess_data_topic,step4preprocess_data_topic,
                       step9brollback,
                       step9bdeletevectordbcount,
                       step9bvectordbpath,
                       step9btemperature,
                       step9bvectordbcollectionname,
                       step9bollamacontainername,
                       step9bCUDA_VISIBLE_DEVICES,
                       step9bmainip,
                       step9bmainport,
                       step9bembedding,
                       step9bagents_topic_prompt,
                       step9bteamlead_topic,
                       step9bteamleadprompt,
                       step9bsupervisor_topic,
                       step9bagenttoolfunctions,
                       step9bagent_team_supervisor_topic)
                                                                              
    doparse("/{}/docs/source/kube.rst".format(sname), ["--solutionnamecode--;{}".format(kcmd2)])

    kpfwd="kubectl port-forward deployment/{} {}:{}".format(sname,solutionvipervizport[1:],solutionvipervizport[1:])
    doparse("/{}/docs/source/kube.rst".format(sname), ["--kube-portforward--;{}".format(kpfwd)])
    doparse("/{}/docs/source/kube.rst".format(sname), ["--visualizationurl--;{}".format(vizurlkube)])
    doparse("/{}/docs/source/kube.rst".format(sname), ["--visualizationurling--;{}".format(vizurlkubeing)])
    doparse("/{}/docs/source/kube.rst".format(sname), ["--nginxname--;{}".format(sname)])

    if len(CLIENTPORT) > 1:
      if 'gRPC' in PRODUCETYPE:
        kcmd3=tsslogging.ingressgrpc(sname) 
      else: 
        kcmd3=tsslogging.ingress(sname) 
    else:   # localfile being processed
      kcmd3=tsslogging.ingressnoext(sname)
     
    doparse("/{}/docs/source/kube.rst".format(sname), ["--ingress--;{}".format(kcmd3)])

    ###########################
    try:
      tmuxwindows = "None"  
      with open("/tmux/pythonwindows_{}.txt".format(sname), 'r', encoding='utf-8') as file: 
        data = file.readlines() 
        data.append("viper-produce")
        data.append("viper-preprocess")
        data.append("viper-preprocess-pgpt")
        data.append("viper-preprocess-agenticai")        
        data.append("viper-ml")
        data.append("viper-predict")
        tmuxwindows = ", ".join(data)
        tmuxwindows = tmuxwindows.replace("\n","")
        print("tmuxwindows=",tmuxwindows)
    except Exception as e:
       pass 

    doparse("/{}/docs/source/operating.rst".format(sname), ["--tmuxwindows--;{}".format(tmuxwindows)])
    #try:
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
    
    
    rtd = context['ti'].xcom_pull(task_ids='step_10_solution_task_document',key="{}_RTD".format(sname))
     #try:
    sp=f"{sname}/docs/source"
    orepo=tsslogging.getrepo()
    op=f"/{orepo}/tml-airflow/dags/tml-solutions/{projectname}" 
    files,opath=tsslogging.dorst2pdf(sp,op)
    tsslogging.mergepdf(opath,files,f"{sname}")
  
    gb="https://github.com/{}/{}/tree/main/tml-airflow/dags/tml-solutions/{}/pdf_documentation/{}.pdf".format(os.environ['GITUSERNAME'],tsslogging.getrepo(),projectname,sname)
    print("INFO: Your PDF Documentation will be found here: {}".format(gb))

    # gityml
    gityml="https://github.com/{}/{}/tree/main/tml-airflow/dags/tml-solutions/{}/ymls/{}".format(os.environ['GITUSERNAME'],tsslogging.getrepo(),projectname,sname)
    doparse("/{}/docs/source/kube.rst".format(sname), ["--gityml--;{}".format(gityml)])

    oppt=copyymls(projectname,sname,kcmd3,kcmd2)
    updateollamaandpgpt(oppt,step9bollamacontainername,step9bconcurrency,step9bvectordbcollectionname,step9btemperature,step9brollback,step9bollama,step9bdeletevectordbcount,step9bvectordbpath,step9btopicid,step9benabletls,step9bpartition,step9bmainip,
                       step9bmainport,step9bembedding,step9bagents_topic_prompt,step9bteamlead_topic,step9bteamleadprompt,step9bsupervisor_topic,step9bsupervisorprompt,step9bagenttoolfunctions,step9bagent_team_supervisor_topic,
                       pvectorsearchtype,ptemperature,pcollection,pconcurrency,pvectordimension,pcontextwindowsize,pmainmodel,pmainembedding,pgptcontainername)
  
    subprocess.call("/tmux/gitp.sh {} 'For solution details GOTO: https://{}.readthedocs.io'".format(sname,snamertd), shell=True)

     #except Exception as e:
      # print("Error=",e) 
    try:  
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
     print("INFO: Your Documentation will be found here: https://{}.readthedocs.io/en/latest".format(snamertd))
    except Exception as e:
     print("ERROR=",e)
