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
import random
import json

sys.dont_write_bytecode = True

######################################################USER CHOSEN PARAMETERS ###########################################################
default_args = {
 'owner': 'Sebastian Maurice',   # <<< *** Change as needed
 'pgptcontainername' : 'maadsdocker/tml-privategpt-with-gpu-nvidia-amd64', #'maadsdocker/tml-privategpt-no-gpu-amd64',  # enter a valid container https://hub.docker.com/r/maadsdocker/tml-privategpt-no-gpu-amd64
 'rollbackoffset' : '2',  # <<< *** Change as needed
 'offset' : '-1', # leave as is
 'enabletls' : '1', # change as needed
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
 'identifier' : 'This is analysing TML output with privategpt',
 'pgpthost': 'http://127.0.0.1', # PrivateGPT container listening on this host
 'pgptport' : '8001', # PrivateGPT listening on this port
 'preprocesstype' : '', # Leave as is 
 'partition' : '-1', # Leave as is 
 'prompt': 'Do the device data show any malfunction or defects?', # Enter your prompt here
 'context' : 'This is IoT data from devices. The data are \
anomaly probabilities for each IoT device. If voltage or current \
probabilities are low, it is likely the device is not working properly.', # what is this data about? Provide context to PrivateGPT
 'jsonkeytogather' : 'hyperprediction', # enter key you want to gather data from to analyse with PrivateGpt i.e. Identifier or hyperprediction
 'keyattribute' : 'Voltage,current', # change as needed  
 'keyprocesstype' : 'anomprob',  # change as needed
 'hyperbatch' : '0', # Set to 1 if you want to batch all of the hyperpredictions and sent to chatgpt, set to 0, if you want to send it one by one   
 'vectordbcollectionname' : 'tml', # change as needed
 'concurrency' : '1', # change as needed Leave at 1
 'CUDA_VISIBLE_DEVICES' : '0' # change as needed
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

def stopcontainers():

   subprocess.call("docker image ls > gptfiles.txt", shell=True)
   with open('gptfiles.txt', 'r', encoding='utf-8') as file:
        data = file.readlines()
        r=0
        for d in data:
          darr = d.split(" ")
          if '-privategpt-' in darr[0]:
            buf="docker stop $(docker ps -q --filter ancestor={} )".format(darr[0])
            print(buf)
            subprocess.call(buf, shell=True)

def startpgptcontainer():
      collection = default_args['vectordbcollectionname']
      concurrency = default_args['concurrency']
      pgptcontainername = default_args['pgptcontainername']
      pgptport = int(default_args['pgptport'])
      cuda = int(default_args['CUDA_VISIBLE_DEVICES'])
      stopcontainers()
#      buf="docker stop $(docker ps -q --filter ancestor={} )".format(pgptcontainername)
 #     subprocess.call(buf, shell=True)
      time.sleep(10)
      buf = "docker run -d -p {}:{} --net=host --gpus all --env PORT={} --env GPU=1 --env COLLECTION={} --env WEB_CONCURRENCY={} --env CUDA_VISIBLE_DEVICES={} {}".format(pgptport,pgptport,pgptport,collection,concurrency,cuda,pgptcontainername)
      v=subprocess.call(buf, shell=True)
      return v,buf
 
def qdrantcontainer():
    v=0
    buf=""
    if int(default_args['concurrency']) > 1:
      buf="docker stop $(docker ps -q --filter ancestor=qdrant/qdrant )"
      subprocess.call(buf, shell=True)
      time.sleep(4)
      buf = "docker run -d -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage:z qdrant/qdrant"
      v=subprocess.call(buf, shell=True)
    return v,buf

def pgptchat(prompt,context,docfilter,port,includesources,ip,endpoint):

  response=maadstml.pgptchat(prompt,context,docfilter,port,includesources,ip,endpoint)
  return response

def producegpttokafka(value,maintopic):
     inputbuf=value
     topicid=int(default_args['topicid'])
     producerid=default_args['producerid']
     identifier = default_args['identifier']

     # Add a 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic
     delay=default_args['delay']
     enabletls=default_args['enabletls']

     try:
        result=maadstml.viperproducetotopic(VIPERTOKEN,VIPERHOST,VIPERPORT,maintopic,producerid,enabletls,delay,'','', '',0,inputbuf,'',
                                            topicid,identifier)
        print(result)
     except Exception as e:
        print("ERROR:",e)

def consumetopicdata():

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
   context = default_args['context']
   jsonkeytogather = default_args['jsonkeytogather']
   attribute = default_args['keyattribute']
   processtype = default_args['keyprocesstype']

   res=json.loads(result,strict='False')
   message = ""
   found=0 

   if jsonkeytogather == '':
     tsslogging.tsslogit("PrivateGPT DAG jsonkeytogather is empty in {} {}".format(os.path.basename(__file__),e), "ERROR" )
     tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")
     return

   for r in res['StreamTopicDetails']['TopicReads']:
       if jsonkeytogather == 'Identifier':
         identarr=r['Identifier'].split("~")
         try:
           #print(r['Identifier'], " attribute=",attribute)
           attribute = attribute.lower()
           aar = attribute.split(",")
           isin=any(x in r['Identifier'].lower() for x in aar)
           if isin:
             found=0
             for d in r['RawData']:              
                found=1
                message = message  + str(d) + ', '
             if found:
               message = "{}.  Data: {}. {}".format(context,message,prompt)
               privategptmessage.append([message,identarr[0]])
             message = ""
         except Excepption as e:
           tsslogging.tsslogit("PrivateGPT DAG in {} {}".format(os.path.basename(__file__),e), "ERROR" )
           tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")
#           break
       else:
         isin1 = False
         isin2 = False
         found=0
         message = ""   
         identarr=r['Identifier'].split("~")   
         if processtype != '' and attribute != '':
           processtype = processtype.lower()
           ptypearr = processtype.split(",")
           isin1=any(x in r['Preprocesstype'].lower() for x in ptypearr)

           attribute = attribute.lower()
           aar = attribute.split(",")
           isin2=any(x in r['Identifier'].lower() for x in aar)

           if isin1 and isin2:
             buf = r[jsonkeytogather]
             if buf != '':
               found=1
               message = message  + "{} (Identifier={})".format(buf,identarr[0]) + ', '
         elif processtype != '' and attribute == '':
           processtype = processtype.lower()
           ptypearr = processtype.split(",")
           isin1=any(x in r['Preprocesstype'].lower() for x in ptypearr)
           if isin1:
             buf = r[jsonkeytogather]
             if buf != '':
               found=1
               message = message  + "{} (Identifier={})".format(buf,identarr[0]) + ', '
         elif processtype == '' and attribute != '':
           attribute = attribute.lower()
           aar = attribute.split(",")
           isin2=any(x in r['Identifier'].lower() for x in aar)
           if isin2:
             buf = r[jsonkeytogather]
             if buf != '':
               found=1
               message = message  + "{} (Identifier={})".format(buf,identarr[0]) + ', '
         else:
           buf = r[jsonkeytogather]
           if buf != '':
             found=1
             message = message  + "{} (Identifier={})".format(buf,identarr[0]) + ', '
         
         if found and default_args['hyperbatch']=="0":
              message = "{}.  Data: {}.  {}".format(context,message,prompt)
              privategptmessage.append([message,identarr[0]])

                
   if jsonkeytogather != 'Identifier' and found and default_args['hyperbatch']=="1":
     message = "{}.  Data: {}.  {}".format(context,message,prompt)
     privategptmessage.append(message)


#   print("privategptmessage=",privategptmessage)
   return privategptmessage


def sendtoprivategpt(maindata):

   counter = 0   
   maxc = 300
   pgptendpoint="/v1/completions"
   
   maintopic = default_args['pgpt_data_topic']
   mainip = default_args['pgpthost']
   mainport = default_args['pgptport']

   for mess in maindata:
        if default_args['jsonkeytogather']=='Identifier' or default_args['hyperbatch']=="0":
           m = mess[0]
           m1 = mess[1]
        else:
           m = mess
           m1 = default_args['keyattribute']
            
        response=pgptchat(m,False,"",mainport,False,mainip,pgptendpoint)
        # Produce data to Kafka
        response = response[:-1] + "," + "\"prompt\":\"" + m + "\",\"identifier\":\"" + m1 + "\"}"
        print("PGPT response=",response)
        if 'ERROR:' not in response:         
          response = response.replace('\\"',"'").replace('\n',' ')  
          producegpttokafka(response,maintopic)
          time.sleep(1)
        else:
          counter += 1
          time.sleep(1)
          if counter > maxc:                
             startpgptcontainer()
             qdrantcontainer()
             counter = 0 
             tsslogging.tsslogit("PrivateGPT Step 9 DAG PrivateGPT Container restarting in {} {}".format(os.path.basename(__file__),response), "WARN" )
             tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")                    
                

def windowname(wtype,sname,dagname):
    randomNumber = random.randrange(10, 9999)
    wn = "python-{}-{}-{},{}".format(wtype,randomNumber,sname,dagname)
    with open("/tmux/pythonwindows_{}.txt".format(sname), 'a', encoding='utf-8') as file:
      file.writelines("{}\n".format(wn))

    return wn

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
       ti.xcom_push(key="{}_pgptcontainername".format(sname), value=default_args['pgptcontainername'])
       ti.xcom_push(key="{}_offset".format(sname), value="_{}".format(default_args['offset']))
       ti.xcom_push(key="{}_rollbackoffset".format(sname), value="_{}".format(default_args['rollbackoffset']))

       ti.xcom_push(key="{}_topicid".format(sname), value="_{}".format(default_args['topicid']))
       ti.xcom_push(key="{}_enabletls".format(sname), value="_{}".format(default_args['enabletls']))
       ti.xcom_push(key="{}_partition".format(sname), value="_{}".format(default_args['partition']))

       ti.xcom_push(key="{}_prompt".format(sname), value=default_args['prompt'])
       ti.xcom_push(key="{}_context".format(sname), value=default_args['context'])
       ti.xcom_push(key="{}_jsonkeytogather".format(sname), value=default_args['jsonkeytogather'])
       ti.xcom_push(key="{}_keyattribute".format(sname), value=default_args['keyattribute'])
       ti.xcom_push(key="{}_keyprocesstype".format(sname), value=default_args['keyprocesstype'])
        
       ti.xcom_push(key="{}_vectordbcollectionname".format(sname), value=default_args['vectordbcollectionname'])

       ti.xcom_push(key="{}_concurrency".format(sname), value="_{}".format(default_args['concurrency']))
       ti.xcom_push(key="{}_cuda".format(sname), value="_{}".format(default_args['CUDA_VISIBLE_DEVICES']))
       ti.xcom_push(key="{}_pgpthost".format(sname), value=default_args['pgpthost'])
       ti.xcom_push(key="{}_pgptport".format(sname), value="_{}".format(default_args['pgptport']))
       ti.xcom_push(key="{}_hyperbatch".format(sname), value="_{}".format(default_args['hyperbatch']))

       repo=tsslogging.getrepo()
       if sname != '_mysolution_':
        fullpath="/{}/tml-airflow/dags/tml-solutions/{}/{}".format(repo,sname,os.path.basename(__file__))
       else:
         fullpath="/{}/tml-airflow/dags/{}".format(repo,os.path.basename(__file__))

       wn = windowname('ai',sname,sd)
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

        tsslogging.locallogs("INFO", "STEP 9: Starting privateGPT")
        v,buf=startpgptcontainer()
        if v==1:
          tsslogging.locallogs("WARN", "STEP 9: There seems to be an issue starting the privateGPT container.  Here is the run command - try to run it nanually for testing: {}".format(buf))
        else:
          tsslogging.locallogs("INFO", "STEP 9: Success starting privateGPT.  Here is the run command: {}".format(buf))
         
        v,buf=qdrantcontainer()
        if buf != "":
         if v==1:
          tsslogging.locallogs("WARN", "STEP 9: There seems to be an issue starting the Qdrant container.  Here is the run command - try to run it nanually for testing: {}".format(buf))
         else:
          tsslogging.locallogs("INFO", "STEP 9: Success starting Qdrant.  Here is the run command: {}".format(buf))
        
        time.sleep(10)  # wait for containers to start

        while True:
         try:
             # Get preprocessed data from Kafka
             result = consumetopicdata()

             # Format the preprocessed data for PrivateGPT
             maindata = gatherdataforprivategpt(result)

             # Send the data to PrivateGPT and produce to Kafka
             if len(maindata) > 0:
              sendtoprivategpt(maindata)                      
             time.sleep(2)
         except Exception as e:
          tsslogging.locallogs("ERROR", "STEP 9: PrivateGPT Step 9 DAG in {} {}".format(os.path.basename(__file__),e))
          tsslogging.tsslogit("PrivateGPT Step 9 DAG in {} {}".format(os.path.basename(__file__),e), "ERROR" )
          tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")
          break
