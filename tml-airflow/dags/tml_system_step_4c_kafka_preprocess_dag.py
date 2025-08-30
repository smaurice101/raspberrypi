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
import base64
import threading
import shutil

sys.dont_write_bytecode = True
######################################## USER CHOOSEN PARAMETERS ########################################
default_args = {
  'owner' : 'Sebastian Maurice',  # <<< *** Change as needed      
  'enabletls': '1', # <<< *** 1=connection is encrypted, 0=no encryption
  'microserviceid' : '',  # <<< *** leave blank
  'producerid' : 'rtmssolution',   # <<< *** Change as needed   
  'raw_data_topic' : 'iot-preprocess', # *************** INCLUDE ONLY ONE TOPIC - This is one of the topic you created in SYSTEM STEP 2
  'preprocess_data_topic' : 'rtms-preprocess', # *************** INCLUDE ONLY ONE TOPIC - This is one of the topic you created in SYSTEM STEP 2
  'maxrows' : '200', # <<< ********** Number of offsets to rollback the data stream -i.e. rollback stream by 500 offsets
  'offset' : '-1', # <<< Rollback from the end of the data streams  
  'brokerhost' : '',   # <<< *** Leave as is
  'brokerport' : '-999',  # <<< *** Leave as is   
  'delay' : '70', # Add a 70 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic     
  'array' : '0', # do not modify
  'saveasarray' : '1', # do not modify
  'topicid' : '-999', # do not modify
  'rawdataoutput' : '1', # <<< 1 to output raw data used in the preprocessing, 0 do not output
  'asynctimeout' : '120', # <<< 120 seconds for connection timeout 
  'timedelay' : '0', # <<< connection delay
  'tmlfilepath' : '', # leave blank
  'usemysql' : '1', # do not modify
  'rtmsstream' : 'rtms-stream-mylogs', # Change as needed - STREAM containing log file data (or other data) for RTMS
                                                    # If entitystream is empty, TML uses the preprocess type only.
  'identifier' : 'RTMS Past Memory of Events', # <<< ** Change as needed
  'searchterms' : 'rgx:p([a-z]+)ch ~~~ |authentication failure,--entity-- password failure ~~~ |unknown--entity--', # main Search terms, if AND add @, if OR use | s first characters, default OR
                                                             # Must include --entity-- if correlating with entity - this will be replaced 
                                                             # dynamically with the entities found in raw_data_topic
  'localsearchtermfolder': '|mysearchfile1,|mysearchfile2', # Specify a folder of files containing search terms - each term must be on a new line - use comma
                               # to apply each folder to the rtmstream topic
                               # Use @ =AND, |=OR to specify whether the terms in the file should be AND, OR
                               # For example, @mysearchfolder1,|mysearchfolder2, means all terms in mysearchfolder1 should be AND
                               # |mysearchfolder2, means all search terms should be OR'ed
  'localsearchtermfolderinterval': '60', # This is the number of seconds between reading the localsearchtermfolder.  For example, if 60, 
                                       # The files will be read every 60 seconds - and searchterms will be updated
  'rememberpastwindows' : '500', # Past windows to remember
  'patternwindowthreshold' : '30', # check for the number of patterns for the items in searchterms
  'rtmsscorethreshold': '0.6',  # RTMS score threshold i.e. '0.8'   
  'rtmsscorethresholdtopic': 'rtmstopic',   # All rtms score greater than rtmsscorethreshold will be streamed to this topic
  'attackscorethreshold': '0.6',   # Attack score threshold i.e. '0.8'   
  'attackscorethresholdtopic': 'attacktopic',   # All attack score greater than attackscorethreshold will be streamed to this topic
  'patternscorethreshold': '0.6',   # Pattern score threshold i.e. '0.8'   
  'patternscorethresholdtopic': 'patterntopic',   # All pattern score greater thn patternscorethreshold will be streamed to this topic
  'rtmsfoldername': 'rtms',
  'rtmsmaxwindows': '10000'
}

