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
import threading
from binaryornot.check import is_binary
docidstrarr = []

sys.dont_write_bytecode = True

######################################################USER CHOSEN PARAMETERS ###########################################################
default_args = {
 'owner': 'Sebastian Maurice',   # <<< *** Change as needed
 'pgptcontainername' : 'maadsdocker/tml-privategpt-with-gpu-nvidia-amd64-v2', #'maadsdocker/tml-privategpt-no-gpu-amd64',  # enter a valid container https://hub.docker.com/r/maadsdocker/tml-privategpt-no-gpu-amd64
 'rollbackoffset' : '5',  # <<< *** Change as needed
 'offset' : '-1', # leave as is
 'enabletls' : '1', # change as needed
 'brokerhost' : '', # <<< *** Leave as is
 'brokerport' : '-999', # <<< *** Leave as is
 'microserviceid' : '',  # change as needed
 'topicid' : '-999', # leave as is
 'delay' : '100', # change as needed
 'companyname' : 'otics',  # <<< *** Change as needed
 'consumerid' : 'streamtopic',  # <<< *** Leave as is
 'consumefrom' : 'cisco-network-preprocess',    # <<< *** Change as needed
 'pgpt_data_topic' : 'cisco-network-privategpt',
 'producerid' : 'private-gpt',   # <<< *** Leave as is
 'identifier' : 'This is analysing TML output with privategpt',
 'pgpthost': 'http://127.0.0.1', # PrivateGPT container listening on this host
 'pgptport' : '8001', # PrivateGPT listening on this port
 'preprocesstype' : '', # Leave as is 
 'partition' : '-1', # Leave as is 
 'prompt': '[INST] Are there any errors in the  logs? Give s detailed response including IP addresses and host machines.[/INST]', # Enter your prompt here
 'context' : 'This is network data from inbound and outbound packets. The data are \
anomaly probabilities for cyber threats from analysis of inbound and outbound packets. If inbound or outbound \
anomaly probabilities are less than 0.60, it is likely the risk of a cyber attack is also low. If its above 0.60, then risk is mid to high.', # what is this data about? Provide context to PrivateGPT
 'jsonkeytogather' : 'hyperprediction', # enter key you want to gather data from to analyse with PrivateGpt i.e. Identifier or hyperprediction
 'keyattribute' : 'inboundpackets,outboundpackets', # change as needed  
 'keyprocesstype' : 'anomprob',  # change as needed
 'hyperbatch' : '0', # Set to 1 if you want to batch all of the hyperpredictions and sent to chatgpt, set to 0, if you want to send it one by one   
 'vectordbcollectionname' : 'tml-llm-model-v2', # change as needed
 'concurrency' : '2', # change as needed Leave at 1
 'CUDA_VISIBLE_DEVICES' : '0', # change as needed
 'docfolder': 'mylogs,mylogs2',  # You can specify the sub-folder that contains TEXT or PDF files..this is a subfolder in the MAIN folder mapped to /rawdata
                   # if this field in NON-EMPTY, privateGPT will query these documents as the CONTEXT to answer your prompt
                   # separate multiple folders with a comma
 'docfolderingestinterval': '900', # how often you want TML to RE-LOAD the files in docfolder - enter the number of SECONDS
 'useidentifierinprompt': '1', # If 1, this uses the identifier in the TML json output and appends it to prompt, If 0, it uses the prompt only    
 'searchterms': '192.168.--identifier--,authentication failure',
 'temperature' : '0.1', # This value ranges between 0 and 1, it controls how conservative LLM model will be, if 0 very very, if 1 it will hallucinate
 'vectorsearchtype' : 'Manhattan', # this is for the Qdrant Search algorithm.  it can be: Cosine, Euclid, Dot, or Manhattan
 'streamall': '1'
}

############################################################### DO NOT MODIFY BELOW ####################################################

