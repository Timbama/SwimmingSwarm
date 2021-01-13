# Usage

A general guide to setting up necessary configuration files and running the Swarm.

## Prereqs

Prior to running this software, follow the [topside computer](Documentation/Software/TopsideComputer.md) and [raspberry pi](Documentation/Software/RaspberryPi.md) setup guides.

Also set up the configuration files as described later in this document.

## Running the software

This software is run in two parts.  First, the Controller is run on the topside computer, which allows incomming connections from vizier nodes, and then the Robot code is run on the bot, which connects the bot to the Controller and allows commands to be recieved.  In order to connect, both systems must share a network connection.

### Controller

Basic controller usage: `python ./controller.py -mode joystick`
    
- Available modes: `joystick`, `keyboard`, `auto`

### Robot

Basic robot usage: `python ./robot.py -host HOST_IP -port 8080`

- HOST_IP should be the IP of the topside computer


## Setting up the config files

There are 2 config files needed to run the multibot code: `controller_config.json` and `robot_config.json`

### `controller_config.json`

This config file is for the Controller. It has 2 main components

- host

    Needs to have 2 attributes - port, which is a number representing the port the controller is running on, and node, which is an object that describes this MQTT node. See the vizier docs for details about the node object.

    1. port
       - The port the controller will be running on
    2. node
       - The vizier (MQTT) descriptor for the topside computer node. This basically describes the routes the node will publish on/subscribe to.  The inner structure of `node` is described in the [Vizier Guide](Documentation/Software/Vizier.md#installation)
- bots
    A list of bot objects, one for each actual bot we have. Needs 2 attributes at the moment:
    1. color_codes
       - A list of at least 2 numeric values representing the color codes to idenfity this specific bot with. These numbers correspond to the chosen color code values in the pixyMon color code configuration process. (ie `[1, 2]`)
    2. bot_name
       - What to call this bot by when it is identified

### `robot_config.json`
This config file is for all the running bots. It is a list of objects, each with the following attributes:
1. host
   - The IP address of the controller computer that this bot should connect to (host parameter overrides)
2. port
   - The port on the controller computer this bot should connect to (default 8080)
3. device_id
   - This is the pixhawk's UID. it's needed by the robot script in order to connect to the pixhawk. The current pixhawk id's can be found in [Pixhawk.txt](util/Pixhawk.txt)
4. vehicle_mode
   - One of the drone-kit supported vehicle modes. See the [dronekit docs](https://dronekit-python.readthedocs.io/en/latest/automodule.html#dronekit.VehicleMode) for more details on the various vehicle modes. Use "STABILIZE" if unsure of what this value should be.
5. node
   - The vizier (MQTT) descriptor for the topside computer node. This basically describes the routes the node will publish on/subscribe to. The inner structure of `node` is described in the [Vizier Guide](Documentation/Software/Vizier.md#installation)
