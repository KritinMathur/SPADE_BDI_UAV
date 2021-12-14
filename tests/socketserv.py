#
#   Hello World server in Python
#   Binds REP socket to tcp://*:5555
#   Expects b"Hello" from client, replies with b"World"
#

import asyncio
import zmq
import zmq.asyncio


context = zmq.asyncio.Context()
socket = context.socket(zmq.PAIR)
socket.bind("tcp://*:5555")


async def server_messenger():
    while True:
        #  Wait for next request from client
        message = await socket.recv()
        print("Received request: %s" % message)

        #  Do some 'work'
        await asyncio.sleep(1)

        #  Send reply back to client
        await socket.send(b'world')

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(server_messenger())