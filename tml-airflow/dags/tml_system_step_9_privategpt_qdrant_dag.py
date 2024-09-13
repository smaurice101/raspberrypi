from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime
from airflow.decorators import dag, task
import os 
import tsslogging
import sys
import time
import maadstml
import subprocess

sys.dont_write_bytecode = True

######################################################USER CHOSEN PARAMETERS ###########################################################
default_args = {
 'owner': 'Sebastian Maurice',   # <<< *** Change as needed   
 'pgptcontainername' : 'maadsdocker/tml-privategpt-no-gpu-amd64',  # enter a valid container https://hub.docker.com/r/maadsdocker/tml-privategpt-no-gpu-amd64
 'rollbackoffset' : '2',  # <<< *** Change as needed     
 'offset' : '-1',   
 'enabletls' : '1',   
 'brokerhost' : '', # <<< *** Leave as is   
 'brokerport' : '-999', # <<< *** Leave as is    
 'microserviceid' : '',  # change as needed   
 'topicid' : '-999', # leave as is  
 'delay' : '100', # change as needed   
 'companyname' : 'otics',  # <<< *** Change as needed   
 'consumerid' : 'streamtopic',  # <<< *** Leave as is  
 'consumefrom' : 'iot-preprocess',    # <<< *** Change as needed   
 'pgpt_data_topic' : 'cisco-network-privategpt',   
 'producerid' : 'private-gpt',   # <<< *** Leave as is  
 'identifier' : 'This is analysing TML output with privategpt'
 'pgpthost': 'http://127.0.0.1', # PrivateGPT container listening on this host
 'pgptport' : '8001', # PrivateGPT listening on this port  
 'preprocesstype' : '',
 'partition' : '-1',
 'prompt': '', # Enter your prompt here
 'context' : '', # what is this data about? Provide context to PrivateGPT   
 'jsonkeytogather' : '', # enter key you want to gather data from to analyse with PrivateGpt   
 'keyattribute' : '',   
}

############################################################### DO NOT MODIFY BELOW ####################################################
# Instantiate your DAG
@dag(dag_id="tml_system_step_9_privategpt_qdrant_dag", default_args=default_args, tags=["tml_system_step_9_privategpt_qdrant_dag"], schedule=None,  catchup=False)
def startaiprocess():
    # Define tasks
    def empty():
        pass
dag = startaiprocess()    

VIPERTOKEN=""
VIPERHOST=""
VIPERPORT=""
HTTPADDR=""
maintopic =  default_args['consumefrom']  
mainproducerid = default_args['producerid']   

def pgptchat(prompt,context,docfilter,port,includesources,ip,endpoint):
  
  response=maadstml.pgptchat(prompt,context,docfilter,port,includesources,ip,endpoint)
  return response
    
def consumetopicdata(maintopic,rollback):
    
      maintopic = default_args['consumefrom']
      rollbackoffsets = int(default_args['rollbackoffset'])
      enabletls = int(default_args['enabletls'])
      consumerid=default_args['consumerid']
      companyname=default_args['companyname']
      offset = int(default_args['offset'])  
      brokerhost = default_args['brokerhost']
      brokerport = int(default_args['brokerport'])
      microserviceid = default_args['microserviceid']
      topicid = default_args['topicid']
      preprocesstype = default_args['preprocesstype']
      delay = int(default_args['delay'])
      partition = int(default_args['partition'])
  
      result=maadstml.viperconsumefromtopic(VIPERTOKEN,VIPERHOST,VIPERPORT,maintopic,
                  consumerid,companyname,partition,enabletls,delay,
                  offset, brokerhost,brokerport,microserviceid,
                  topicid,rollbackoffsets,preprocesstype)

#      print(result)
      return result

def gatherdataforprivategpt(result):
   
   privategptmessage = [] 
   prompt = default_args['prompt']
   jsonkeytogather = default_args['jsonkeytogather']
   attribute = default_args['keyattribute']
    
   res=json.loads(result,strict='False')
   message = "" 
    
   if jsonkeytogather == '':
     tsslogging.tsslogit("PrivateGPT DAG jsonkeytogather is empty in {} {}".format(os.path.basename(__file__),e), "ERROR" )                     
     tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")        
     return
    
   for r in res['StreamTopicDetails']['TopicReads']:       
       if jsonkeytogather == 'Identifier':
         identarr=r['Identifier'].split("~")   
         try:   
           for d in r['RawData']:
             message = message  + str(d) + '<br>'
           message = message + "<br>{}".format(prompt)
           privategptmessage.append(message)
         except Excepption as e: 
           tsslogging.tsslogit("PrivateGPT DAG in {} {}".format(os.path.basename(__file__),e), "ERROR" )                     
           tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")    
           break 
       else:
         buf = r[jsonkeytogather] 
         message = message  + buf + '<br>'
         privategptmessage.append(message)
        
   return privategptmessage          
        