VIPERTOKEN=""
VIPERHOST=""
VIPERPORT=""
HTTPADDR=""
maintopic =  default_args['consumefrom']
mainproducerid = default_args['producerid']
GPTONLINE=0

def checkresponse(response,ident):
    global GPTONLINE
    print("Checkresponse")
    st="false"
    
    if "ERROR:" in response:         
         return response,st
        
    GPTONLINE=1
                
    response = response.replace("null","-1").replace("\n","")
    r1=json.loads(response)
    c1=r1['choices'][0]['message']['content']
    if '=' in c1 and ('Answer:' in c1 or 'A:' in c1):
      r1['choices'][0]['message']['content'] = "The analysis of the document(s) did not find a proper result."
      response = json.dumps(r1)
      return response,st  
        
    if default_args['searchterms'] != '':          
          starr = default_args['searchterms'].split(",")
          for t in starr:
              if '--identifier--' in t:
                  t = t.replace("--identifier--",ident)   
              if t in  c1:
                st="true"
                break

    return response,st

def stopcontainers():
   pgptcontainername = default_args['pgptcontainername']
   cfound=0
   subprocess.call("docker image ls > gptfiles.txt", shell=True)
   with open('gptfiles.txt', 'r', encoding='utf-8') as file:
        data = file.readlines()
        r=0
        for d in data:
          darr = d.split(" ")
          if '-privategpt-' in darr[0]:
            buf="docker stop $(docker ps -q --filter ancestor={} )".format(darr[0])
            if pgptcontainername in darr[0]:
                cfound=1  
            print(buf)
            subprocess.call(buf, shell=True)
   if cfound==0:
      print("INFO STEP 9: PrivateGPT container {} not found.  It may need to be pulled.".format(pgptcontainername))
      tsslogging.locallogs("WARN", "STEP 9: PrivateGPT container not found. It may need to be pulled if it does not start: docker pull {}".format(pgptcontainername))

def startpgptcontainer():
      collection = default_args['vectordbcollectionname']
      concurrency = default_args['concurrency']
      pgptcontainername = default_args['pgptcontainername']
      pgptport = int(default_args['pgptport'])
      cuda = int(default_args['CUDA_VISIBLE_DEVICES'])
      temp = default_args['temperature']
      vectorsearchtype = default_args['vectorsearchtype']
 
      stopcontainers()
#      buf="docker stop $(docker ps -q --filter ancestor={} )".format(pgptcontainername)
 #     subprocess.call(buf, shell=True)
      time.sleep(10)
      if '-no-gpu-' in pgptcontainername:       
          buf = "docker run -d -p {}:{} --net=host --env PORT={} --env GPU=0 --env COLLECTION={} --env WEB_CONCURRENCY={} --env CUDA_VISIBLE_DEVICES={} --env temperature={} --env vectorsearchtype=\"{}\" {}".format(pgptport,pgptport,pgptport,collection,concurrency,cuda,temperature,vectorsearchtype,pgptcontainername)       
      else: 
        if os.environ['TSS'] == "1":       
          buf = "docker run -d -p {}:{} --net=host --gpus all -v /var/run/docker.sock:/var/run/docker.sock:z --env PORT={} --env TSS=1 --env GPU=1 --env COLLECTION={} --env WEB_CONCURRENCY={} --env CUDA_VISIBLE_DEVICES={} --env TOKENIZERS_PARALLELISM=false --env temperature={} --env vectorsearchtype=\"{}\" {}".format(pgptport,pgptport,pgptport,collection,concurrency,cuda,temperature,vectorsearchtype,pgptcontainername)
        else:
          buf = "docker run -d -p {}:{} --net=bridge --gpus all -v /var/run/docker.sock:/var/run/docker.sock:z --env PORT={} --env TSS=0 --env GPU=1 --env COLLECTION={} --env WEB_CONCURRENCY={} --env CUDA_VISIBLE_DEVICES={} --env TOKENIZERS_PARALLELISM=false --env temperature={} --env vectorsearchtype=\"{}\" {}".format(pgptport,pgptport,pgptport,collection,concurrency,cuda,temperature,vectorsearchtype,pgptcontainername)
         
      v=subprocess.call(buf, shell=True)
      print("INFO STEP 9: PrivateGPT container.  Here is the run command: {}, v={}".format(buf,v))
      tsslogging.locallogs("INFO", "STEP 9: PrivateGPT container.  Here is the run command: {}, v={}".format(buf,v))

      return v,buf
 
