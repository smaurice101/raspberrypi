from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime
from airflow.decorators import dag, task
import paho.mqtt.client as paho
from paho import mqtt
import sys
import maadstml
import tsslogging
import os
import subprocess
import time
import random
import json

sys.dont_write_bytecode = True
##################################################  MQTT SERVER #####################################
# This is a MQTT server that will handle connections from a client.  It will handle connections
# from an MQTT client for on_message, on_connect, and on_subscribe

# If Connecting to HiveMQ cluster you will need USERNAME/PASSWORD and mqtt_enabletls = 1
# USERNAME/PASSWORD should be set in your DOCKER RUN command of the TSS container

######################################## USER CHOOSEN PARAMETERS ########################################
default_args = {
  'owner' : 'Sebastian Maurice',    
  'enabletls': '1',
  'microserviceid' : '',
  'producerid' : 'iotsolution',  
  'topics' : 'iot-raw-data', # *************** This is one of the topic you created in SYSTEM STEP 2
  'identifier' : 'TML solution',  
  'mqtt_broker' : '', # <<<****** Enter MQTT broker i.e. test.mosquitto.org
  'mqtt_port' : '', # <<<******** Enter MQTT port i.e. 1883, 8883    (for HiveMQ cluster)
  'mqtt_subscribe_topic' : '', # <<<******** enter name of MQTT to subscribe to i.e. tml/iot  
  'mqtt_enabletls': '0', # set 1=TLS, 0=no TLSS  
  'delay' : '7000', # << ******* 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic
  'topicid' : '-999', # <<< ********* do not modify      
}

######################################## DO NOT MODIFY BELOW #############################################

    
# This sets the lat/longs for the IoT devices so it can be map
VIPERTOKEN=""
VIPERHOST=""
VIPERPORT=""
HTTPADDR=""  
VIPERHOSTFROM=""
    
# setting callbacks for different events to see if it works, print the message etc.
def on_connect(client, userdata, flags, rc, properties=None):
  print("CONNACK received with code %s." % rc)

