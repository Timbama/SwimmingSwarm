import dronekit
import json
import socket
import time
from vizier.node import Node
import sys
import pixyController

GPS_FIX_TYPE = {
    "no_gps": 0,
    "no_fix": 1,
    "2d_fix": 2,
    "3d_fix": 3,
    "dgps": 4,
    "rtk_float": 5,
    "rtk_fixed": 6,
    "static": 7,
    "ppp": 8
}
GPS_INPUT_IGNORE_FLAGS = {
    "alt": 1,
    "hdop": 2,
    "vdop": 4,
    "vel_horiz": 8,
    "vel_vert": 16,
    "speed_accuracy": 32,
    "horizontal_accuracy": 64,
    "vertical_accuracy": 128
}

class Drone:
    def __init__(self, started_node: Node, connection_string: str, vehicle_mode: str):
        self.node = started_node

        # Get the links for Publishing/Subscribing
        self.publishable_link = list(started_node.publishable_links)[0]
        self.subscribable_link = list(started_node.subscribable_links)[0]
        self.msg_queue = self.node.subscribe(self.subscribable_link)
 
        print("Connecting via dronekit")
        connected = False
        while not connected:
            try:
                self.vehicle = dronekit.connect(connection_string, wait_ready=True)
                self.vehicle.wait_ready(True)
                connected = True
            except Exception as e:
                print("Error:", e, "retrying")
                time.sleep(1)
        print("Connected successfully")

        self.vehicle.mode = dronekit.VehicleMode(vehicle_mode)
        print("Setting mode:", vehicle_mode, end="")
        while self.vehicle.mode.name != vehicle_mode:
            self.vehicle.mode = dronekit.VehicleMode(vehicle_mode)
            print(".",end="")
            time.sleep(1)
        print("\nMode set:", self.vehicle.mode.name)   

    def send(self, message: str):
        self.node.publish(self.publishable_link, message)
    
    def receive(self, block=True, timeout=None):
        return self.msg_queue.get(block=block, timeout=timeout).decode(encoding = 'UTF-8')
    
    def arm_vehicle(self):
        self.vehicle.armed = True
        print("Arming", end="")
        while not self.vehicle.armed:
            self.vehicle.armed = True
            print(".",end="")
            time.sleep(1)
        print("\nArmed")
    
    def disarm_vehicle(self):
        self.vehicle.armed = False
        print("Disarming", end="")
        while self.vehicle.armed:
            self.vehicle.armed = False
            print(".",end="")
            time.sleep(1)
        print("\nDisarmed")
    
class GuidedDrone(Drone):
    def __init__(self, node, connection_string: str):
        super().__init__(node, connection_string, "GUIDED")
        guided_parameters = {
            "EK3_ENABLE": 1,
            "EK2_ENABLE": 0,
            "AHRS_EKF_TYPE": 3,
            "EK3_GPS_TYPE": 0,
            "EK3_MAG_CAL": 5,
            "EK3_ALT_SOURCE": 2,
            "GPS_TYPE": 14,
            "GPS_DELAY_MS": 50,
            "COMPASS_USE": 0,
            "COMPASS_USE2": 0,
            "COMPASS_USE3": 0
        }
        for key in guided_parameters:
            self.vehicle.parameters[key] = guided_parameters[key]

    def command(self, lat: float, lon: float, alt = 0):
        self.vehicle.simple_goto(dronekit.LocationGlobal(lat, lon, alt))

    def send_GPS(signature, pixy):
        bot = pixy.get_bot_position(signature)
        msg = self.vehicle.message_factory.gps_input_encode(bot) # i'm not sure if that's how message_factory works
        self.vehicle.send_mavlink(msg)

class ManualDrone(Drone):
    def __init__(self, node, connection_string: str):
        super().__init__(node, connection_string, "MANUAL")

    def command(self, pitch: int, roll: int, yaw: int, throttle: int):
        # Ch1 =Roll, Ch 2=Pitch, Ch 3=Horizontal throttle, Ch 4=Yaw, Ch 5=Forward throttle
        self.vehicle.channels.overrides['1'] = roll
        self.vehicle.channels.overrides['2'] = pitch
        self.vehicle.channels.overrides['5'] = throttle
        self.vehicle.channels.overrides['4'] = yaw

def host_ready(ip: str, port: int): 
    try:
        prober = socket.create_connection((ip, port))
        prober.close()
        return True
    except Exception as e:
        return False


def main(host_ip: str, port: int, desc_filename: str, connection_string: str, mode: str):
    node_desc = None
    with open(desc_filename, 'r') as desc_file:
        node_desc = json.load(desc_file)
    node = Node(host_ip, port, node_desc)

    while not host_ready(host_ip, port):
        print("Attempting to connect to " + host_ip + " on port" + port + "...")
        time.sleep(1)
        continue

    print("Connected")
    node.start()

    connection_string = "/dev/serial/by-id/" + connection_string

    drone = None
    if mode == "MANUAL":
        drone = ManualDrone(node, connection_string)
    elif mode == "GUIDED":
        drone = GuidedDrone(node, connection_string)
    else:
        drone = Drone(node, connection_string, mode)

    state = {"alive": True}
    while state["alive"]:
        # Send the initial condition to the PC
        drone.send(json.dumps(state, separators = (',', ':')))
        try:
            message = drone.receive(timeout=0.1).decode(encoding="UTF-8")
        except:
            continue
        state = json.loads(message)
        drone.command(*state)

if __name__ == "__main__":
    # Parse Command Line Arguments
    if len(sys.argv) != 2:
        print("Arguments invalid\nUsage: python3 robot_new.py [HOST_IP_HERE]")
        sys.exit(1)
    HOST_IP = sys.argv[1]           # enter host IP address on call
    PORT = 8080
    DESC_FILENAME = './node_desc_robot.json'
    DEVICE_ID = 'usb-ArduPilot_fmuv2_25003C000E51373339363131-if00'
    ALL_MODES = ['MANUAL', 'GUIDED']
    MODE = ALL_MODES[0]

    main(HOST_IP, PORT, DESC_FILENAME, DEVICE_ID, MODE)