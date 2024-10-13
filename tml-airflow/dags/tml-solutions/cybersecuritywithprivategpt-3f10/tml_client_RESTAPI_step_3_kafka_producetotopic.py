import requests
import sys
from datetime import datetime
import time
import json

sys.dont_write_bytecode = True
 
# defining the api-endpoint
rest_port = "9001"  # <<< ***** Change Port to match the Server Rest_PORT
httpaddr = "http:" # << Change to https or http

# Modify the apiroute: jsondataline, or jsondataarray
# 1. jsondataline: You can send One Json message at a time
# 1. jsondatarray: You can send a Json array 

apiroute = "jsondataline"

API_ENDPOINT = "{}//localhost:{}/{}".format(httpaddr,rest_port,apiroute)
 
def send_tml_data(data): 
  # data to be sent to api
  headers = {'Content-type': 'application/json'}
  r = requests.post(url=API_ENDPOINT, data=json.dumps(data), headers=headers)

  # extracting response text
  return r.text
    

def readdatafile(inputfile):

  ##############################################################
  # NOTE: You can send any "EXTERNAL" data through this API
  # It is reading a localfile as an example
  ############################################################
  
  try:
    file1 = open(inputfile, 'r')
    print("Data Producing to Kafka Started:",datetime.now())
  except Exception as e:
    print("ERROR: Something went wrong ",e)  
    return
  k = 0
  while True:
    line = file1.readline()
    line = line.replace(";", " ")
    print("line=",line)
    # add lat/long/identifier
    k = k + 1
    try:
      if line == "":
        #break
        file1.seek(0)
        k=0
        print("Reached End of File - Restarting")
        print("Read End:",datetime.now())
        continue
      ret = send_tml_data(line)
      print(ret)
      # change time to speed up or slow down data   
      time.sleep(.5)
    except Exception as e:
      print(e)
      time.sleep(0.5)
      pass
    
def start():
      inputfile = "IoTDatasample.txt"
      readdatafile(inputfile)
        
if __name__ == '__main__':
    start()