def qdrantcontainer():
    v=0
    buf=""
    buf="docker stop $(docker ps -q --filter ancestor=qdrant/qdrant )"
    subprocess.call(buf, shell=True)
    time.sleep(4)
    if os.environ['TSS'] == "1":
      buf = "docker run -d -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage:z qdrant/qdrant"
    else: 
       buf = "docker run -d --network=bridge -v /var/run/docker.sock:/var/run/docker.sock:z -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage:z qdrant/qdrant"

    v=subprocess.call(buf, shell=True)
    print("INFO STEP 9: Qdrant container.  Here is the run command: {}, v={}".format(buf,v))
    
    tsslogging.locallogs("INFO", "STEP 9: Qdrant container.  Here is the run command: {}, v={}".format(buf,v))
    
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
   if 'step9prompt' in os.environ:
      if os.environ['step9prompt'] != '':
        prompt = os.environ['step9prompt']
        default_args['prompt'] = prompt
      else:
       prompt = default_args['prompt']
   else: 
      prompt = default_args['prompt']

   if 'step9context' in os.environ:
      if os.environ['step9context'] != '':
        context = os.environ['step9context']
        default_args['context'] = context
      else:
        context = default_args['context']  
   else: 
     context = default_args['context']

   jsonkeytogather = default_args['jsonkeytogather']
   if default_args['docfolder'] != '':
       context = ''
       if default_args['useidentifierinprompt'] == "1":
          jsonkeytogather = "Identifier"

   if 'step9keyattribute' in os.environ:
     if os.environ['step9keyattribute'] != '':
       attribute = os.environ['step9keyattribute']
       default_args['keyattribute'] = attribute
     else: 
       attribute = default_args['keyattribute']      
   else:
    attribute = default_args['keyattribute']

   if 'step9keyprocesstype' in os.environ:
     if os.environ['step9keyprocesstype'] != '':
        processtype = os.environ['step9keyprocesstype']
        default_args['keyprocesstype'] = processtype
     else: 
       processtype = default_args['keyprocesstype']    
   else: 
     processtype = default_args['keyprocesstype']

   if 'step9hyperbatch' in os.environ:
     if os.environ['step9hyperbatch'] != '':
        hyperbatch = os.environ['step9hyperbatch']
        default_args['hyperbatch'] = hyperbatch
     else: 
       hyperbatch = default_args['hyperbatch']    
   else: 
     hyperbatch = default_args['hyperbatch']

   res=json.loads(result,strict='False')
   message = ""
   found=0 

   if jsonkeytogather == '':
     tsslogging.tsslogit("PrivateGPT DAG jsonkeytogather is empty in {} {}".format(os.path.basename(__file__),e), "ERROR" )
     tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")
     return

   for r in res['StreamTopicDetails']['TopicReads']:
       if jsonkeytogather == 'Identifier' or jsonkeytogather == 'identifier':
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
               if context != '':
                  message = "{}.  Data: {}. {}".format(context,message,prompt)
               elif '--identifier--' in prompt:
                  prompt2 = prompt.replace('--identifier--',identarr[0])
                  message = "{}".format(prompt2)
               else: 
                 message = "{}".format(prompt)
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
         
         if found and hyperbatch=="0":
              if '--identifier--' in prompt:
                  prompt2 = prompt.replace('--identifier--',identarr[0])
                  message = "{}.  Data: {}.  {}".format(context,message,prompt2)
              else: 
                  message = "{}.  Data: {}.  {}".format(context,message,prompt)
              privategptmessage.append([message,identarr[0]])

                
   if jsonkeytogather != 'Identifier' and found and hyperbatch=="1":
     message = "{}.  Data: {}.  {}".format(context,message,prompt)
     privategptmessage.append(message)


