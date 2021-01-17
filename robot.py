import logging
import json
from argparse import ArgumentParser

from swarm.drone import Drone, DroneSitl


class ManualDrone(Drone):
    def handle_start(self):
        pass

    def handle_stop(self):
        pass

    def handle_message(self, link: str, msg: str):
        """
        Execute MQTT message
        """
        logging.info("Received %s message from: %s", msg, link)
        state = json.loads(msg.decode())
        if state["alive"]:
            command = state["command"]
            logging.info("New command %s", command)
            pitch = int(command[0])
            roll = int(command[1])
            yaw = int(command[2])
            speed = int(command[3])
            self.channel_command(pitch, roll, yaw, throttle=speed)
        else:
            logging.info("Stopping...")
            self.stop()
        self.publish_all(json.dumps(state, separators=(",", ":")))
        logging.info("Published to %s message: %s", link, state)


class ManualSitlDrone(DroneSitl):
    def handle_start(self):
        pass

    def handle_stop(self):
        pass

    def handle_message(self, link: str, msg: str):
        """
        Execute MQTT message
        """
        logging.info("Received %s message from: %s", msg, link)
        state = json.loads(msg.decode())
        if state["alive"]:
            command = state["command"]
            logging.info("New command %s", command)
            pitch = int(command[0])
            roll = int(command[1])
            yaw = int(command[2])
            speed = int(command[3])
            self.channel_command(pitch, roll, yaw, throttle=speed)
        else:
            logging.info("Stopping...")
            self.stop()
        self.publish_all(json.dumps(state, separators=(",", ":")))
        logging.info("Published to %s message: %s", link, state)


def main():
    # Parse Command Line Arguments
    parser = ArgumentParser()
    parser.add_argument("config", type=str, help="Config file")
    parser.add_argument("-sitl", action="store_true")
    parser.add_argument("-sitl-path", default="firmware/sitl/ardusub")
    args = parser.parse_args()

    if args.sitl:
        bot = ManualSitlDrone.from_config(args.config, args.sitl_path)
    else:
        bot = ManualDrone.from_config(args.config)
    bot.start()


if __name__ == "__main__":
    main()
