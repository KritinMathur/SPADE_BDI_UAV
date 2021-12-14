#
#   Hello World client in Python
#   Connects REQ socket to tcp://localhost:5555
#   Sends "Hello" to server, expects "World" back
#

import zmq
import zmq.asyncio
import asyncio

context = zmq.asyncio.Context()

#  Socket to talk to server
print("Connecting to hello world server…")
socket = context.socket(zmq.PAIR)
socket.connect("tcp://localhost:5555")

#  Do 10 requests, waiting each time for a response

async def client_messenger():

    for request in range(10):
        print("Sending request %s …" % request)
        await socket.send(b'hello')

        #  Get the reply.
        message = await socket.recv()
        print("Received reply %s [ %s ]" % (request, message))

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(client_messenger())