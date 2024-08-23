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

sys.dont_write_bytecode = True
##################################################  MQTT SERVER #####################################
# This is a MQTT server that will handle connections from a client.  It will handle connections
# from an MQTT client for on_message, on_connect, and on_subscribe

######################################## USER CHOOSEN PARAMETERS ########################################
default_args = {
  'owner' : 'Sebastian Maurice',    
  'enabletls': 1,
  'microserviceid' : '',
  'producerid' : 'iotsolution',  
  'topics' : 'iot-raw-data', # *************** This is one of the topic you created in SYSTEM STEP 2
  'identifier' : 'TML solution',  
  'mqtt_broker' : '', # <<<****** Enter MQTT broker i.e. test.mosquitto.org
  'mqtt_port' : '', # <<<******** Enter MQTT port i.e. 1883    
  'mqtt_subscribe_topic' : '', # <<<******** enter name of MQTT to subscribe to i.e. encyclopedia/#  
  'delay' : 7000, # << ******* 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic
  'topicid' : -999, # <<< ********* do not modify      
  'start_date': datetime (2024, 6, 29),
  'retries': 1,
    
}

######################################## DO NOT MODIFY BELOW #############################################

# Instantiate your DAG
@dag(dag_id="tml_mqtt_step_3_kafka_producetotopic_dag_mytmlsolution", default_args=default_args, tags=["tml_mqtt_step_3_kafka_producetotopic_dag_mytmlsolution"], schedule=None,catchup=False)
def startproducingtotopic():
  # This sets the lat/longs for the IoT devices so it can be map
  VIPERTOKEN=""
  VIPERHOST=""
  VIPERPORT=""
  
    
  # setting callbacks for different events to see if it works, print the message etc.
  def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)

  # print which topic was subscribed to
  def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

  data = ''
  def on_message(client, userdata, msg):
    global data
    data=json.loads(msg.payload.decode("utf-8"))
    print(msg.payload.decode("utf-8"))
    readdata(data)
    
  def mqttserverconnect():

     repo = tsslogging.getrepo()
     tsslogging.tsslogit("MQTT producing DAG in {}".format(os.path.basename(__file__)), "INFO" )                     
     tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")        
        
     ti.xcom_push(key='PRODUCETYPE',value='MQTT')
     ti.xcom_push(key='TOPIC',value=default_args['topics'])
     buf = default_args['mqtt_broker'] + ":" + default_args['mqtt_port']   
     ti.xcom_push(key='PORT',value=buf)
     buf="MQTT Subscription Topic: " + default_args['mqtt_subscribe_topic']   
     ti.xcom_push(key='IDENTIFIER',value=buf)
        
     client = paho.Client(paho.CallbackAPIVersion.VERSION2)
     mqttBroker = default_args['mqtt_broker'] 
     mqttport = default_args['mqtt_port']
     client.connect(mqttBroker,mqttport)
    
     if client:
       client.on_subscribe = on_subscribe
       client.on_message = on_message
       client.subscribe(args['mqtt_subscribe_topic'], qos=1)            
       client.on_connect = on_connect
    
       client.loop_start()
    
  def producetokafka(value, tmlid, identifier,producerid,maintopic,substream,args):
     inputbuf=value     
     topicid=args['topicid']
  
     # Add a 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic 
     delay=args['delay']
     enabletls = args['enabletls']
     identifier = args['identifier']

     try:
        result=maadstml.viperproducetotopic(VIPERTOKEN,VIPERHOST,VIPERPORT,maintopic,producerid,enabletls,delay,'','', '',0,inputbuf,substream,
                                            topicid,identifier)
     except Exception as e:
        print("ERROR:",e)

  @task(task_id="gettmlsystemsparams")         
  def gettmlsystemsparams(rc):
    VIPERTOKEN = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="VIPERTOKEN")
    VIPERHOST = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="VIPERHOST")
    VIPERPORT = ti.xcom_pull(dag_id='tml_system_step_1_getparams_dag',task_ids='getparams',key="VIPERPORT")
    
    mqttserverconnect()
        
  def readdata(valuedata):
      # MAin Kafka topic to store the real-time data
      maintopic = default_args['topics']
      producerid = default_args['producerid']
      try:
          producetokafka(valuedata.strip(), "", "",producerid,maintopic,"",default_args)
          # change time to speed up or slow down data   
          #time.sleep(0.15)
      except Exception as e:
          print(e)  
          pass  
   
dag = startproducingtotopic()
