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
        ip_dict = botIPDict(bot_macs)
        for bot in configuration["bots"]:
            if bot["mac"] in ip_dict:
                bot_ssh = connectBySSH(ip_dict[bot["mac"]], bot["username"], bot["password"])
                file_and_path = []
                for key in bot["file"].keys():
                    file_and_path.append((open(bot["file"][key], "r"), bot["file"][key]))
                uploadFiles(bot_ssh, file_and_path)
                runScript(bot_ssh, bot["file"]["script"], controller_ip, controller_port, bot["file"]["config"])

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
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(ip, username = uname, password = passw)
    return ssh_client

def uploadFiles(ssh_client, file_and_paths: list):
    ftp_client=ssh_client.open_sftp()
    for file, path in file_and_paths:
        ftp_client.putfo(file, path)
    ftp_client.close()

def runScript(ssh_client, script_location: str, host: str, port: int, script_config_location: str):
    command = "python3 " + script_location + " -h " + host + " -p " + str(port) + " " + script_config_location
    ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(command)
    return (ssh_stdout, ssh_stderr)

def botIPDict(macs: list):
    ip_dict = {}
    command = ["sudo", "arp-scan", "--localnet"]
    process = subprocess.Popen(command, stdout = subprocess.PIPE)
    while True:
        line = process.stdout.readline()
        if not line or len(macs) == 0:
            break
        for bot_mac in macs:
            if bot_mac in line.decode():
                ip_dict[bot_mac] = line.decode().rstrip().split()[0]
                macs.remove(bot_mac)
    return ip_dict

def update(mode: str):
    update_mode = {"always": always, "on_upgrade": "", "never": ""}
    return update_mode[mode]

    def always(source_version, ssh_client, config_path):
        return uploadFiles(ssh_client, config_path)
    
    def onUpgrade(source_version, ssh_client, config_path):
        dest_config = json.load(open(config_path, "r"))

if(__name__ == "__main__"):
    main()