## About the project 
Desktop application designed to test distributed communication protocols with heterogeneous SITL-MAVs.

### Built with

* [MAVSDK]()
* [SPADE]()
* [SPADE_BDI]()
* [SPAD_PubSub]()
* [Prosody XMPP server]()
* [AgentSpeak(L)]()
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

3. modify the empty admins JSON by adding test@localhost ,test2@localhost and gcs@localhost

```lua
admins = {"test@localhost","gcs@localhost","test2@localhost" }
```

4. save and exit using `ctrl + x`,then press `y` to save  change. 

5. Execute the following commands to register agents in the prosody server
```
prosodyctl register test localhost password
prosodyctl register test2 localhost password
prosodyctl register gcs localhost password
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

2. Run simulation of 2 UAVs.


```bash
cd path/to/px4/firmware
Tools/gazebo_sitl_multiple_run.sh -n 2
```

3. On a new terminal, run agent 1.

```bash
cd path/to/SPADE_BDI_UAV
python3 src/MAV_model.py
```

4. On a new terminal, run agent 2.

```bash
cd path/to/SPADE_BDI_UAV
python3 src/MAV_model2.py
```
> If using `virtual env`, do not forget to `source` before execution of the following steps.


> **Note** : Incase of samestanza error, comment line 75 on MAV_model.py and MAV_model2.py 

5. On a new terminal, run GCS

```bash
cd path/to/SPADE_BDI_UAV
python3 src/GCS.py
```

6. The execution of GCS.py, take ID and Command as input. 
   * ID can be `test` or `test2` to refer to UAV1 or UAV2 respectively.
   * Command can be `mission`, `rtl` or `get_info`.


## Roadmap

- [ ] Sprint 1
  - [ ] Feature 1
  - [ ] Feature 2