# print which topic was subscribed to
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
  print("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_message(client, userdata, msg):
  data=json.loads(msg.payload.decode("utf-8"))
  datad = json.dumps(data)
  readdata(datad)

def mqttserverconnect():

 repo = tsslogging.getrepo()
 tsslogging.tsslogit("MQTT producing DAG in {}".format(os.path.basename(__file__)), "INFO" )                     
 tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")        

 username = ""    
 password = ""   
 if 'MQTTUSERNAME' in os.environ:
       username = os.environ['MQTTUSERNAME']  
 if 'MQTTPASSWORD' in os.environ:
       password = os.environ['MQTTPASSWORD']  
 
 try: 
   client = paho.Client(paho.CallbackAPIVersion.VERSION2)
   mqttBroker = default_args['mqtt_broker'] 
   mqttport = int(default_args['mqtt_port'])
   if default_args['mqtt_enabletls'] == "1":
     client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
     client.username_pw_set(username, password)
 except Exception as e:       
   tsslogging.locallogs("ERROR", "Cannot connect to MQTT broker in {} - {}".format(os.path.basename(__file__),e))    
    
   tsslogging.tsslogit("ERROR: Cannot connect to MQTT broker in {} - {}".format(os.path.basename(__file__),e), "ERROR" )                     
   tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")        
   print("ERROR: Cannot connect to MQTT broker") 
   return 

 client.connect(mqttBroker,mqttport)

 if client:
   print("Connected")   
   tsslogging.locallogs("INFO", "MQTT connection established...")
   client.on_subscribe = on_subscribe
   client.on_message = on_message
   client.subscribe(default_args['mqtt_subscribe_topic'], qos=1)            
   client.on_connect = on_connect
   client.loop_forever()
 else:   
    print("Cannot Connect")   
    tsslogging.locallogs("ERROR", "Cannot connect to MQTT broker in {} - {}".format(os.path.basename(__file__),e)) 
    tsslogging.tsslogit("CANNOT Connect to MQTT Broker in {}".format(os.path.basename(__file__)), "ERROR" )                     
    tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")        
    

def producetokafka(value, tmlid, identifier,producerid,maintopic,substream,args):
 inputbuf=value     
 topicid=int(args['topicid'])

 # Add a 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic 
 delay=int(args['delay'])
 enabletls = int(args['enabletls'])
 identifier = args['identifier']

 try:
    result=maadstml.viperproducetotopic(VIPERTOKEN,VIPERHOST,VIPERPORT,maintopic,producerid,enabletls,delay,'','', '',0,inputbuf,substream,
                                        topicid,identifier)
 except Exception as e:
    print("ERROR:",e)

    
def readdata(valuedata):
  # MAin Kafka topic to store the real-time data
  maintopic = default_args['topics']
  producerid = default_args['producerid']
  try:
      producetokafka(valuedata, "", "",producerid,maintopic,"",default_args)
      # change time to speed up or slow down data   
      #time.sleep(0.15)
  except Exception as e:
      print(e)  
      pass  

def windowname(wtype,sname,dagname):
    randomNumber = random.randrange(10, 9999)
    wn = "python-{}-{}-{},{}".format(wtype,randomNumber,sname,dagname)
    with open("/tmux/pythonwindows_{}.txt".format(sname), 'a', encoding='utf-8') as file: 
      file.writelines("{}\n".format(wn))
    
    return wn

def startproducing(**context):
       global VIPERTOKEN
       global VIPERHOST
       global VIPERPORT
       global HTTPADDR
       global VIPERHOSTFROM

       tsslogging.locallogs("INFO", "STEP 3: producing data started")    
        
       sd = context['dag'].dag_id
       sname=context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_solutionname".format(sd))

       VIPERTOKEN = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERTOKEN".format(sname))
       VIPERHOST = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERHOSTPRODUCE".format(sname))
       VIPERPORT = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERPORTPRODUCE".format(sname))
       HTTPADDR = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_HTTPADDR".format(sname))

       hs,VIPERHOSTFROM=tsslogging.getip(VIPERHOST)     
       ti = context['task_instance']
       ti.xcom_push(key="{}_PRODUCETYPE".format(sname),value='MQTT')
       ti.xcom_push(key="{}_TOPIC".format(sname),value=default_args['topics'])
       buf = default_args['mqtt_broker'] + ":" + default_args['mqtt_port']   
       ti.xcom_push(key="{}_CLIENTPORT".format(sname),value="")  
       buf="MQTT Subscription Topic: " + default_args['mqtt_subscribe_topic']   
       ti.xcom_push(key="{}_IDENTIFIER".format(sname),value=buf)
       ti.xcom_push(key="{}_FROMHOST".format(sname),value="{},{}".format(hs,VIPERHOSTFROM))
       ti.xcom_push(key="{}_TOHOST".format(sname),value=VIPERHOST)

       ti.xcom_push(key="{}_TSSCLIENTPORT".format(sname),value="_{}".format(default_args['mqtt_port']))
       ti.xcom_push(key="{}_TMLCLIENTPORT".format(sname),value="_{}".format(default_args['mqtt_port']))

       ti.xcom_push(key="{}_PORT".format(sname),value=VIPERPORT)
       ti.xcom_push(key="{}_HTTPADDR".format(sname),value=HTTPADDR)
       sd = context['dag'].dag_id
       sname=context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_solutionname".format(sd))
        
       chip = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_chip".format(sname))          
       repo=tsslogging.getrepo() 
       if sname != '_mysolution_':
        fullpath="/{}/tml-airflow/dags/tml-solutions/{}/{}".format(repo,sname,os.path.basename(__file__))  
       else:
         fullpath="/{}/tml-airflow/dags/{}".format(repo,os.path.basename(__file__))  
            
       wn = windowname('produce',sname,sd)      
       subprocess.run(["tmux", "new", "-d", "-s", "{}".format(wn)])
       subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "cd /Viper-produce", "ENTER"])
       subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "python {} 1 {} {}{} {}".format(fullpath,VIPERTOKEN,HTTPADDR,VIPERHOSTFROM,VIPERPORT[1:]), "ENTER"])        
       
    
if __name__ == '__main__':
    
    if len(sys.argv) > 1:
       if sys.argv[1] == "1":          
         VIPERTOKEN = sys.argv[2]
         VIPERHOST = sys.argv[3] 
         VIPERPORT = sys.argv[4]                  
        
         mqttserverconnect()
