import time
import asyncio
import aioconsole
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade_pubsub import PubSubMixin
import json

import argparse
import agentspeak
from spade import quit_spade
from spade_bdi.bdi import BDIAgent
import asyncio

import MAV_controller2

AUTOPILOT = 'PX4'
HETRO_CHAR = { 'socialization' : 10, 'processing_power' : 20 }

class MAVAgent(PubSubMixin,BDIAgent):

    class MAVtoGCS(CyclicBehaviour):

        async def on_start(self):
            print("Starting behaviour . . .")
            self.counter = 0

        async def run(self):
            print("Counter: {}".format(self.counter))
            self.counter += 1

            command_payload = await mav.pubsub.get_items('pubsub.localhost', "Cmd_node")
            
            if command_payload:
                command_gcs_literal = command_payload[-1].data
                command_gcs = json.loads(command_gcs_literal)

                if command_gcs['ID'] == 'test2':
                    await self.agent.pubsub.purge('pubsub.localhost', "Cmd_node")
                    print(command_gcs)

                    if command_gcs['data'] == 'mission':
                        print('Starting mission')
                        # -> set belief to go_mission uav.agent.bdi.set_belief('mission', 'go')
                        #asyncio.ensure_future(MAV_controller2.do_mission(mav.drone))
                        mav.bdi.set_belief('go_mission','positive')

                    if command_gcs['data'] == 'rtl':
                        print('RTL')
                        #asyncio.ensure_future(MAV_controller2.do_rtl(mav.drone))
                        mav.bdi.set_belief('rtl','positive')

                    if command_gcs['data'] == 'get_info':
                        print('Sending telemetry data')

                        telem_unit = await MAV_controller2.get_telemetry(mav.drone)
                        print(telem_unit)

                        payload = {'ID' : 'test2', 'data' : { 'telem' : telem_unit , 'characteristic' : HETRO_CHAR } }
                        await mav.pubsub.purge('pubsub.localhost', "Telemetry_node")
                        await mav.pubsub.publish('pubsub.localhost', "Telemetry_node", json.dumps(payload))


            await asyncio.sleep(1)


    async def setup(self):
        print("GCS Agent starting . . .")
        m2g = self.MAVtoGCS()
        self.add_behaviour(m2g)

        
        self.drone = await MAV_controller2.connect_mav()

        #await self.pubsub.create('pubsub.localhost', "Telemetry_node")


    ####BDI###
    def add_custom_actions(self, actions):

        @actions.add_function(".mission", (int,))
        def _my_function(x):

            asyncio.ensure_future(MAV_controller2.do_mission(mav.drone))

            return x

        @actions.add_function(".rtl", (int,))
        def _my_function(x):

            asyncio.ensure_future(MAV_controller2.do_rtl(mav.drone))

            return x

        @actions.add(".reply", 1)
        def _my_action(agent, term, intention):
            arg = agentspeak.grounded(term.args[0], intention.scope)
            print(arg)
            yield

if __name__ == "__main__":
    mav = MAVAgent("test2@localhost", "password",'/home/kritin/Desktop/SPADE_BDI_UAV/src/behave.asl')
    future = mav.start()
    future.result()

    #print("Wait until user interrupts with ctrl+C")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
    mav.stop()