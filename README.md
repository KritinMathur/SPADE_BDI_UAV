## About the project 
Desktop application designed to test distributed communication protocols with heterogeneous SITL-MAVs.

### Built with

* [MAVSDK python](https://mavsdk.mavlink.io/main/en/)
* [SPADE](https://spade-mas.readthedocs.io/en/latest/readme.html)
* [SPADE_BDI](https://github.com/javipalanca/spade_bdi)
* [SPAD_PubSub](https://spade-pubsub.readthedocs.io/en/latest/)
* [Prosody XMPP server](https://prosody.im/doc/xmpp)
* [AgentSpeak(L)](http://astralanguage.com/wordpress/docs/introduction-to-agentspeakl/)
* [ZeroMQ](https://zeromq.org/)

## Getting Started

This is an example of how you may set up your project locally. To get a local copy up and running follow these simple steps.

### Prerequisites

>ensure `python 3.6` or greater is installed on the host PC. Testing has been done with `python 3.8` and `pip 20.0.2`


* Install [prosody](https://prosody.im/download/start) XMPP server
```bash
sudo apt-get install prosody
```

* Install [PX4-Firmware]() and Toolchain

```bash
git clone https://github.com/PX4/PX4-Autopilot.git --recursive
bash ./PX4-Autopilot/Tools/setup/ubuntu.sh
```



### Installation

1. clone the github repository
```bash
git clone https://github.com/KritinMathur/SPADE_BDI_UAV.git
```

2. install the required packages

```bash
pip install -r requirements.txt
```

> Creating a virtual environment is advisable. Click [here]() to know more about setting up virtual environments.

### Server setup

1. edit server config file in `nano`

```bash
sudo nano /etc/prosody/prosody.cfg.lua
```

2. add the following line of code at the botttom of the server config file

```lua
Component "pubsub.localhost" "pubsub"
```

3. modify the empty admins JSON by adding test@localhost ,test2@localhost,test3@localhost,test4@localhost,test5@localhost and gcs@localhost

```lua
admins = {"test@localhost","test2@localhost","test3@localhost","test4@localhost","test5@localhost","gcs@localhost" }
```

4. save and exit using `ctrl + x`,then press `y` to save  change. 

5. Execute the following commands to register agents in the prosody server
```
prosodyctl register test localhost password
prosodyctl register test2 localhost password
prosodyctl register test3 localhost password
prosodyctl register test4 localhost password
prosodyctl register test5 localhost password
prosodyctl register gcs localhost password
```

6. Execute `setup.py` to create pubsub nodes

```bash
cd path/to/SPADE_BDI_UAV
python3 src/setup.py
```

## Usage

1. Start prosody server
```
sudo service start prosody
```

>Similarly, to stop prosody server -
``` 
sudo service stop prosody 
```
>Server logs can be monitored with - 
```
sudo tail /var/log/prosody/prosody.log
```

2. Run simulation of 5 UAVs.


```bash
cd path/to/px4/firmware

export PX4_HOME_LAT=2.4713686
export PX4_HOME_LON=-76.5975746

Tools/gazebo_sitl_multiple_run.sh -n 5
```

> If using `virtual env`, do not forget to `source` before execution of the following steps.

3. On a new terminal, execute agent `Master` with JID = `test`.

```bash
cd path/to/SPADE_BDI_UAV
python3 src/MAV_model.py
```

4. On a new terminal, execute agent `Coordinator 1` with JID = `test2`.

```bash
cd path/to/SPADE_BDI_UAV
python3 src/MAV_model.py --name test2 --uav_add udp://:14541 --uav_port 50041 --mc_port 5556
```

5. On a new terminal, execute agent `Coordinator 2` with JID = `test3`.

```bash
cd path/to/SPADE_BDI_UAV
python3 src/MAV_model.py --name test3 --uav_add udp://:14542 --uav_port 50042 --mc_port 5557
```

8. On a new terminal, execute agent `Coordinator 3` with JID = `test4`.

```bash
cd path/to/SPADE_BDI_UAV
python3 src/MAV_model.py --name test4 --uav_add udp://:14543 --uav_port 50043 --mc_port 5558
```

7. On a new terminal, execute agent `Coordinator 4` with JID = `test5`.

```bash
cd path/to/SPADE_BDI_UAV
python3 src/MAV_model.py --name test5 --uav_add udp://:14544 --uav_port 50044 --mc_port 5559
```

1. On a new terminal, run `GCS`

```bash
cd path/to/SPADE_BDI_UAV
python3 src/GCS.py
```

6. The execution of GCS.py, take ID and Command as input. 
   * ID can be `test`,`test2`,etc to refer to UAV1,UAV2,etc respectively.
   * Command can be `mission`, `rtl` or `get_info`.


## Roadmap

- [ ] Sprint 1 - Simulation Environment
  - [ ] BDI Controller
  - [ ] State, Neighbour, waypoint register
  - [ ] Inter-MAV communication
  - [ ] Defined Hetrogenity
  - [ ] Basic function - RTL, Mission, Takeoff.
  - [ ] SITL PX$
- [ ] Sprint 2 - Multi-Agent Architecture
  - [ ] FIPA protocol
  - [ ] Role in society
  - [ ] Communication restriction
  - [ ] Record labels and warning
  - [ ] Registering transactions



