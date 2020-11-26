# Setting up the config files
There are 2 config files needed to run the multibot code - controller_config.json and robot_config.json
## controller_config.json
This config file is for the Topside controller. It has 2 main components
1. host

    Needs to have 2 attributes - port, which is a number representing the port the controller is running on, and node, which is an object that describes this MQTT node. See the vizier docs for details about the node object.
    1. port
       - the port the controller will be running on
    2. node
       - the vizier (MQTT) descriptor for the topside computer node. This basically describes the routes the node will publish on/subscribe to. General format is given below:
       ```
        "node": {
            "end_point" : "controller",
            "links" : {
                "/input0" :
                {
                    "links" : {},
                    "type" : "STREAM"
                },
                "/input1" :
                {
                    "links" : {},
                    "type" : "STREAM"
                },
                "/input2" :
                {
                    "links" : {},
                    "type" : "STREAM"
                }
            },
            "requests" : [{"link": "robot0/state", "type": "STREAM", "required": false}, {"link": "robot1/state", "type": "STREAM", "required": false}, {"link": "robot2/state", "type": "STREAM", "required": false}]
        }
       ```
          Links are what the controller will publish on, requests are what the controller will subscribe to. There will be corresponding (but opposite) links /requests in the robot config. For full documentation on how to format the node object, see the [Vizier Guide](https://github.com/nthieu173/SwimmingSwarm/blob/master/Documentation/Software/Vizier.md#installation)
2. bots
    A list of bot objects, one for each actual bot we have. Needs 2 attributes at the moment:
    1. color_codes
       - A list of at least 2 numeric values representing the color codes to idenfity this specific bot with. These numbers correspond to the chosen color code values in the pixyMon color code configuration process.
    2. bot_name
       - What to call this bot by when it is identified

## robot_config.json
This config file is for all the running bots. It is a list of objects, each with the following attributes:
1. host
   - the ip address of the controller computer that this bot should connect to
2. port
   - the port on the controller computer this bot should connect to
3. device_id
   - this is the pixhawk's id value. it's needed by the robot script in order to connect to the pixhawk. The current pixhawk id's can be found in [Pixhawk.txt](https://github.com/tom-hightower/SwimmingSwarm/blob/master/util/Pixhawk.txt)
4. vehicle_mode
   - one of the drone-kit supported vehicle modes. See the [dronekit docs](https://dronekit-python.readthedocs.io/en/latest/automodule.html#dronekit.VehicleMode) for more details on the various vehicle modes. Use "STABILIZE" if unsure of what this value should be.
5. node
   - the vizier (MQTT) descriptor for the topside computer node. This basically describes the routes the node will publish on/subscribe to. General format is given below:
       ```
        "node": {
            "end_point" : "controller",
            "links" : {
                "/input0" :
                {
                    "links" : {},
                    "type" : "STREAM"
                },
                "/input1" :
                {
                    "links" : {},
                    "type" : "STREAM"
                },
                "/input2" :
                {
                    "links" : {},
                    "type" : "STREAM"
                }
            },
            "requests" : [{"link": "robot0/state", "type": "STREAM", "required": false}, {"link": "robot1/state", "type": "STREAM", "required": false}, {"link": "robot2/state", "type": "STREAM", "required": false}]
        }
       ```
       Links are what the controller will publish on, requests are what the controller will subscribe to. There will be corresponding (but opposite) links /requests in the controller config. For full documentation on how to format the node object, see the [Vizier Guide](https://github.com/nthieu173/SwimmingSwarm/blob/master/Documentation/Software/Vizier.md#installation)
