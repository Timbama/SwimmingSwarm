from argparse import ArgumentParser
import json
import pyGui
import socket
import subprocess
import time
from vizier.node import Node

class Controller:
    def __init__(self, started_node):
        self.node = started_node

        # Get the links for Publishing/Subscribing
        self.publishable_link = list(started_node.publishable_links)[0]
        self.subscribable_link = list(started_node.subscribable_links)[0]
        self.msg_queue = self.node.subscribe(self.subscribable_link)
    
    def send(self, message: str):
        self.node.publish(self.publishable_link, message)
    
    def receive(self, block=True, timeout=None):
        return self.msg_queue.get(block=block, timeout=timeout).decode(encoding = 'UTF-8')

# Start the Message Broker
def start_mosquitto(port: int):
    command = ["mosquitto", "-p", str(port)]
    mosquitto = subprocess.Popen(command)
    time.sleep(0.5)
    return mosquitto

# Stop the Message Broker
def stop_mosquitto(process: subprocess.Popen):
    process.terminate()
    time.sleep(0.5)


def get_host_IP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #the IP address doesn't have to be reachable
    s.connect(("10.255.255.255", 1)) 
    ip = s.getsockname()[0]
    s.close()
    return ip

# Pulse Width Modulation - allows motors to run at values between fully on or fully off
def pwm(value):
    max_pwm = 1590 #1832
    min_pwm = 1390 #1148
    center = (max_pwm + min_pwm)/2
    diff = (max_pwm - min_pwm)/2
    return int(center + (diff * value))

def main(port: int, desc_filename: str, mode: str):
    print(mode)
    node_desc = None
    with open(desc_filename, 'r') as desc_file:
        node_desc = json.load(desc_file)

    #Sets up the host node and the controller
    mosquitto = start_mosquitto(HOST_PORT) #? from where does HOST_PORT originate?
    host_node = Node(get_host_IP(), HOST_PORT, node_desc) #? what is a node in this context?
    host_node.start()
    controller = Controller(host_node)

    if MODE == "joystick" or MODE == "keyboard":
        gui = pyGui.Gui(hasJoystick = MODE == "joystick")

        state = {"alive": True}
        while state["alive"]:
            gui.render()
            try:
                # Receive bot's status. (Json parses message into a dictionary saved to state.)
                state = json.loads(controller.receive(timeout=0.1))
            except:
                continue
            if (MODE == "joystick"):
                command = gui.get_joystick_axis()
            elif (MODE == "keyboard"):
                command = gui.get_keyboard_command()
            # Inputs given commands from joystick/keyboard to the state
            state["command"] = (pwm(-command[0]), pwm(-command[1]), pwm(-command[2]), pwm(-command[3]))
            # (json.dumps converts state dictionary in python to json format)
            # Sends bot commands to perform
            controller.send(json.dumps(state, separators=(',',':')))

    # Auto mode is intended to operate such that you give the bot a lat & lon and it goes there
    elif MODE == "auto":
        state = {"alive": True}
        while state["alive"]:
            try:
                # Receive bot's status.
                state = json.loads(controller.receive(timeout=0.1))
            except:
                continue
            # Inputs command of lat/lon/alt
            state["command"] = {"lat":1,"lon":1,"alt":1} #NOTE: this is hardcoded
            # Sends bot commands to perform
            controller.send(json.dumps(state, separators=(',',':')))

    host_node.stop()
    stop_mosquitto()

if __name__ == "__main__":
    # Default values
    DESC_FILENAME = "./node_desc_controller.json"
    ALL_MODES = ["joystick", "keyboard", "auto"]

    # Parse Command Line Arguments
    parser = ArgumentParser()
    parser.add_argument("-port", type = int, help = "MQTT Port", default = 8080)
    parser.add_argument("-mode", choices=ALL_MODES, help = "Control Mode: auto, keyboard or joystick",
                        default = ALL_MODES[0])
    args = parser.parse_args()

    HOST_PORT = args.port
    MODE = args.mode

    main(HOST_PORT, DESC_FILENAME, MODE)