######################################## DO NOT MODIFY BELOW #############################################

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
         tmlfilepath=default_args['tmlfilepath']
         usemysql=int(default_args['usemysql'])
  
         rtmsstream=default_args['rtmsstream']
         identifier = default_args['identifier']
         searchterms=default_args['searchterms']
         rememberpastwindows = default_args['rememberpastwindows']  
         patternwindowthreshold = default_args['patternwindowthreshold']  

         rtmsscorethreshold = default_args['rtmsscorethreshold']  
         rtmsscorethresholdtopic = default_args['rtmsscorethresholdtopic']  
         attackscorethreshold = default_args['attackscorethreshold']  
         attackscorethresholdtopic = default_args['attackscorethresholdtopic']  
         patternscorethreshold = default_args['patternscorethreshold']  
         patternscorethresholdtopic = default_args['patternscorethresholdtopic']  
         rtmsmaxwindows=default_args['rtmsmaxwindows']

         searchterms = str(base64.b64encode(searchterms.encode('utf-8')))
         try:
                result=maadstml.viperpreprocessrtms(VIPERTOKEN,VIPERHOST,VIPERPORT,topic,producerid,offset,maxrows,enabletls,delay,brokerhost,
                                                  brokerport,microserviceid,topicid,rtmsstream,searchterms,rememberpastwindows,identifier,
                                                  preprocesstopic,patternwindowthreshold,array,saveasarray,rawdataoutput,
                                                  rtmsscorethreshold,rtmsscorethresholdtopic,attackscorethreshold,
                                                  attackscorethresholdtopic,patternscorethreshold,patternscorethresholdtopic,rtmsmaxwindows)
#                print(result)
         except Exception as e:
                print("ERROR:",e)

        
def windowname(wtype,sname,dagname):
    randomNumber = random.randrange(10, 9999)
    wn = "python-{}-{}-{},{}".format(wtype,randomNumber,sname,dagname)
    with open("/tmux/pythonwindows_{}.txt".format(sname), 'a', encoding='utf-8') as file: 
      file.writelines("{}\n".format(wn))

    return wn

# add any non-fle search terms to the file search terms
def updatesearchterms(searchtermsfile,regx):
    # check if search terms exist    
    stcurr = default_args['searchterms']
    stcurrfile = searchtermsfile
    mainsearchterms=""

    if len(regx) > 0:
        for r in regx:
           mainsearchterms = mainsearchterms + r + "~~~"
      
    if stcurr != "":
       stcurrarr = stcurr.split("~~~")
       stcurrarrfile = stcurrfile.split("~~~")
       for a in stcurrarr:
          stcurrarrfile.append(a)
       stcurrarrfile = set(stcurrarrfile)
       mainsearchterms = mainsearchterms + '~~~'.join(stcurrarrfile) 
       #mainsearchterms = mainsearchterms[:-1]
    else:
       stcurrarrfile = stcurrfile.split("~~~")      
       stcurrarrfile = set(stcurrarrfile)
       mainsearchterms = mainsearchterms + '~~~'.join(stcurrarrfile) 
       #mainsearchterms = mainsearchterms[:-1]
      
      
    return  mainsearchterms

def ingestfiles():
    buf = default_args['localsearchtermfolder']
    interval=int(default_args['localsearchtermfolderinterval'])
    searchtermsfile = ""

    dirbuf = buf.split(",")
    if len(dirbuf) == 0:
       return

    while True:  
     try: 
      lg=""
      buf = default_args['localsearchtermfolder']
      interval=int(default_args['localsearchtermfolderinterval'])
      searchtermsfile = ""
      dirbuf = buf.split(",")      
      rgx = []      
      for dr in dirbuf:        
         filenames = []
         linebuf=""
         ibx = []
         if dr != "":
            if dr[0]=='@':
              dr = dr[1:]
              lg="@"
            elif dr[0]=='|':
              dr = dr[1:]
              lg="|"
            else:  
              lg="|"

         if os.path.isdir("/rawdata/{}".format(dr)):            
           a = [os.path.join("/rawdata/{}".format(dr), f) for f in os.listdir("/rawdata/{}".format(dr)) if 
           os.path.isfile(os.path.join("/rawdata/{}".format(dr), f))]
           filenames.extend(a)

         if len(filenames) > 0:
           filenames = set(filenames)
           
           for fdr in filenames:            
             with open(fdr) as f:
              lines = [line.rstrip('\n').strip() for line in f]
              lines = set(lines)
              # check regex
              for m in lines:
                if len(m) > 0:
                  if 'rgx:' in m and m[:4]=="rgx:":
                    rgx.append(m)
                  elif '~~~' in m and m[:3]=="~~~":                  
                    ibx.append(m)
                  else:  
                    m=m.replace(",", " ")
                    if m[0] != "~":
                      linebuf = linebuf + m + ","

         if linebuf != "":
           linebuf = linebuf[:-1]
           searchtermsfile = searchtermsfile + lg + linebuf +"~~~"
         if len(ibx)>0:
            ibxs = ''.join(ibx) 
            ibxs=ibxs[3:]
            searchtermsfile = searchtermsfile + ibxs +"~~~"

      if searchtermsfile != "":    
        searchtermsfile = searchtermsfile[:-3]    
        searchtermsfile=updatesearchterms(searchtermsfile,rgx)
        default_args['searchterms']=searchtermsfile
        print("INFO:", searchtermsfile)

      if interval==0:
        break
      else:  
       time.sleep(interval)
     except Exception as e: 
       print("ERROR: ingesting files:",e)
       continue
       
      
