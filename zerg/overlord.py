import subprocess
import time
import socket
import paramiko
import queue
import json
from hashlib import md5
from collections import namedtuple
from vizier import node

def update(bot, bot_ssh: paramiko.SSHClient):
    def always(bot, bot_ssh: paramiko.SSHClient):
        files_to_update = []
        if not md5sum_equal(bot.config["source"], bot.config["dest"], bot_ssh):
            files_to_update.append((bot.config["source"], bot.config["dest"]))
        if not md5sum_equal(bot.script["source"], bot.script["dest"], bot_ssh):
            files_to_update.append((bot.script["source"], bot.script["dest"]))
        uploadFiles(bot_ssh, files_to_update)
    
    def never(bot, bot_ssh):
        pass

    execute_update = {"always": always, "never": never}
    return execute_update[bot.update_mode](bot, bot_ssh)

def md5sum_equal(source, dest, bot_ssh):
    std_in, stdout, stderr = bot_ssh.exec_command("md5sum " + dest + "; echo $?")
    md5out = stdout.readlines()
    md5out_code = stdout.readline()
    if md5out_code == 0:
        md5out = md5out.split()[0]
        with open(source, "r") as file:
            h = md5(file)
            return h.hexdigest() == md5out
    else:
        return False

def connectBySSH(ip: str, uname: str, passw: str):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(ip, username = uname, password = passw)
    return ssh_client

def uploadFiles(ssh_client: paramiko.SSHClient, paths: list):
    ftp_client=ssh_client.open_sftp()
    for source, dest in paths:
        ftp_client.put(source, dest)
    ftp_client.close()

def runScript(ssh_client, script_location: str, host: str, port: int, script_config_location: str):
    command = "python3 " + script_location + " -h " + host + " -p " + str(port) + " " + script_config_location
    ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(command)
    return (ssh_stdout, ssh_stderr)

class Overlord:
    def __init__(self, config: object):
        self.host = namedtuple("Host", config["host"].keys())(*config["host"].values())
        self.bots = []
        for bot in config["bots"]:
            self.bots.append(namedtuple("Bot", bot.keys())(*bot.values()))
        self.host_ip = self._getHostIP()
        self.host_node = node.Node(self.host_ip, self.host.port, self.host.node)
        self.started = False
        self._event = {"start": [], "stop":[], "communicate": []}
        self._bot_ip = None
    
    def start(self):
        try:
            self._startMosquitto()
            self.host_node.start()
            ssh_stdout = None
            bot_ssh_list = []
            for bot in self.bots:
                bot_ssh = connectBySSH(self._getBotIP(bot.mac), bot.username, bot.password)
                update(bot, bot_ssh)
                command = "python3 " + bot.script["dest"] + " -host " + self.host_ip + " -port " + str(self.host.port) + " -v " + bot.config["dest"]
                ssh_stdin, ssh_stdout, ssh_stderr = bot_ssh.exec_command(command)
                bot_ssh_list.append(bot_ssh)

            # Get the links for Publishing/Subscribing
            publishable_link = list(self.host_node.publishable_links)[0]
            subscribable_link = list(self.host_node.subscribable_links)[0]

            self.started = True
            self._fire_event("start")
            while self.started:
                try:
                    msg_queue = self.host_node.subscribe(subscribable_link)
                    message = msg_queue.get(timeout=0.1).decode(encoding = 'UTF-8')
                    host_node.publish(publishable_link, self._fire_event("communicate")(message))
                except queue.Empty:
                    pass
                except KeyboardInterrupt:
                    self._fire_event("stop")
                    self.stop()
                except Exception as e:
                    self._fire_event("stop")
                    self.stop()

        finally:
            print(ssh_stdout.read())
            for bot_ssh in bot_ssh_list:
                bot_ssh.close()
            self.host_node.stop()
            self._stopMosquitto()
        
    def stop(self):
        self.started = False
    
    def addEventListener(self, event_name: str, listener: callable):
        # All events are expected to expect one return argument:
        # the Drone object itself
        self._event[event_name].append(listener)
    
    def removeEventListeners(self, event_name: str):
        self._event[event_name] = []
    
    def _fire_event(self, event_name: str, *args):
        for listener in self._event[event_name]:
            listener(*args)
    
    def _startMosquitto(self):
        command = ["mosquitto", "-p", str(self.host.port)]
        self.mosquitto = subprocess.Popen(command)
        time.sleep(1)
    
    def _stopMosquitto(self):
        self.mosquitto.terminate()
        time.sleep(1)

    def _getHostIP(self):
        return socket.gethostbyname(socket.gethostname())

    def _getBotIP(self, mac: str):
        if (self._bot_ip == None):
            self._bot_ip = {}
            macs = []
            for bot in self.bots:
                macs.append(bot.mac)
            command = ["sudo", "arp-scan", "--localnet"]
            process = subprocess.Popen(command, stdout = subprocess.PIPE)
            while True:
                line = process.stdout.readline()
                if not line or len(macs) == 0:
                    break
                for bot_mac in macs:
                    if bot_mac in line.decode():
                        self._bot_ip[bot_mac] = line.decode().rstrip().split()[0]
                        macs.remove(bot_mac)
        return self._bot_ip[mac]
