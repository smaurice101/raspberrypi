import paho.mqtt.client as paho
from paho import mqtt
import time
import sys
from datetime import datetime

default_args = {
    'mqtt_broker': '08b9fcbd4d00421daa25c0ee4a44b494.s1.eu.hivemq.cloud',
    'mqtt_port': '8883',
    'mqtt_subscribe_topic': 'tml/iot',
    'mqtt_enabletls': '1',
}

sys.dont_write_bytecode = True

def on_connect(client, userdata, flags, rc, properties=None):
    """rc=0 = SUCCESS"""
    print(f"MQTT CONNACK: rc={rc}")
    if rc == 0:
        print("✅ Connected successfully")
        client.connected_flag = True
        client.subscribe(default_args['mqtt_subscribe_topic'], qos=1)
    else:
        print(f"❌ Connection failed - rc={rc}")
        client.connected_flag = False

def mqttconnection():
    username = "<Enter MQTT Username>"
    password = "<Enter MQTT Password>"
    
    client = paho.Client(paho.CallbackAPIVersion.VERSION2)
    client.connected_flag = False  # Reset flag
    
    mqttBroker = default_args['mqtt_broker']
    mqttport = int(default_args['mqtt_port'])
    
    # ✅ CRITICAL: Set callback BEFORE connect
    client.on_connect = on_connect
    
    # TLS + Auth
    client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
    client.username_pw_set(username, password)
    
    print("Connecting...")
    client.connect(mqttBroker, mqttport)
    
    # ✅ WAIT FOR CALLBACK - don't subscribe immediately
    timeout = 10
    start_time = time.time()
    while not client.connected_flag and (time.time() - start_time) < timeout:
        time.sleep(0.1)
        client.loop(timeout=0.1)  # Process network
    
    if client.connected_flag:
        print("✅ Connection confirmed - starting loop")
        return client
    else:
        print("❌ Connection timeout")
        return None

def publishtomqttbroker(client, line):
    try:
        result = client.publish(
            topic=default_args['mqtt_subscribe_topic'], 
            payload=line, 
            qos=1, 
            retain=False
        )
        print(f"Published: {result.rc}")
    except Exception as e:
        print("Publish ERROR:", e)

def readdatafile(client, inputfile):
    try:
        file1 = open(inputfile, 'r')
        print("Data producing started:", datetime.now())
    except Exception as e:
        print("ERROR opening file:", e)
        return
    
    k = 0
    while client and client.connected_flag:
        line = file1.readline().strip()
        if not line:
            file1.seek(0)
            continue
        print(line)        
        publishtomqttbroker(client, line)
        time.sleep(0.15)
    
    file1.close()

if __name__ == "__main__":
    client = mqttconnection()
    if client:
        inputfile = "IoTDatasample.txt"
        readdatafile(client, inputfile)
        client.loop_forever()  # Keep alive
    else:
        print("Cannot start - MQTT connection failed")