#   print("privategptmessage=",privategptmessage)
   return privategptmessage

def startdirread():
  global GPTONLINE
  print("INFO startdirread")  
  try:  
    t = threading.Thread(name='child procs', target=ingestfiles)
    t.start()
  except Exception as e:
    print(e)

def deleteembeddings(docids):
  pgptendpoint="/v1/ingest/"
  pgptip = default_args['pgpthost']
  pgptport = default_args['pgptport']
  maadstml.pgptdeleteembeddings(docids,pgptip,pgptport,pgptendpoint)   


def getingested(docname):
  pgptendpoint="/v1/ingest/list"
  pgptip = default_args['pgpthost']
  pgptport = default_args['pgptport']
  docids,docstr,docidsstr=maadstml.pgptgetingestedembeddings(docname,pgptip,pgptport,pgptendpoint)
  return docids,docstr,docidsstr

def ingestfiles():
    global docidstrarr, GPTONLINE
    pgptendpoint="/v1/ingest"
    docidstrarr = []
    basefolder='/rawdata/'
    pgptip = default_args['pgpthost']
    pgptport = default_args['pgptport']
 #   buf="/mnt/c/maads/tml-airflow/rawdata/mylogs,/mnt/c/maads/tml-airflow/rawdata/mylogs2"
    buf = default_args['docfolder']
 
    bufarr=buf.split(",")
    while True:
     if GPTONLINE:
      docidstrarr = []
      for dirp in bufarr:
        # lock the directory
        dirp = basefolder + dirp
        if os.path.exists(dirp):
          with tsslogging.LockDirectory(dirp) as lock:
            newfd = os.dup(lock.dir_fd)
            files = [ os.path.join(dirp,f) for f in os.listdir(dirp) if os.path.isfile(os.path.join(dirp,f)) ]
            for mf in files:
               docids,docstr,docidstr=getingested(mf)
               deleteembeddings(docids)
               print("INFO Ingestfiles:",mf)  
 
               if is_binary(mf):
                 maadstml.pgptingestdocs(mf,'binary',pgptip,pgptport,pgptendpoint)
               else:
                 try:
                    maadstml.pgptingestdocs(mf,'text',pgptip,pgptport,pgptendpoint)
                 except Exception as e:
                     print("ERROR:",e)

               docids,docstr,docidstr=getingested(mf)
               if len(docidstr) >=1:
                 docidstrarr.append(docidstr[0])
               
        else:
          print("WARN Directory Path: {} does not exist".format(dirp))
         
      time.sleep(int(default_args['docfolderingestinterval']))
      print("docidsstr=",docidstrarr)
     time.sleep(1)

