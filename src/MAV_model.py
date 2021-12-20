import os
import time
from spade.agent import Agent
from spade.message import Message
from spade.template import Template
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade_pubsub import PubSubMixin
import json
import argparse
import agentspeak
from spade import quit_spade
from spade_bdi.bdi import BDIAgent
import asyncio
import zmq
import zmq.asyncio
import geospatial

HETRO_CHAR = {'socialization': 10, 'processing_power': 20}


class MAVAgent(PubSubMixin, BDIAgent):

    class MAVtoMAV(CyclicBehaviour):

        class Handle_Inform(CyclicBehaviour):
            async def run(self):
                
                msg = await self.receive()
                if msg is not None and mav.role == 'initiator':

                    distance_bw_ini_part = float(msg.body)
                    print("Distance between {} and {} = {} ".format(args.name,msg.sender,distance_bw_ini_part))

                await asyncio.sleep(1)

        class Handle_Request(CyclicBehaviour):
            async def run(self):
                # Getting location of participant
                msg = await self.receive()

                if msg is not None and mav.role == 'participant':

                    telem_unit_initiator = msg.body
                    telem_unit_initiator = json.loads(telem_unit_initiator)

                    # Get telemetry from controller
                    await mav.socket.send(b'get_telemetry')
                    telem_unit_participant = await mav.socket.recv()
                    telem_unit_participant = telem_unit_participant.decode()
                    print(telem_unit_participant)
                    telem_unit_participant = json.loads(telem_unit_participant)
                    print(telem_unit_participant)

                    lat1 = telem_unit_initiator['pos']['lat']
                    lon1 = telem_unit_initiator['pos']['lon']
                    lat2 = telem_unit_participant['pos']['lat']
                    lon2 = telem_unit_participant['pos']['lon']

                    # Calculate distance between participant & initiator
                    distance_bw_ini_part = geospatial.distance(lat1,lat2,lon1,lon2)
                    #print(distance_bw_ini_part)

                    if distance_bw_ini_part <= 150:
                        
                        sender_JID = msg.sender
                        msg = Message(to=f"{sender_JID}@{args.server}")
                        msg.set_metadata("performative", "inform")
                        msg.body = str(distance_bw_ini_part)

                        print('Sending inform from {} to {} '.format(args.name, sender_JID))
                        await self.send(msg)

                await asyncio.sleep(1)

        async def on_start(self):

            print('Starting MAV to MAV behaviour')
            self.counter = 0

        async def run(self):
            print("Counter: {}".format(self.counter))
            self.counter += 1

            if mav.role == 'initiator' and self.counter % 10 == 0:
                print(mav.role)
                
                # Get telemetry from controller
                await mav.socket.send(b'get_telemetry')
                telem_unit_initiator = await mav.socket.recv()
                telem_unit_initiator = telem_unit_initiator.decode()
                telem_unit_initiator = json.loads(telem_unit_initiator) 
            
                for counter_party in mav.counter_parties:

                    msg = Message(to=f"{counter_party}@{args.server}")
                    msg.set_metadata("performative", "request")
                    msg.body = json.dumps(telem_unit_initiator)

                    print('Sending request from {} to {} '.format(args.name, counter_party))
                    await self.send(msg)

            await asyncio.sleep(1)

    class MAVtoGCS(CyclicBehaviour):

        async def on_start(self):
            print('Starting MAV to GCS behaviour')
            self.counter = 0

        async def run(self):
            print("Counter: {}".format(self.counter))
            self.counter += 1

            command_payload = await mav.pubsub.get_items('pubsub.localhost', "Cmd_node")

            if command_payload:
                command_gcs_literal = command_payload[-1].data
                command_gcs = json.loads(command_gcs_literal)

                if command_gcs['ID'] == args.name:
                    await self.agent.pubsub.purge('pubsub.localhost', "Cmd_node")
                    print(command_gcs)

                    if command_gcs['data'] == 'mission':
                        print('Starting mission')

                        mav.bdi.set_belief('go_mission', 'positive')

                    if command_gcs['data'] == 'rtl':
                        print('RTL')

                        mav.bdi.set_belief('rtl', 'positive')

                    if command_gcs['data'] == 'get_info':
                        print('Sending telemetry data')

                        await mav.socket.send(b'get_telemetry')
                        telem_unit = await mav.socket.recv()
                        telem_unit = telem_unit.decode()
                        telem_unit = json.loads(telem_unit)
                        print(telem_unit)

                        payload = {'ID': 'test', 'data': {
                            'telem': telem_unit, 'characteristic': HETRO_CHAR}}
                        await mav.pubsub.purge('pubsub.localhost', "Telemetry_node")
                        await mav.pubsub.publish('pubsub.localhost', "Telemetry_node", json.dumps(payload))

            await asyncio.sleep(1)

    async def setup(self):

        # ROLE DEFINTION
        if args.name == 'test':
            self.role = 'initiator'
            self.counter_parties = ('test2','test3','test4','test5')
            self.presence.approve_all = True

        elif args.name == 'test2' or args.name == 'test3' or args.name == 'test4' or args.name == 'test5':
            self.role = 'participant'
            self.counter_parties = ('test',)
            self.approve_all = True
            
        else:
            self.role == None
            self.counter_party = None
        
        #Neighbour definition
        for counter_party in self.counter_parties:
            self.presence.subscribe(counter_party)

        print("neighbor list" ,self.presence.get_contacts())
        print("number of neighbors",len(self.presence.get_contacts()))

        # Drone Model-Controller socket
        self.context = zmq.asyncio.Context()
        print("Starting drone model controller server…")
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.bind(f"tcp://*:{args.mc_port}")

        # Adding behaviours

        print("GCS Agent starting . . .")
        m2g = self.MAVtoGCS()
        self.add_behaviour(m2g)

        print("IMAV Agent starting . . .")
        m2m = self.MAVtoMAV()
        self.add_behaviour(m2m)

        print('Creating Templates for FIPA . . .')
        request_template = Template()
        request_template.set_metadata("performative", "request")
        inform_template = Template()
        inform_template.set_metadata("performative", "inform")

        print('Adding FIPA Behvaiours . . .')
        req_behave = self.MAVtoMAV.Handle_Request()
        inf_behave = self.MAVtoMAV.Handle_Inform()

        if self.role == 'participant':
            self.add_behaviour(req_behave, request_template)

        if self.role == 'initiator':
            self.add_behaviour(inf_behave, inform_template)

    ####BDI###
    def add_custom_actions(self, actions):

        @actions.add_function(".mission", (int,))
        def _my_function(x):

            asyncio.ensure_future(mav.socket.send(b'do_mission'))
            return x

        @actions.add_function(".rtl", (int,))
        def _my_function(x):

            asyncio.ensure_future(mav.socket.send(b'do_rtl'))
            return x

        @actions.add(".reply", 1)
        def _my_action(agent, term, intention):
            arg = agentspeak.grounded(term.args[0], intention.scope)
            print(arg)
            yield


