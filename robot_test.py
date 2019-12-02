import math
import json
from argparse import ArgumentParser

import router_coord
from swarm.drone import Drone

def main():
    # Parse Command Line Arguments
    parser = ArgumentParser()

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
    bot = Drone(connection_string, "", 0, None, vehicle_mode=config["vehicle_mode"], local = True, verbose = True)
    bot.set_vehicle_mode(config["vehicle_mode"])
    bot.arm_vehicle()
    test()
    print("Test passed")
    bot.disarm_vehicle()

def test(bot: Drone, message: str == ""):
    #example movement
    test_list = ["C1", "C2", "C3"]
    move(bot, test_list)

def move(bot: Drone, sequence: list):
    speed = 5
    for i in range(len(sequence)):
        m = router_coord.mapping[sequence[i]]
        newyaw = int(math.degrees(math.atan2(m[1], m[0])))
        newyaw2 = int(((newyaw / 360.0)*(1832-1148)) + 1148)
        bot.channel_command(0, 0, newyaw2, 1832)
        #bot.vehicle.airspeed = speed
        while True:
            curr_grid = router_coord.getCoor()
            if curr_grid == sequence[i]:
                bot.channel_command(0, 0, newyaw2, 1490)
                break
