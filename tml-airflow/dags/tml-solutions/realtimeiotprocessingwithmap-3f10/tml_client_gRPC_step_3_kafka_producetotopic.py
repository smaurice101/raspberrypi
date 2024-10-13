import grpc
import tml_grpc_pb2_grpc as pb2_grpc
import tml_grpc_pb2 as pb2
import sys
from datetime import datetime
import time

sys.dont_write_bytecode = True

class TmlgrpcClient(object):
    """
    Client for gRPC functionality
    """

    def __init__(self):
        self.host = 'localhost'
        self.server_port = 9002 # <<<<*********** Change to gRPC server port

        # instantiate a channel
        self.channel = grpc.insecure_channel(
            '{}:{}'.format(self.host, self.server_port))

        # bind the client and the server
        self.stub = pb2_grpc.TmlprotoStub(self.channel)

    def sendtotmlgrpcserver(self, message):
        """
        Client function to call the rpc for GetServerResponse
        """
        message = pb2.Message(message=message)
        print(f'{message}')
        return self.stub.GetServerResponse(message)

    def readdata(self, inputfile):
        
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
        print("line2=",line)
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
          ret = self.sendtotmlgrpcserver(line)
          print(ret)
          # change time to speed up or slow down data   
          time.sleep(.5)
        except Exception as e:
          print(e)
          time.sleep(.5)
          pass


if __name__ == '__main__':
    try:
      client = TmlgrpcClient()
      inputfile = "IoTDatasample.txt"
      result = client.readdata(inputfile)
      print(f'{result}')
    except Exception as e:
      print("ERROR: ",e)