if __name__ == "__main__":

    global args
    parser = argparse.ArgumentParser(description='MAV_Model BDI')
    parser.add_argument('--server', type=str,
                        default="localhost", help='XMPP server address.')
    parser.add_argument('--name', type=str, default="test",
                        help='XMPP name for the agent.')
    parser.add_argument('--password', type=str,
                        default="password", help='XMPP password for the agent.')
    parser.add_argument('--autopilot', type=str, default="px4",
                        help='Agent autopilot software.')
    parser.add_argument('--uav_add', type=str,
                        default='udp://:14540', help='UAV system address')
    parser.add_argument('--uav_port', type=int, default=50040,
                        help='MAVSDK Server port (only required for PX4)')
    parser.add_argument('--mc_port', type=int, default=5555,
                        help='model controller port')
    args = parser.parse_args()

    if args.autopilot == 'px4':
        os.system('xterm -e python3 src/MAV_controller_px4.py --uav_add {} --uav_port {} --mc_port {} &'.format(
            args.uav_add, args.uav_port, args.mc_port))

    mav = MAVAgent("{}@{}".format(args.name, args.server),
                   args.password, './src/behave.asl')
    future = mav.start()
    future.result()

    #print("Wait until user interrupts with ctrl+C")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")

    if args.autopilot == 'px4':
        os.system('pkill -9 -f MAV_controller_px4.py')
    mav.stop()