def startdirread():
  if 'localsearchtermfolder' not in default_args:
     return
    
  if default_args['localsearchtermfolder'] != '' and default_args['localsearchtermfolderinterval'] != '':
    print("INFO startdirread")  
    try:  
      t = threading.Thread(name='child procs', target=ingestfiles)
      t.start()
    except Exception as e:
      print(e)
      
def dopreprocessing(**context):
       sd = context['dag'].dag_id
       sname=context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_solutionname".format(sd))
       pname=context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_projectname".format(sd))
       
       VIPERTOKEN = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERTOKEN".format(sname))
       VIPERHOST = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERHOSTPREPROCESS3".format(sname))
       VIPERPORT = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERPORTPREPROCESS3".format(sname))
       HTTPADDR = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_HTTPADDR".format(sname))

       chip = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_chip".format(sname)) 
                
       ti = context['task_instance']    
       ti.xcom_push(key="{}_raw_data_topic".format(sname), value=default_args['raw_data_topic'])
       ti.xcom_push(key="{}_preprocess_data_topic".format(sname), value=default_args['preprocess_data_topic'])
       ti.xcom_push(key="{}_delay".format(sname), value="_{}".format(default_args['delay']))
       ti.xcom_push(key="{}_array".format(sname), value="_{}".format(default_args['array']))
       ti.xcom_push(key="{}_saveasarray".format(sname), value="_{}".format(default_args['saveasarray']))
       ti.xcom_push(key="{}_topicid".format(sname), value="_{}".format(default_args['topicid']))
       ti.xcom_push(key="{}_rawdataoutput".format(sname), value="_{}".format(default_args['rawdataoutput']))
       ti.xcom_push(key="{}_asynctimeout".format(sname), value="_{}".format(default_args['asynctimeout']))
       ti.xcom_push(key="{}_timedelay".format(sname), value="_{}".format(default_args['timedelay']))
       ti.xcom_push(key="{}_usemysql".format(sname), value="_{}".format(default_args['usemysql']))
       ti.xcom_push(key="{}_identifier".format(sname), value=default_args['identifier'])

       ti.xcom_push(key="{}_rtmsscorethresholdtopic".format(sname), value=default_args['rtmsscorethresholdtopic'])
       ti.xcom_push(key="{}_attackscorethresholdtopic".format(sname), value=default_args['attackscorethresholdtopic'])
       ti.xcom_push(key="{}_patternscorethresholdtopic".format(sname), value=default_args['patternscorethresholdtopic'])

       localsearchtermfolder=default_args['localsearchtermfolder']
       if 'step4clocalsearchtermfolder' in os.environ:
         ti.xcom_push(key="{}_localsearchtermfolder".format(sname), value=os.environ['step4clocalsearchtermfolder'])
         localsearchtermfolder=os.environ['step4clocalsearchtermfolder']         
       else:  
        ti.xcom_push(key="{}_localsearchtermfolder".format(sname), value=default_args['localsearchtermfolder']) 

       localsearchtermfolderinterval=default_args['localsearchtermfolderinterval']
       if 'step4clocalsearchtermfolderinterval' in os.environ:
         ti.xcom_push(key="{}_localsearchtermfolderinterval".format(sname), value=os.environ['step4clocalsearchtermfolderinterval'])
         localsearchtermfolderinterval=os.environ['step4clocalsearchtermfolderinterval']         
       else:  
        ti.xcom_push(key="{}_localsearchtermfolderinterval".format(sname), value="_{}".format(default_args['localsearchtermfolderinterval']))

       rtmsstream=default_args['rtmsstream']
       if 'step4crtmsstream' in os.environ:
         ti.xcom_push(key="{}_rtmsstream".format(sname), value=os.environ['step4crtmsstream'])
         rtmsstream=os.environ['step4crtmsstream']
       else:  
         ti.xcom_push(key="{}_rtmsstream".format(sname), value=default_args['rtmsstream'])

       maxrows=default_args['maxrows']
       if 'step4cmaxrows' in os.environ:
         ti.xcom_push(key="{}_maxrows".format(sname), value="_{}".format(os.environ['step4cmaxrows']))         
         maxrows=os.environ['step4cmaxrows']
       else:  
         ti.xcom_push(key="{}_maxrows".format(sname), value="_{}".format(default_args['maxrows']))

       searchterms=default_args['searchterms']
       if 'step4csearchterms' in os.environ:
         ti.xcom_push(key="{}_searchterms".format(sname), value="{}".format(os.environ['step4csearchterms']))         
         searchterms=os.environ['step4csearchterms']
       else:  
         ti.xcom_push(key="{}_searchterms".format(sname), value=default_args['searchterms'])

       raw_data_topic=default_args['raw_data_topic']
       if 'step4crawdatatopic' in os.environ:
         ti.xcom_push(key="{}_raw_data_topic".format(sname), value="{}".format(os.environ['step4crawdatatopic']))         
         raw_data_topic=os.environ['step4crawdatatopic']
       else:  
         ti.xcom_push(key="{}_raw_data_topic".format(sname), value=default_args['raw_data_topic'])

       rememberpastwindows=default_args['rememberpastwindows']
       if 'step4crememberpastwindows' in os.environ:
         ti.xcom_push(key="{}_rememberpastwindows".format(sname), value="_{}".format(os.environ['step4crememberpastwindows']))         
         rememberpastwindows=os.environ['step4crememberpastwindows']
       else:  
         ti.xcom_push(key="{}_rememberpastwindows".format(sname), value="_{}".format(default_args['rememberpastwindows']))

       patternwindowthreshold=default_args['patternwindowthreshold']
       if 'step4cpatternwindowthreshold' in os.environ:
         ti.xcom_push(key="{}_patternwindowthreshold".format(sname), value="_{}".format(os.environ['step4cpatternwindowthreshold']))         
         patternwindowthreshold=os.environ['step4cpatternwindowthreshold']
       else:  
         ti.xcom_push(key="{}_patternwindowthreshold".format(sname), value="_{}".format(default_args['patternwindowthreshold']))

       rtmsscorethreshold=default_args['rtmsscorethreshold']
       if 'step4crtmsscorethreshold' in os.environ:
         ti.xcom_push(key="{}_rtmsscorethreshold".format(sname), value="_{}".format(os.environ['step4crtmsscorethreshold']))         
         rtmsscorethreshold=os.environ['step4crtmsscorethreshold']
       else:  
         ti.xcom_push(key="{}_rtmsscorethreshold".format(sname), value="_{}".format(default_args['rtmsscorethreshold']))

       attackscorethreshold=default_args['attackscorethreshold']
       if 'step4cattackscorethreshold' in os.environ:
         ti.xcom_push(key="{}_attackscorethreshold".format(sname), value="_{}".format(os.environ['step4cattackscorethreshold']))         
         attackscorethreshold=os.environ['step4cattackscorethreshold']
       else:  
         ti.xcom_push(key="{}_attackscorethreshold".format(sname), value="_{}".format(default_args['attackscorethreshold']))

       patternscorethreshold=default_args['patternscorethreshold']
       if 'step4cpatternscorethreshold' in os.environ:
         ti.xcom_push(key="{}_patternscorethreshold".format(sname), value="_{}".format(os.environ['step4cpatternscorethreshold']))         
         patternscorethreshold=os.environ['step4cpatternscorethreshold']
       else:  
         ti.xcom_push(key="{}_patternscorethreshold".format(sname), value="_{}".format(default_args['patternscorethreshold']))

       rtmsfoldername=default_args['rtmsfoldername']
       if 'step4crtmsfoldername' in os.environ:
         ti.xcom_push(key="{}_rtmsfoldername".format(sname), value="{}".format(os.environ['step4crtmsfoldername']))         
         rtmsfoldername=os.environ['step4crtmsfoldername']
       else:  
         ti.xcom_push(key="{}_rtmsfoldername".format(sname), value="{}".format(default_args['rtmsfoldername']))
       os.environ["step4crtmsfoldername"] = rtmsfoldername
       try: 
         f = open("/tmux/rtmsfoldername.txt", "w")
         f.write(rtmsfoldername)
         f.close()
       except Exception as e:
         pass

       repo=tsslogging.getrepo() 
       if sname != '_mysolution_':
        fullpath="/{}/tml-airflow/dags/tml-solutions/{}/{}".format(repo,pname,os.path.basename(__file__))  
       else:
         fullpath="/{}/tml-airflow/dags/{}".format(repo,os.path.basename(__file__))  

       if 'step4crtmsmaxwindows' in os.environ:
          rtmsmaxwindows=os.environ['step4crtmsmaxwindows']
          default_args['rtmsmaxwindows']=rtmsmaxwindows
       else: 
          rtmsmaxwindows = default_args['rtmsmaxwindows']
       ti.xcom_push(key="{}_rtmsmaxwindows".format(sname), value="_{}".format(rtmsmaxwindows))         
       try: 
         f = open("/tmux/rtmsmax.txt", "w")
         f.write(rtmsmaxwindows)
         f.close()
       except Exception as e:
         pass
        
       wn = windowname('preprocess3',sname,sd)     
       subprocess.run(["tmux", "new", "-d", "-s", "{}".format(wn)])
       subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "cd /Viper-preprocess3", "ENTER"])
       subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "python {} 1 {} {}{} {} {} \"{}\" {} {} \"{}\" \"{}\" {} {} {} \"{}\" {} \"{}\" {}".format(fullpath,VIPERTOKEN,HTTPADDR,VIPERHOST,VIPERPORT[1:],maxrows,searchterms,rememberpastwindows,patternwindowthreshold,raw_data_topic,rtmsstream,rtmsscorethreshold,attackscorethreshold,patternscorethreshold,localsearchtermfolder,localsearchtermfolderinterval,rtmsfoldername,rtmsmaxwindows), "ENTER"])

