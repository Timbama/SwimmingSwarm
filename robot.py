import json
from argparse import ArgumentParser

from swarm.drone import Drone


class ManualDrone(Drone):
    def handle_message(self, link: str, msg: str):
        """
        Execute MQTT message
        """
        state = json.loads(msg)
        if state["alive"]:
            command = state["command"]
            pitch = int(command[0])
            roll = int(command[1])
            yaw = int(command[2])
            speed = int(command[3])
            self.channel_command(pitch, roll, yaw, throttle=speed)
        else:
            self.stop()


def main():
    # Parse Command Line Arguments
    parser = ArgumentParser()
    parser.add_argument(
        "config", type=str, help="Config file", nargs="?", default="./robot_config.json"
    )
    args = parser.parse_args()

    bot = ManualDrone.from_config(args.config)
    bot.start()


if __name__ == "__main__":
    main()
