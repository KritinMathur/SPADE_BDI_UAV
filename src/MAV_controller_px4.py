#!/usr/bin/env python3

import asyncio
import zmq
import zmq.asyncio
from mavsdk import System
from mavsdk.mission import (MissionItem, MissionPlan)
import json
import argparse

global cont_args
parser = argparse.ArgumentParser(description='MAV_Model BDI')
parser.add_argument('--uav_add', type =str, default='udp://:14540',help='UAV system address')
parser.add_argument('--uav_port', type =int, default=50040, help='MAVSDK Server port (only required for PX4)')
parser.add_argument('--mc_port', type =int, default=5555, help = 'model controller port')
cont_args = parser.parse_args()

async def connect_mav():

    drone = System(port=cont_args.uav_port)
    await drone.connect(system_address=cont_args.uav_add)

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"Drone discovered!")
            break

    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok:
            print("Global position estimate ok")
            break

    cmd_context = zmq.asyncio.Context()
    telem_context = zmq.asyncio.Context()

    #  Socket to talk to server
    print("Connecting to drone model controller server…")
    cmd_socket = cmd_context.socket(zmq.PAIR)
    cmd_socket.connect(f"tcp://localhost:{cont_args.mc_port}")
    telem_socket = telem_context.socket(zmq.PAIR)
    telem_socket.connect(f"tcp://localhost:{str(int(cont_args.mc_port)+1000)}")

    ## Task list
    mission_task,rtl_task = None,None
    

    while True:
        telem_task = asyncio.ensure_future(pub_telemetry(drone,telem_socket))

        print('controller - waiting to recv')
        message = await cmd_socket.recv()

        try:
            telem_task.cancel()
        except:
            pass
        
        print('controller - received message')

        print("Received [ %s ]" % message)
        message = message.decode()
        print(message)

        if str(message) == 'do_mission' :

            if rtl_task:
                rtl_task.cancel()

            mission_task = asyncio.ensure_future(do_mission(drone))

        if str(message) == 'do_rtl':

            if mission_task:
                mission_task.cancel()

            rtl_task = asyncio.ensure_future(do_rtl(drone))

        if str(message) == 'do_land':

            if mission_task:
                mission_task.cancel()

            if rtl_task:
                rtl_task.cancel()

            land_task = asyncio.ensure_future(do_land(drone))

        if str(message) == 'do_inc_altitude':

            if mission_task:
                mission_task.cancel()
            if rtl_task:
                rtl_task.cancel()

            inc_altitude_task = asyncio.ensure_future(do_inc_altitude(drone))

        await asyncio.sleep(1)


async def do_takeoff(drone):
    print("-- Arming")
    await drone.action.arm()

    print("-- Taking off")
    await drone.action.takeoff()

    await asyncio.sleep(8)

    print("-- Landing")
    await drone.action.land()


async def do_mission(drone):
    mission_items = []
    mission_items.append(MissionItem(47.398039859999997,
                                     8.5455725400000002,
                                     25,
                                     10,
                                     True,
                                     float('nan'),
                                     float('nan'),
                                     MissionItem.CameraAction.NONE,
                                     float('nan'),
                                     float('nan'),
                                     float('nan'),
                                     float('nan'),
                                     float('nan')))
    mission_items.append(MissionItem(47.398036222362471,
                                     8.5450146439425509,
                                     25,
                                     10,
                                     True,
                                     float('nan'),
                                     float('nan'),
                                     MissionItem.CameraAction.NONE,
                                     float('nan'),
                                     float('nan'),
                                     float('nan'),
                                     float('nan'),
                                     float('nan')))
    mission_items.append(MissionItem(47.397825620791885,
                                     8.5450092830163271,
                                     25,
                                     10,
                                     True,
                                     float('nan'),
                                     float('nan'),
                                     MissionItem.CameraAction.NONE,
                                     float('nan'),
                                     float('nan'),
                                     float('nan'),
                                     float('nan'),
                                     float('nan')))

    mission_plan = MissionPlan(mission_items)

    print("-- Uploading mission")
    await drone.mission.upload_mission(mission_plan)

    print("-- Arming")
    await drone.action.arm()

    print("-- Starting mission")
    await drone.mission.start_mission()

    async for mission in drone.mission.mission_progress():
        print(mission)

        if await drone.mission.is_mission_finished():
            break

async def do_rtl(drone):
    print("-- Returning to Launch")
    await drone.action.return_to_launch()

    async for is_in_air in drone.telemetry.in_air():
        if not is_in_air:
            break

        await asyncio.sleep(1)

    print("-- Disarming")
    await drone.action.disarm()

async def do_land(drone):
    print("-- Land")
    await drone.action.land()

    async for is_in_air in drone.telemetry.in_air():
        if not is_in_air:
            break

        await asyncio.sleep(1)

    print("-- Disarming")
    await drone.action.disarm()


async def do_inc_altitude(drone):
    await drone.action.hold()
    
    telem_unit = {}

    async for position in drone.telemetry.position():
        telem_unit['pos'] = {'lat':position.latitude_deg,'lon':position.longitude_deg,'alt_rel':position.relative_altitude_m,'alt_abs':position.absolute_altitude_m}
        break    

    await drone.action.goto_location(telem_unit['pos']['lat'], telem_unit['pos']['lon'], telem_unit['pos']['alt_abs']+10, 0)


async def pub_telemetry(drone,telem_socket):

    while True:

        telem_unit = {}

        async for battery in drone.telemetry.battery():
            telem_unit['batt'] = battery.remaining_percent
            break

        async for gps_info in drone.telemetry.gps_info():
            telem_unit['gps'] = {'num_sat' : gps_info.num_satellites , 'fix_type' : gps_info.fix_type.name}
            break

        async for in_air in drone.telemetry.in_air():
            telem_unit['state'] = in_air
            break

        async for position in drone.telemetry.position():
            telem_unit['pos'] = {'lat':position.latitude_deg,'lon':position.longitude_deg,'alt_rel':position.relative_altitude_m,'alt_abs':position.absolute_altitude_m}
            break

        telem_unit = json.dumps(telem_unit)
        await telem_socket.send(telem_unit.encode())
        await asyncio.sleep(1)
    

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(connect_mav())