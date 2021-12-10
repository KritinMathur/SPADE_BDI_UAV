import argparse

import agentspeak
from spade import quit_spade

from spade_bdi.bdi import BDIAgent

import asyncio
import takeoff_action

parser = argparse.ArgumentParser(description='spade bdi basic example')
parser.add_argument('--server', type=str, default="localhost", help='XMPP server address.')
parser.add_argument('--name', type=str, default="test", help='XMPP name for the agent.')
parser.add_argument('--password', type=str, default="password", help='XMPP password for the agent.')
arguments = parser.parse_args()


class MyCustomBDIAgent(BDIAgent):
    def add_custom_actions(self, actions):
        @actions.add_function(".my_function", (int,))
        def _my_function(x):

            asyncio.ensure_future(takeoff_action.run())

            return x * x

        @actions.add(".my_action", 1)
        def _my_action(agent, term, intention):
            arg = agentspeak.grounded(term.args[0], intention.scope)
            print(arg)
            yield


a = MyCustomBDIAgent("{}@{}".format(arguments.name, arguments.server), arguments.password, "/home/kritin/Desktop/SPADE_BDI_UAV/src/takeoff.asl")

a.start()

import time

time.sleep(15)
a.stop().result()

quit_spade()