if __name__ == '__main__':
    if len(sys.argv) > 1:
       if sys.argv[1] == "1": 
        repo=tsslogging.getrepo()
        try:            
          tsslogging.tsslogit("Preprocessing3 DAG in {}".format(os.path.basename(__file__)), "INFO" )                     
          tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")    
        except Exception as e:
            #git push -f origin main
            try:
              os.chdir("/{}".format(repo))
              subprocess.call("git push -f origin main", shell=True)
            except Exception as e:
              pass
        
        VIPERTOKEN = sys.argv[2]
        VIPERHOST = sys.argv[3] 
        VIPERPORT = sys.argv[4]                  
        maxrows =  sys.argv[5]
        default_args['maxrows'] = maxrows
        subprocess.Popen("/tmux/rtmstrunc.sh", shell=True)

        searchterms =  sys.argv[6]
        default_args['searchterms'] = searchterms
        rememberpastwindows =  sys.argv[7]
        default_args['rememberpastwindows'] = rememberpastwindows
        patternwindowthreshold =  sys.argv[8]
        default_args['patternwindowthreshold'] = patternwindowthreshold
        rawdatatopic =  sys.argv[9]
        default_args['raw_data_topic'] = rawdatatopic
        rtmsstream =  sys.argv[10]
        default_args['rtmsstream'] = rtmsstream

        rtmsscorethreshold =  sys.argv[11]
        default_args['rtmsscorethreshold'] = rtmsscorethreshold
        attackscorethreshold =  sys.argv[12]
        default_args['attackscorethreshold'] = attackscorethreshold
        patternscorethreshold =  sys.argv[13]
        default_args['patternscorethreshold'] = patternscorethreshold

        localsearchtermfolder =  sys.argv[14]
        default_args['localsearchtermfolder'] = localsearchtermfolder
        localsearchtermfolderinterval =  sys.argv[15]
        default_args['localsearchtermfolderinterval'] = localsearchtermfolderinterval
        rtmsfoldername =  sys.argv[16]
        default_args['rtmsfoldername'] = rtmsfoldername
        rtmsmaxwindows =  sys.argv[17]
        default_args['rtmsmaxwindows'] = rtmsmaxwindows

        tsslogging.locallogs("INFO", "STEP 4c: Preprocessing 3 started")
        try:
          shutil.rmtree("/rawdata/{}".format(rtmsfoldername),ignore_errors=True)
        except Exception as e:
           pass
          
        try:
         directory="/rawdata/{}".format(rtmsfoldername)         
         if not os.path.exists(directory):
            os.makedirs(directory)
        except Exception as e:
           tsslogging.locallogs("ERROR", "STEP 4c: Cannot make directory /rawdata/{} in {} {}".format(rtmsfoldername,os.path.basename(__file__),e))         

        startdirread()
        while True:
          try: 
            processtransactiondata()
            time.sleep(1)
          except Exception as e:     
           tsslogging.locallogs("ERROR", "STEP 4c: Preprocessing3 DAG in {} {}".format(os.path.basename(__file__),e))
           tsslogging.tsslogit("Preprocessing3 DAG in {} {}".format(os.path.basename(__file__),e), "ERROR" )                     
           tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")    
           break