def sendtoprivategpt(maindata,maintopic):

   pgptendpoint="/v1/completions"

   for m in maindata:
        print(m)
        response=pgptchat(m,False,"",mainport,False,mainip,pgptendpoint)
        # Produce data to Kafka
        response = response[:-1] + "," + "\"prompt\":\"" + m + "\"}"
        if 'ERROR:' not in response:
          producegpttokafka(response,maintopic)
          print("response=",response)
            
def startprivategpt(**context):
       sd = context['dag'].dag_id
       sname=context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_solutionname".format(sd))
       
       VIPERTOKEN = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERTOKEN".format(sname))
       VIPERHOST = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERHOSTPREPROCESSPGPT".format(sname))
       VIPERPORT = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERPORTPREPROCESSPGPT".format(sname))
       HTTPADDR = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_HTTPADDR".format(sname))

       ti = context['task_instance']
       ti.xcom_push(key="{}_consumefrom".format(sname), value=default_args['consumefrom'])
       ti.xcom_push(key="{}_pgpt_data_topic".format(sname), value=default_args['pgpt_data_topic'])
       ti.xcom_push(key="{}_pgptcontainer".format(sname), value="_{}".format(default_args['pgptcontainername']))
       ti.xcom_push(key="{}_offset".format(sname), value="_{}".format(default_args['offset']))
       ti.xcom_push(key="{}_rollbackoffset".format(sname), value="_{}".format(default_args['rollbackoffset']))
        
       ti.xcom_push(key="{}_topicid".format(sname), value="_{}".format(default_args['topicid']))
       ti.xcom_push(key="{}_enabletls".format(sname), value="_{}".format(default_args['enabletls']))
       ti.xcom_push(key="{}_partition".format(sname), value=default_args['partition'])

       ti.xcom_push(key="{}_prompt".format(sname), value=default_args['prompt'])
       ti.xcom_push(key="{}_context".format(sname), value=default_args['context']) 
       ti.xcom_push(key="{}_jsonkeytogather".format(sname), value=default_args['jsonkeytogather'])

    
    
       repo=tsslogging.getrepo() 
       if sname != '_mysolution_':
        fullpath="/{}/tml-airflow/dags/tml-solutions/{}/{}".format(repo,sname,os.path.basename(__file__))  
       else:
         fullpath="/{}/tml-airflow/dags/{}".format(repo,os.path.basename(__file__))  
            
       wn = windowname('ml',sname,sd)     
       subprocess.run(["tmux", "new", "-d", "-s", "{}".format(wn)])
       subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "cd /Viper-preprocess-pgpt", "ENTER"])
       subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "python {} 1 {} {}{} {}".format(fullpath,VIPERTOKEN, HTTPADDR, VIPERHOST, VIPERPORT[1:]), "ENTER"])        

if __name__ == '__main__':
    if len(sys.argv) > 1:
       if sys.argv[1] == "1":          
        repo=tsslogging.getrepo()
        try:
          tsslogging.tsslogit("PrivateGPT Step 9 DAG in {}".format(os.path.basename(__file__)), "INFO" )                     
          tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")    
        except Exception as e:
            #git push -f origin main
            os.chdir("/{}".format(repo))
            subprocess.call("git push -f origin main", shell=True)
            
        VIPERTOKEN = sys.argv[2]
        VIPERHOST = sys.argv[3]
        VIPERPORT = sys.argv[4]        
    
        while True:
         try:     
             # Get preprocessed data from Kafka
             result = consumetopicdata()

             # Format the preprocessed data for PrivateGPT
             maindata = gatherdataforprivategpt(result)

             # Send the data to PrivateGPT and produce to Kafka
             sendtoprivategpt(maindata,pgpttopic)
             time.sleep(1)
         except Exception as e:
          tsslogging.tsslogit("PrivateGPT Step 9 DAG in {} {}".format(os.path.basename(__file__),e), "ERROR" )                     
          tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")    
          break
