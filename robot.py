import argparse
import json

from swarm.drone import Drone

def main():
    # Parse Command Line Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-host", type = str, help = "MQTT Host IP")
    parser.add_argument("-port", type = int, help = "MQTT Port")
    parser.add_argument("config", type = str, help = "Config file")
    parser.add_argument("-verbose", action="store_true")

    args = parser.parse_args()

    # Ensure that Node Descriptor File can be Opened
    config = None
    try:
        f = open(args.config, 'r')
        config = json.load(f)
        f.close()
    except Exception as e:
        print(repr(e))
        print("Couldn't open config file " + args.config)
        return -1

    connection_string = "/dev/serial/by-id/" + config["device_id"]

    bot = Drone(connection_string, args.host, args.port, config["node"], verbose = args.verbose)
    bot.addEventListener("message", execute)
    bot.start()

def execute(bot: Drone, message: str):
    """
    Execute MQTT message
    """
    command = message[1:-1].split(',')
    pitch = int(command[0])
    roll = int(command[1])
    yaw = int(command[2])
    speed = float(command[3])
    bot.commandMavLink((pitch, roll, yaw), speed)

if (__name__ == "__main__"):
    main()