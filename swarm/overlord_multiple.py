import subprocess
import time
import socket
import paramiko
import queue
import json
import threading
import hashlib
from collections import namedtuple
from vizier import node

def update(bot, bot_ssh: paramiko.SSHClient):
    def always(bot, bot_ssh: paramiko.SSHClient):
        files_to_update = []
        if not md5sum_equal(bot.config["source"], bot.config["dest"], bot_ssh):
            files_to_update.append((bot.config["source"], bot.config["dest"]))
        if not md5sum_equal(bot.script["source"], bot.script["dest"], bot_ssh):
            files_to_update.append((bot.script["source"], bot.script["dest"]))
        upload_files(bot_ssh, files_to_update)
    
    def never(bot, bot_ssh):
        pass

    execute_update = {"always": always, "never": never}
    return execute_update[bot.update_mode](bot, bot_ssh)

def md5sum_equal(source, dest, bot_ssh):
    std_in, stdout, stderr = bot_ssh.exec_command("md5sum " + dest + "; echo $?")
    md5out = stdout.readline()
    md5out_code = int(stdout.readline().strip())
    if md5out_code == 0:
        md5out = md5out.split()[0]
        with open(source, "rb") as file:
            return hashlib.md5(file.read()).hexdigest() == md5out
    else:
        return False

def connect_by_SSH(ip: str, uname: str, passw: str):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(ip, username = uname, password = passw)
    return ssh_client

def upload_files(ssh_client: paramiko.SSHClient, paths: list):
    ftp_client=ssh_client.open_sftp()
    for source, dest in paths:
        ftp_client.put(source, dest)
    ftp_client.close()

def _read_ssh_ouput(stdout, stderr, output):
    if output.lower() == "stdout":
        return stdout.read()
    elif output.lower() == "stderr":
        return stderr.read()
    elif output.lower() == "both":
        return stdout, stdout
    else:
        return None

class Overlord:
    def __init__(self, config: object, verbose: bool = False):
        self.host = namedtuple("Host", config["host"].keys())(*config["host"].values())
        self.bots = []
        for bot in config["bots"]:
            self.bots.append(namedtuple("Bot", bot.keys())(*bot.values()))
        self.host_ip = self._get_host_IP()
        print("Host IP:", self.host_ip)
        self.host_node = node.Node(self.host_ip, self.host.port, self.host.node)
        self.started = False
        self._event = {"start": [], "loop": [], "stop":[]}
        self._bot_ip = None
        self._verbose = verbose
    
    def start(self):
        try:
            self._start_mosquitto()
            self.host_node.start()
            #bot_ssh = None
            #for bot in self.bots:
            #    bot_ssh = connect_by_SSH(self._get_bot_IP(bot.mac), bot.username, bot.password)
            #    update(bot, bot_ssh)

            # Get the links for Publishing/Subscribing
            #self.publishable_link = list(self.host_node.publishable_links)[0]
            #self.subscribable_link = list(self.host_node.subscribable_links)[0]

            self.publishable_links = list(self.host_node.publishable_links)       #now has list of publishable/subscribable links instead of just one; config was changed accordingly
            self.subscribable_links = list(self.host_node.subscribable_links)

            #self.msg_queue = self.host_node.subscribe(self.subscribable_link)
            self.msg_queues = []            #msg_queue changed to msg_queues which is a list of tuples containing (bot_number, msg_queue) where the msg_queue is the queue for each invididually subscribed link (each one in subscribable_links above)
            #for each bot
            for i in range(len(bots)):
                bot = bots[i]
                msg_queue_with_bot_identifier = (bot[0], self.host_node.subscribe(self.subscribable_links[i])) #bot[0] is the mac address, unique so a good identifier; second entry is the msg_queue for this subscribable link
                msg_queues.append(msg_queue_with_bot_identifier)
            


            self.started = True
            self._fire_event("start")
            if self._verbose: print("Starting loop")
            while self.started:
                try:
                    self._fire_event("loop")
                except KeyboardInterrupt:
                    self.stop()
                except queue.Empty:
                    if self._verbose: print("Empty queue")
                    pass
                except Exception as e:
                    print(e)
                    self.stop()

        finally:
            self.host_node.stop()
            self._stop_mosquitto()
        
    def stop(self):
        self._fire_event("stop")
        self.started = False
    
    def publish(self, message, publishable_link):   #you now have to specify the link you are publishing to
        self.host_node.publish(publishable_link, message)
    
    def get_message(self, block=True, timeout=None, bot_number):
        return self.msg_queues[bot_number][1].get(block=block, timeout=timeout).decode(encoding = 'UTF-8')

    def add_event_listener(self, event_name: str, listener: callable):
        # All events expects nothing and return nothing. Control the object through public methods.
        self._event[event_name].append(listener)
    
    def remove_event_listeners(self, event_name: str):
        self._event[event_name] = []
    
    def _fire_event(self, event_name: str, *args):
        data = []
        for listener in self._event[event_name]:
            data.append(listener(*args))
        if len(data) == 0:
            return None
        elif len(data) == 1:
            return data[0]
        else:
            return data
    
    def _start_mosquitto(self):
        command = ["mosquitto", "-p", str(self.host.port)]
        self.mosquitto = subprocess.Popen(command)
        time.sleep(1)
    
    def _stop_mosquitto(self):
        self.mosquitto.terminate()
        time.sleep(1)

    def _get_host_IP(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)) #Connecting to Google and then getting whatever ip address was used
        return s.getsockname()[0]

    def _get_bot_IP(self, mac: str):
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
        ip = ""
        try:
            ip = self._bot_ip[mac]
            print("Bot IP:", ip)
        except:
            raise Exception("Bot not found on local network")

        return ip
