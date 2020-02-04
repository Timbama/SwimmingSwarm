import json
import pyGui
import socket
import subprocess
import time
from vizier.node import Node

class Controller:
    def _init_(self, started_node):
        self.node = started_node

        # Get the links for Publishing/Subscribing
        self.publishable_link = list(started_node.publishable_links)[0]
        self.subscribable_link = list(started_node.subscribable_links)[0]
        self.msg_queue = self.node.subscribe(self.subscribable_link)
    
    def send(self, message: str):
        self.node.publish(self.publishable_link, message)
    
    def receive(self, block=True, timeout=None):
        return self.msg_queue.get(block=block, timeout=timeout).decode(encoding = 'UTF-8')
    
def start_mosquitto(port: int):
    command = ["mosquitto", "-p", str(port)]
    mosquitto = subprocess.Popen(command)
    time.sleep(0.5)
    return mosquitto

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

if __name__ == "__main__":
    # Default values
    HOST_PORT = 8080
    DESC_FILENAME = "./node_desc_controller.json"
    ALL_MODES = ["joystick", "keyboard", "auto"]
    MODE = ALL_MODES[0]

    main(HOST_PORT, DESC_FILENAME, MODE)

def main(port: int, desc_filename: str, mode: str):
    node_desc = None
    with open(desc_filename, 'r') as desc_file:
        node_desc = json.load(desc_file)
    
    mosquitto = start_mosquitto(HOST_PORT)
    host_node = Node(get_host_IP(), HOST_PORT, node_desc)
    host_node.start()
    controller = Controller(host_node)

    if MODE == "joystick" or MODE == "keyboard":
        gui = pyGui.Gui(hasJoystick = MODE == "joystick")

        state = {"alive": True}
        while state["alive"]:
            gui.render()
            try:
                state = json.loads(controller.receive(timeout=0.1))
            except:
                continue
            if (MODE == "joystick"):
                command = gui.get_joystick_axis()
            elif (MODE == "keyboard"):
                command = gui.get_keyboard_command()
            state["command"] = (pwm(-command[0]), pwm(-command[1]), pwm(-command[2]), pwm(-command[3]))
            controller.send(json.dumps(state, separators=(',',':')))

            def pwm(value):
                max_pwm = 1832
                min_pwm = 1148
                center = (max_pwm + min_pwm)/2
                diff = (max_pwm - min_pwm)/2
                return int(center + (diff * value))
    elif MODE == "auto":
        state = {"alive": True}
        while state["alive"]:
            try:
                state = json.loads(controller.receive(timeout=0.1))
            except:
                continue
            state["command"] = {"lat":1,"lon":1,"alt":1}
            controller.send(json.dumps(state, separators=(',',':')))

    host_node.stop()
    stop_mosquitto()