def sendtoprivategpt(maindata,docfolder):
   global docidstrarr
   counter = 0   
   maxc = 300
   pgptendpoint="/v1/completions"

   mcontext = False
   usingqdrant = ''
   if docfolder != '':
     mcontext = True
     usingqdrant = 'Using documents in Qdrant VectorDB for context.' 
    
   maintopic = default_args['pgpt_data_topic']
   if os.environ['TSS']=="1":
     mainip = default_args['pgpthost']
   else: 
     mainip = "http://" + os.environ['qip']

   mainport = default_args['pgptport']

   if 'step9keyattribute' in os.environ:
     if os.environ['step9keyattribute'] != '':
       attribute = os.environ['step9keyattribute']
       default_args['keyattribute'] = attribute
     else: 
       attribute = default_args['keyattribute']      
   else:
    attribute = default_args['keyattribute']

   if 'step9hyperbatch' in os.environ:
     if os.environ['step9hyperbatch'] != '':
        hyperbatch = os.environ['step9hyperbatch']
        default_args['hyperbatch'] = hyperbatch
     else: 
       hyperbatch = default_args['hyperbatch']    
   else: 
     hyperbatch = default_args['hyperbatch']
 
   for mess in maindata:
        if default_args['jsonkeytogather']=='Identifier' or hyperbatch=="0":
           m = mess[0]
           m1 = mess[1]
        else:
           m = mess
           m1 = attribute #default_args['keyattribute']
        
        response=pgptchat(m,mcontext,docidstrarr,mainport,False,mainip,pgptendpoint)
        # Produce data to Kafka
        sf="false"
        if usingqdrant != '':
           response,sf=checkresponse(response,m1) 
           if default_args['streamall']=="0": # Only stream if search terms found in response
              if sf=="false":
                 response="ERROR:"
           m = m + ' (' + usingqdrant + ')'
        response = response[:-1] + "," + "\"prompt\":\"" + m + "\",\"identifier\":\"" + m1 + "\",\"searchfound\":\"" + sf + "\"}"
        print("PGPT response=",response)
        if 'ERROR:' not in response:         
          response = response.replace('\\"',"'").replace('\n',' ')  
          producegpttokafka(response,maintopic)
        #  time.sleep(1)
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

       if 'step9rollbackoffset' in os.environ:
          if os.environ['step9rollbackoffset'] != '':
            default_args['rollbackoffset'] = os.environ['step9rollbackoffset']

       if 'step9prompt' in os.environ:
          if os.environ['step9prompt'] != '':
            default_args['prompt'] = os.environ['step9prompt']
       if 'step9context' in os.environ:
          if os.environ['step9context'] != '':
            default_args['context'] = os.environ['step9context']

       if 'step9keyattribute' in os.environ:
          if os.environ['step9keyattribute'] != '':
            default_args['keyattribute'] = os.environ['step9keyattribute']
       if 'step9keyprocesstype' in os.environ:
          if os.environ['step9keyprocesstype'] != '':
            default_args['keyprocesstype'] = os.environ['step9keyprocesstype']
       if 'step9hyperbatch' in os.environ:
          if os.environ['step9hyperbatch'] != '':
            default_args['hyperbatch'] = os.environ['step9hyperbatch']
       if 'step9vectordbcollectionname' in os.environ:
          if os.environ['step9vectordbcollectionname'] != '':
            default_args['vectordbcollectionname'] = os.environ['step9vectordbcollectionname']
       if 'step9concurrency' in os.environ:
          if os.environ['step9concurrency'] != '':
            default_args['concurrency'] = os.environ['step9concurrency']
       if 'CUDA_VISIBLE_DEVICES' in os.environ:
          if os.environ['CUDA_VISIBLE_DEVICES'] != '':
            default_args['CUDA_VISIBLE_DEVICES'] = os.environ['CUDA_VISIBLE_DEVICES']
           
       if 'step9docfolder' in os.environ:
          if os.environ['step9docfolder'] != '':
            default_args['docfolder'] = os.environ['step9docfolder']
       if 'step9docfolderingestinterval' in os.environ:
          if os.environ['step9docfolderingestinterval'] != '':
            default_args['docfolderingestinterval'] = os.environ['step9docfolderingestinterval']
       if 'step9useidentifierinprompt' in os.environ:
          if os.environ['step9useidentifierinprompt'] != '':
            default_args['useidentifierinprompt'] = os.environ['step9useidentifierinprompt']
       if 'step9searchterms' in os.environ:
          if os.environ['searchterms'] != '':
            default_args['searchterms'] = os.environ['searchterms']

       if 'step9temperature' in os.environ:
          if os.environ['temperature'] != '':
            default_args['temperature'] = os.environ['temperature']
       if 'step9vectorsearchtype' in os.environ:
          if os.environ['vectorsearchtype'] != '':
            default_args['vectorsearchtype'] = os.environ['vectorsearchtype']

       VIPERTOKEN = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERTOKEN".format(sname))
       VIPERHOST = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERHOSTPREPROCESSPGPT".format(sname))
       VIPERPORT = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERPORTPREPROCESSPGPT".format(sname))
       HTTPADDR = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_HTTPADDR".format(sname))

       ti = context['task_instance']
       ti.xcom_push(key="{}_consumefrom".format(sname), value=default_args['consumefrom'])
       ti.xcom_push(key="{}_pgpt_data_topic".format(sname), value=default_args['pgpt_data_topic'])
       ti.xcom_push(key="{}_pgptcontainername".format(sname), value=default_args['pgptcontainername'])
       ti.xcom_push(key="{}_offset".format(sname), value="_{}".format(default_args['offset']))
       if 'step9rollbackoffset' in os.environ:
          ti.xcom_push(key="{}_rollbackoffset".format(sname), value="_{}".format(os.environ['step9rollbackoffset']))
       else: 
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

       ti.xcom_push(key="{}_docfolder".format(sname), value="{}".format(default_args['docfolder']))
       ti.xcom_push(key="{}_docfolderingestinterval".format(sname), value="_{}".format(default_args['docfolderingestinterval']))
       ti.xcom_push(key="{}_useidentifierinprompt".format(sname), value="_{}".format(default_args['useidentifierinprompt']))
       ti.xcom_push(key="{}_searchterms".format(sname), value="{}".format(default_args['searchterms']))
       ti.xcom_push(key="{}_streamall".format(sname), value="_{}".format(default_args['streamall']))
       ti.xcom_push(key="{}_temperature".format(sname), value="_{}".format(default_args['temperature']))
       ti.xcom_push(key="{}_vectorsearchtype".format(sname), value="{}".format(default_args['vectorsearchtype']))
    

       repo=tsslogging.getrepo()
       if sname != '_mysolution_':
        fullpath="/{}/tml-airflow/dags/tml-solutions/{}/{}".format(repo,sname,os.path.basename(__file__))
       else:
         fullpath="/{}/tml-airflow/dags/{}".format(repo,os.path.basename(__file__))

       wn = windowname('ai',sname,sd)
       subprocess.run(["tmux", "new", "-d", "-s", "{}".format(wn)])
       subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "cd /Viper-preprocess-pgpt", "ENTER"])
       subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "python {} 1 {} {}{} {} \"{}\" \"{}\" \"{}\" \"{}\" \"{}\" \"{}\" \"{}\" \"{}\" \"{}\" \"{}\" \"{}\" \"{}\" \"{}\" {} {} {}".format(fullpath,VIPERTOKEN, HTTPADDR, VIPERHOST, VIPERPORT[1:],
                       default_args['vectordbcollectionname'],default_args['concurrency'],default_args['CUDA_VISIBLE_DEVICES'],default_args['rollbackoffset'],
                       default_args['prompt'],default_args['context'],default_args['keyattribute'],default_args['keyprocesstype'],
                       default_args['hyperbatch'],default_args['docfolder'],default_args['docfolderingestinterval'],
                       default_args['useidentifierinprompt'],default_args['searchterms'],default_args['streamall'],default_args['temperature'],default_args['vectorsearchtype']), "ENTER"])

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
        vectordbcollectionname =  sys.argv[5]
        concurrency =  sys.argv[6]

        cuda =  sys.argv[7]
        rollbackoffset =  sys.argv[8]
        prompt =  sys.argv[9]
        context =  sys.argv[10]
        keyattribute =  sys.argv[11]
        keyprocesstype =  sys.argv[12]
        hyperbatch =  sys.argv[13]
        docfolder =  sys.argv[14]
        docfolderingestinterval =  sys.argv[15]
        useidentifierinprompt =  sys.argv[16]
        searchterms =  sys.argv[17]
        streamall =  sys.argv[18]
        temperature = sys.argv[19]
        vectorsearchtype = sys.argv[20]
        
        default_args['rollbackoffset']=rollbackoffset
        default_args['prompt'] = prompt
        default_args['context'] = context

        default_args['keyattribute'] = keyattribute
        default_args['keyprocesstype'] = keyprocesstype
        default_args['hyperbatch'] = hyperbatch
        default_args['vectordbcollectionname'] = vectordbcollectionname
        default_args['concurrency'] = concurrency
        default_args['CUDA_VISIBLE_DEVICES'] = cuda
        
        default_args['docfolder'] = docfolder
        default_args['docfolderingestinterval'] = docfolderingestinterval
        default_args['useidentifierinprompt'] = useidentifierinprompt
        default_args['searchterms'] = searchterms
        default_args['streamall'] = streamall
        default_args['temperature'] = temperature
        default_args['vectorsearchtype'] = vectorsearchtype

        if "KUBE" not in os.environ:          
          v,buf=qdrantcontainer()
          if buf != "":
           if v==1:
            tsslogging.locallogs("WARN", "STEP 9: There seems to be an issue starting the Qdrant container.  Here is the run command - try to run it nanually for testing: {}".format(buf))
           else:
            tsslogging.locallogs("INFO", "STEP 9: Success starting Qdrant.  Here is the run command: {}".format(buf))
        
          time.sleep(5)  # wait for containers to start
         
          tsslogging.locallogs("INFO", "STEP 9: Starting privateGPT")
          v,buf=startpgptcontainer()
          if v==1:
            tsslogging.locallogs("WARN", "STEP 9: There seems to be an issue starting the privateGPT container.  Here is the run command - try to run it nanually for testing: {}".format(buf))
          else:
            tsslogging.locallogs("INFO", "STEP 9: Success starting privateGPT.  Here is the run command: {}".format(buf))

          time.sleep(10)  # wait for containers to start
          tsslogging.getqip()          
        elif  os.environ["KUBE"] == "0":
          v,buf=qdrantcontainer()
          if buf != "":
           if v==1:
            tsslogging.locallogs("WARN", "STEP 9: There seems to be an issue starting the Qdrant container.  Here is the run command - try to run it nanually for testing: {}".format(buf))
           else:
            tsslogging.locallogs("INFO", "STEP 9: Success starting Qdrant.  Here is the run command: {}".format(buf))
        
          time.sleep(5)  # wait for containers to start         
         
          tsslogging.locallogs("INFO", "STEP 9: Starting privateGPT")
          v,buf=startpgptcontainer()
          if v==1:
            tsslogging.locallogs("WARN", "STEP 9: There seems to be an issue starting the privateGPT container.  Here is the run command - try to run it nanually for testing: {}".format(buf))
          else:
            tsslogging.locallogs("INFO", "STEP 9: Success starting privateGPT.  Here is the run command: {}".format(buf))

          time.sleep(10)  # wait for containers to start         
          tsslogging.getqip() 
        else:  
          tsslogging.locallogs("INFO", "STEP 9: [KUBERNETES] Starting privateGPT - LOOKS LIKE THIS IS RUNNING IN KUBERNETES")
          tsslogging.locallogs("INFO", "STEP 9: [KUBERNETES] Make sure you have applied the private GPT YAML files and have the privateGPT Pod running")

        print("Docfolder=",docfolder)
        if docfolder != '':
          startdirread()
                   
        while True:
         try:
             # Get preprocessed data from Kafka
             result = consumetopicdata()

             # Format the preprocessed data for PrivateGPT
             maindata = gatherdataforprivategpt(result)

             # Send the data to PrivateGPT and produce to Kafka
             if len(maindata) > 0:
              sendtoprivategpt(maindata,docfolder)                      
             time.sleep(2)
         except Exception as e:
            
          tsslogging.locallogs("ERROR", "STEP 9: PrivateGPT Step 9 DAG in {} {}".format(os.path.basename(__file__),e))
          tsslogging.tsslogit("PrivateGPT Step 9 DAG in {} {}".format(os.path.basename(__file__),e), "ERROR" )
          tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")
          time.sleep(5)
