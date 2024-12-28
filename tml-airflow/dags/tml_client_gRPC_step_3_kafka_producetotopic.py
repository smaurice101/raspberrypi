import grpc
import tml_grpc_pb2_grpc as pb2_grpc
import tml_grpc_pb2 as pb2
import sys
from datetime import datetime
import time
import os
import subprocess
import base64
import json
# Set kubernetes = 1 if TML solution running in kubernetes
# Set kubernetes = 0 if TML solution running in docker
import warnings
#warnings.filterwarnings("error")
host='tml.tss:443' 

sys.dont_write_bytecode = True

# NOTE YOU WILL NEED TO INSTALL grpcurl in Linux         
      
def sendgrpcurl(mjson):
    #first encode the json
    mainjson = '{"message":' + json.dumps(mjson) + '}' 
    
   # mainjson=pb2.Message(message=mjson)
    sent=0
    while sent==0:
            cmd="grpcurl -insecure -keepalive-time 10 -import-path . -proto tml_grpc.proto -d '{}' {} tmlproto.Tmlproto/GetServerResponse 2>/dev/null".format(mainjson,host)
           # print("CMD=",cmd.replace("\n",""))
            cmd=cmd.replace("\n","")
            print(cmd)
            proc = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
            out, err = proc.communicate()
            proc.terminate()
            proc.wait()
            
            if out.decode('utf-8')=="":
               sent=0
            else:
               print(out.decode('utf-8'))     
               sent=1
               break


def readdata(inputfile):
        
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
    #    print("line2=",line)
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
          #ret = sendtotmlgrpcserver(line)
          sendgrpcurl(line.rstrip())
          time.sleep(.0)
        except Exception as e:
          print("Main loop error=",e)
          time.sleep(.5)
          pass


if __name__ == '__main__':
    try:
      
      inputfile = "IoTData.txt"
      #result = readdata(inputfile) ##### UNCOMMENT TO READ FILE
      print(f'{result}')
    except Exception as e:
      print("ERROR: ",e)

