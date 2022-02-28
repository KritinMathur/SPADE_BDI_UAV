#!/bin/bash 
export PX4_HOME_LAT=$1
export PX4_HOME_LON=$2
$3/Tools/gazebo_sitl_multiple_run.sh -n $4 -m typhoon_h480