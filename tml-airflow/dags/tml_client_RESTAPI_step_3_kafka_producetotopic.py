import requests
import sys

sys.dont_write_bytecode = True
 
# defining the api-endpoint
rest_port = "9001"  # <<< ***** Change Port to match the Server Rest_PORT

# Modify the apiroute: jsondataline, or jsondataarray
# 1. jsondataline: You can send One Json message at a time
# 1. jsondatarray: You can send a Json array 

apiroute = "jsondataline"

API_ENDPOINT = "http://localhost:{}/{}".format(rest_port,apiroute)
 
def send_tml_data(data): 
  # data to be sent to api
 
  # sending post request and saving response as response object
  r = requests.post(url=API_ENDPOINT, data=data)
 
  # extracting response text
  return r.text
    

def start():
    
      ######### Modify datajson as you need ##############  
      try:  
        datajson = {"Type": "data1 data 2", "Value": "value 1"}   # << ** This json would normal come from some device, or you read from a file   
        ret = send_tml_data(datajson)
        print(ret)  
      except Exception as e:
        print("ERROR: ",e) 
        
if __name__ == '__main__':
    start()
