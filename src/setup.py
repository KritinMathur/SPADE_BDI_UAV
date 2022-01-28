from spade.agent import Agent
from spade_pubsub import PubSubMixin
import argparse

class setupAgent(PubSubMixin,Agent):

    async def setup(self):
        await self.pubsub.create('pubsub.localhost', "Telemetry_node")
        await self.pubsub.create('pubsub.localhost', "Cmd_node")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='MAV_Model BDI')
    parser.add_argument('--server', type=str, default="localhost", help='XMPP server address.')
    parser.add_argument('--name', type=str, default="test", help='XMPP name for the agent.')
    parser.add_argument('--password', type=str, default="password", help='XMPP password for the agent.')
    args = parser.parse_args()

    sa = setupAgent("{}@{}".format(args.name, args.server), args.password)
    future = sa.start()
    future.result()
    sa.stop()