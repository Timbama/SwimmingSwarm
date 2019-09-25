from argparse import ArgumentParser
import json
import subprocess
import time
import socket
import paramiko
import pyGui
import queue

from vizier import node

def main():
    # Parse Command Line Arguments
    parser = ArgumentParser()
    parser.add_argument("-configuration", help = ".json configuration file",
                        default = "controller_config.json")
    args = parser.parse_args()

    # Ensure that Configuration File can be Opened
    configuration = None
    try:
        f = open(args.configuration, 'r')
        configuration = json.load(f)
        f.close()
    except Exception as e:
        print(repr(e))
        print("Cannot open configuration file" + args.configuration)
        return -1
    
    try:
        controller_port = configuration["host"]["port"]
        controller_ip = getControllerIP()
        mosquitto = startMosquitto(controller_port)
        controller_node = node.Node(controller_ip, controller_port, configuration["host"]["node"])
        bot_macs = []
        for bot in configuration["bots"]:
            bot_macs.append(bot["mac"])
        ip_dict = getBotIP(bot_macs)
        for bot in configuration["bots"]:
            if bot["mac"] in ip_dict:
                bot_ssh = connectBySSH(ip_dict[bot["mac"]], bot["username"], bot["password"])
                command = "python3 " + bot["script"] + " -p " + str(controller_port) + " -c /dev/serial/by-id/" + bot["device"] + " " + controller_ip
                ssh_stdin, ssh_stdout, ssh_stderr = bot_ssh.exec_command(command)

        # Start the Node
        controller_node.start()

        # Get the links for Publishing/Subscribing
        publishable_link = list(controller_node.publishable_links)[0]
        subscribable_link = list(controller_node.subscribable_links)[0]
        msg_queue = controller_node.subscribe(subscribable_link)

        # Initializer GUI with keyboard
        gui = pyGui.Gui(False)
        done = False

        def communicate(callable):
            try:
                message = msg_queue.get(timeout=0.1).decode(encoding = 'UTF-8')
                state = int(message)
                if (state == 0):
                    callable()
                if not args.keyboard:
                    command =  gui.get_joystick_axis()
                else:
                    command = gui.get_keyboard_command()
                print('Control input =\t{0},\t{1},\t{2},\t{3}'.format(command[0],command[1],command[2],command[3]), end = '\r')
                controller_node.publish(publishable_link, str(command))
            except KeyboardInterrupt:
                callable()
            except queue.Empty:
                pass
            except Exception as e:
                print(e)
                callable()

        gui.start(communicate)
        controller_node.stop()
    finally:
        mosquitto.terminate()
        time.sleep(1)

def startMosquitto(port: int):
    command = ["mosquitto", "-p", str(port)]
    mosquitto = subprocess.Popen(command)
    time.sleep(1)
    return mosquitto

def getControllerIP():
    return socket.gethostbyname(socket.gethostname())

def connectBySSH(ip, uname, passw):
    ssh = paramiko.SSHClient()
    ssh.connect(ip, username = uname, password = passw)
    return ssh

def getBotIP(mac: list):
    ip_dict = {}
    command = ["sudo", "arp-scan", "--localnet"]
    process = subprocess.Popen(command, stdout = subprocess.PIPE)
    while True:
        line = process.stdout.readline()
        if not line or len(mac) == 0:
            break
        for bot_mac in mac:
            if bot_mac in line.decode():
                ip_dict[bot_mac] = line.decode().rstrip().split()[0]
                mac.remove(bot_mac)
    return ip_dict

if(__name__ == "__main__"):
    main()