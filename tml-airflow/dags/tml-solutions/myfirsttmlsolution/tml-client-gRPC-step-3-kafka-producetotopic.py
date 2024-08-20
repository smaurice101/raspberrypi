import grpc
import tml_grpc_pb2_grpc as pb2_grpc
import tml_grpc_pb2 as pb2
import sys

sys.dont_write_bytecode = True

class TmlgrpcClient(object):
    """
    Client for gRPC functionality
    """

    def __init__(self):
        self.host = 'localhost'
        self.server_port = 9001 # <<<<*********** Change to gRPC server port

        # instantiate a channel
        self.channel = grpc.insecure_channel(
            '{}:{}'.format(self.host, self.server_port))

        # bind the client and the server
        self.stub = pb2_grpc.TmlprotoStub(self.channel)

    def get_url(self, message):
        """
        Client function to call the rpc for GetServerResponse
        """
        message = pb2.Message(message=message)
        print(f'{message}')
        return self.stub.GetServerResponse(message)


if __name__ == '__main__':
    try:
      client = TmlgrpcClient()
      result = client.get_url(message="PUT YOUR DATA HERE")
      print(f'{result}')
    except Exception as e:
      print("ERROR: ",e)
