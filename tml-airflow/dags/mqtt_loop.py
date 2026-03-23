import sys
import paho.mqtt.client as paho
from paho import mqtt
import maadstml
import json
import time
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scadaglobals as sg

#import nest_asyncio
#nest_asyncio.apply()

def producetokafka(value, tmlid, identifier,producerid,maintopic,substream,args,VIPERTOKEN,VIPERHOST,VIPERPORT):
 inputbuf=value     
 topicid=int(args['topicid'])

 # Add a 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic 
 delay=int(args['delay'])
 enabletls = int(args['enabletls'])
 identifier = args['identifier']

 try:
    result=maadstml.viperproducetotopic(VIPERTOKEN,VIPERHOST,VIPERPORT,maintopic,producerid,enabletls,delay,'','', '',0,inputbuf,substream,
                                        topicid,identifier)
    print("mqtt result==",result)
 except Exception as e:
    print("ERROR:",e)
    pass


def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)
    # subscribe once connected
    mqtt_cfg = client.userdata
    if rc == 0:
      print("Subscribing to MQTT topic:", mqtt_cfg['topic'])
      result=client.subscribe(mqtt_cfg["topic"], qos=1)
      print(f"Subscribe result: {result}")
    else:
      print(f"Subscribe failed")

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed fired: " + str(mid) + " " + str(granted_qos))


def on_message(client, userdata, msg):
    print(f"🔥 on_message FIRED! Topic: '{msg.topic}' Payload: {msg.payload}")
    try:
      data = json.loads(msg.payload.decode("utf-8"))
      data = json.dumps(data)
      mqtt_cfg = client.userdata 
      maintopic=mqtt_cfg['sendtotopic']
      producetokafka(data, "", "MQTT Broker","MQTT",maintopic,"",mqtt_cfg['default_args'],mqtt_cfg['VIPERTOKEN'],mqtt_cfg['VIPERHOST'],mqtt_cfg['VIPERPORT'])
    except Exception as e:
        print(f"🚨 on_message CRASH: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

def on_disconnect(client, userdata, rc):
    print("🚨 MQTT DISCONNECTED, rc=", rc)

def mqttserverconnect_threaded(mqtt_cfg, job_id):

    print("🧠 MQTT THREAD STARTED, job_id=", job_id, "mqtt_job=", sg.mqtt_job)

    #sg.mqtt_client = paho.Client(paho.CallbackAPIVersion.VERSION2)

    sg.mqtt_client = paho.Client(
       client_id=f"tml-client-{job_id}",
       clean_session=True,
       callback_api_version=paho.CallbackAPIVersion.VERSION2
    )


    sg.mqtt_client.userdata = mqtt_cfg

    print("connecting to MQTT")

    if mqtt_cfg["enable_tls"]:
        sg.mqtt_client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
        if mqtt_cfg["username"]:
            sg.mqtt_client.username_pw_set(mqtt_cfg["username"], mqtt_cfg["password"])

    sg.mqtt_client.on_connect = on_connect
    sg.mqtt_client.on_message = on_message
    sg.mqtt_client.on_subscribe = on_subscribe

    sg.mqtt_client.connect(mqtt_cfg["broker"], mqtt_cfg["port"])
    sg.mqtt_client.loop_start()
