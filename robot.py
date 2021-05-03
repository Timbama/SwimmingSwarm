import time
import logging
import json
from argparse import ArgumentParser

from swarm.drone.ardusub import DronekitDrone

logging.basicConfig(level=logging.INFO)


class ManualDrone(DronekitDrone):
    def handle_message(self, link: str, msg: str):
        """
        Execute MQTT message
        """
        if msg == "":
            time.sleep(0.1)
            return

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
            logging.info("Stopping drone")
            self.stop()
        state = {"alive": True}
        self.publish_all(json.dumps(state, separators=(",", ":")))
        logging.info("Published to %s message: %s", link, state)


def main():
    # Parse Command Line Arguments
    parser = ArgumentParser()
    parser.add_argument("config", type=str, help="Config file")
    parser.add_argument("-sitl", action="store_true")
    parser.add_argument("-sitl-path", default="firmware/sitl/ardusub")
    args = parser.parse_args()

    bot = None
    if not args.sitl:
        bot = ManualDrone.from_config(args.config)
    else:
        from swarm.drone.ardusub.sitl import DronekitSitlDrone

        class ManualSitlDrone(DronekitSitlDrone):
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
                state = {"alive": True}
                self.publish_all(json.dumps(state, separators=(",", ":")))
                logging.info("Published to %s message: %s", link, state)
                
        bot = ManualSitlDrone.from_config(args.config, args.sitl_path)

    # Wait for vehicle armable

    # bot.wait_vehicle_armable() #Maybe not. It always stops here
    # Arm verhicle
    bot.arm_vehicle()
    state = {"alive": True}
    # Send the initial condition
    bot.publish_all(json.dumps(state, separators=(",", ":")))
    bot.start()
    while bot.active:
        bot.step()
    bot.vehicle.close()


if __name__ == "__main__":
    main()
