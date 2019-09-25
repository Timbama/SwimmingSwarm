import argparse
import json

from swarm import SwarmBot

def main():
    # Parse Command Line Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-node_descriptor", help = ".json file node descriptor",
                        default = "node_desc_robot.json")
    parser.add_argument("-port", type = int, help = "MQTT Port", default = 8080)
    parser.add_argument("-connection_string", type = str, help="Pixhawk connection stirng",
                        default = "/dev/serial/by-id/usb-ArduPilot_Pixhawk1_25003C000E51373339363131-if00")
    parser.add_argument("host", type = str, help = "MQTT Host IP", default = "localhost")
    parser.add_argument("-verbose", action="store_true")

    args = parser.parse_args()

    # Ensure that Node Descriptor File can be Opened
    node_descriptor = None
    try:
        f = open(args.node_descriptor, 'r')
        node_descriptor = json.load(f)
        f.close()
    except Exception as e:
        print(repr(e))
        print("Couldn't open given node file " + args.node_descriptor)
        return -1

    bot = SwarmBot(args.connection_string, args.host, args.port, node_descriptor, verbose = args.verbose)
    bot.start()

if (__name__ == "__main__"):
    main()