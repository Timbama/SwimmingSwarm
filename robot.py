import time
import logging
import json
from argparse import ArgumentParser

from swarm.drone.dronekit import DronekitDrone, DronekitSitlDrone

logging.basicConfig(level=logging.INFO)


class ManualDrone(DronekitDrone):
    def handle_message(self, link: str, msg: str):
        """
        Execute MQTT message
        """
        if msg == "":
            time.sleep(0.1)
            return

        logging.info("Received %s message from: %s", msg, link)
        state = json.loads(msg.decode())
        if state["alive"]:
            command = state["command"]
            logging.info("New command %s", command)
            pitch = int(command[0])
            roll = int(command[1])
            yaw = int(command[2])
            speed = int(command[3])
            self.channel_command(pitch, roll, yaw, throttle=speed)
        else:
            logging.info("Stopping drone")
            self.stop()
        self.publish_all(json.dumps(state, separators=(",", ":")))
        logging.info("Published to %s message: %s", link, state)


class ManualSitlDrone(DronekitSitlDrone):
    def handle_message(self, link: str, msg: str):
        """
        Execute MQTT message
        """
        logging.info("Received %s message from: %s", msg, link)
        state = json.loads(msg.decode())
        if state["alive"]:
            command = state["command"]
            logging.info("New command %s", command)
            pitch = int(command[0])
            roll = int(command[1])
            yaw = int(command[2])
            speed = int(command[3])
            self.channel_command(pitch, roll, yaw, throttle=speed)
        else:
            logging.info("Stopping...")
            self.stop()
        self.publish_all(json.dumps(state, separators=(",", ":")))
        logging.info("Published to %s message: %s", link, state)

class GuidedDrone(DronekitDrone):
    def handle_start(self):
        testLocation = {
            "lat": 80,
            "lon": 80
        }
            #droneLocation = self.vechile.get_location_metres(cameraLocation, -command["dist"]["y"], command["dist"]["x"]) # PixyCam up must be north
        droneLocation = self.vechile.get_location_metres(testLocation, -3, 2)
        self.send_GPS(droneLocation.lat, droneLocation.lon)
        print(self.location())
        pass

    def handle_stop(self):
        pass

    def handle_message(self, link: str, msg: str):
        """
        Execute MQTT message
        """
        logging.info("Received %s message from: %s", msg, link)
        if (not msg):
            state = {
                "alive": True,
                "command": "hi"
            }
        else:
            state = json.loads(msg.decode())
            
        if state["alive"]:
            command = state["command"]
            logging.info("New command %s", command)
            
            # This is telling the drone where it is based on the pixyCam info
            # self.send_GPS(command["coords"]["lat"], command["coords"]["lon"], 0)
            #cameraLocation = LocationGlobal(float(command["camera"]["lat"]), float(command["camera"]["lon"]))
            testLocation = {
                "lat": 80,
                "lon": 80
            }
            #droneLocation = self.vechile.get_location_metres(cameraLocation, -command["dist"]["y"], command["dist"]["x"]) # PixyCam up must be north
            droneLocation = self.vehicle.get_location_metres(testLocation, -3, 2) # PixyCam up must be north
            self.send_GPS(droneLocation.lat, droneLocation.lon)
            print('here')
            print(self.location())
            

            # Guided mode commands
            # this should ideally only execute once, should change that
            goto = LocationGlobal(float(command["goto"]["lat"]), float(command["goto"]["lon"]))

        else:
            logging.info("Stopping...")
            self.stop()
        self.publish_all(json.dumps(state, separators=(",", ":")))
        logging.info("Published to %s message: %s", link, state)

    
    def send_GPS(self, lat: float, lon: float, alt: float, satellites_visible = 3):
        gps_fix_type = {
            "no_fix": 0, "2d_fix": 2,
            "3d_fix": 3, "dgps": 4, "rtk_float": 5
        }
        ignore = {
            "alt": 1, "hdop": 2, "vdop": 4, "vel_horiz": 8, "vel_vert": 16,
            "speed_accuracy": 32, "horizontal_accuracy": 64, "vertical_accuracy": 128
        }
        ignore_flags = ignore["vel_horiz"] | ignore["vel_vert"]
        ignore_flags = ignore_flags | ignore["speed_accuracy"] | ignore["horizontal_accuracy"]
        msg = self.vehicle.channels(
            int(time.time()*10000), #Timestamp (micros since boot or Unix epoch)
            0,                      #ID of the GPS for multiple GPS inputs
            ignore,                 #Flags indicating which fields to ignore (see GPS_INPUT_IGNORE_FLAGS enum). All other fields must be provided.
            0,                      #GPS time (milliseconds from start of GPS week)
            0,                      #GPS week number
            gps_fix_type["3d_fix"], #0-1: no fix, 2: 2D fix, 3: 3D fix. 4: 3D with DGPS. 5: 3D with RTK
            int(lat * (10**7)),     #Latitude (WGS84), in degrees * 1E7
            int(lon * (10**7)),     #Longitude (WGS84), in degrees * 1E7
            alt,                    #Altitude (AMSL, not WGS84), in m (positive for up)
            0,                      #GPS HDOP horizontal dilution of position in m
            0,                      #GPS VDOP vertical dilution of position in m
            0,                      #GPS velocity in m/s in NORTH direction in earth-fixed NED frame
            0,                      #GPS velocity in m/s in EAST direction in earth-fixed NED frame
            0,                      #GPS velocity in m/s in DOWN direction in earth-fixed NED frame
            0,                      #GPS speed accuracy in m/s
            0,                      #GPS horizontal accuracy in m
            0,                      #GPS vertical accuracy in m
            satellites_visible      #Number of satellites visible.
        )
        self.vehicle.send_mavlink(msg)


def main():
    # Parse Command Line Arguments
    parser = ArgumentParser()
    parser.add_argument("config", type=str, help="Config file")
    parser.add_argument("-sitl", action="store_true")
    parser.add_argument("-sitl-path", default="firmware/sitl/ardusub")
    args = parser.parse_args()

    if args.sitl:
        bot = ManualSitlDrone.from_config(args.config, args.sitl_path)
    else:
        bot = GuidedDrone.from_config(args.config)

    # Wait for vehicle armable
    bot.wait_vehicle_armable()
    # Arm verhicle
    bot.arm_vehicle()
    state = {"alive": True}
    # Send the initial condition
    bot.publish_all(json.dumps(state, separators=(",", ":")))
    bot.start()
    while bot.active:
        bot.step()
    bot.vehicle.close()


if __name__ == "__main__":
    main()
