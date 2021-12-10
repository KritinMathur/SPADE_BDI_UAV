#!/usr/bin/env python3

import asyncio
from mavsdk import System
from mavsdk.mission import (MissionItem, MissionPlan)


async def connect_mav():

    drone = System(port = 50041)
    await drone.connect(system_address="udp://:14541")

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

    return drone

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

    print("-- Disarming")
    await drone.action.disarm()


async def get_telemetry(drone):

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

    return telem_unit
    

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(connect_mav())