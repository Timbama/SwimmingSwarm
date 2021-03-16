import logging
import json
from argparse import ArgumentParser

from swarm.overlord import Overlord
from pixyController import pixyController
from gpsCalculator import new_coordinate_relative_origin
import pyGui

# This is the temporary way of choosing where the guided bot goes
TEST_GUIDED_COMMAND = {
    "lat": -1,
    "lon": -1, 
}
logging.basicConfig(level=logging.INFO)


def main():
    # Parse Command Line Arguments
    parser = ArgumentParser()
    parser.add_argument("configuration", type=str, help=".json configuration file")
    parser.add_argument(
        "-mode",
        choices=["auto", "keyboard", "joystick"],
        help="control mode: auto, keyboard or joystick",
    )
    args = parser.parse_args()

    if args.mode == "joystick" or args.mode == "keyboard":

        # Initializer GUI
        gui = pyGui.Gui(list(range(3)), hasJoystick=args.mode == "joystick")
        overlord = ManualOverlord.from_config(args.configuration, args.mode, gui)
        gui.render()
        overlord.start()
        gui.stop()

    elif args.mode == "auto":
        overlord = AutoOverlord.from_config(args.configuration)
        overlord.start()
    
    elif args.mode == "guided":

        # This should be the coordinates of the pixyCam grids top left corner
        coords = {
            "lat": -1,
            "lon": -1,
        } 

        # Without GUI for now just for testing, will implement later
        overlord = GuidedOverlord.from_config(args.configuration, coords)



class ManualOverlord(Overlord):
    def __init__(
        self,
    ):
        super().__init__()
        self.mode = None
        self.gui = None
        self.sub_to_pub = {}

    @classmethod
    def from_config(cls, path: str, mode: str, gui: pyGui.Gui):
        # pylint: disable=arguments-differ
        overlord = super().from_config(path)
        overlord.mode = mode
        overlord.gui = gui
        with open(path, "r") as file:
            configuration = json.load(file)
            for bot in configuration["bots"]:
                # pylint: disable=no-member
                overlord.sub_to_pub[bot["sub_link"]] = bot["pub_link"]
        return overlord

    def handle_message(self, link: str, msg: str):
        if msg == "":
            return

        logging.info("Received %s message from: %s", msg, link)

        state = json.loads(msg.decode())
        if not state["alive"]:
            self.stop()
            return

        if self.gui.has_quit():
            state["alive"] = False
            self.stop()
        else:
            command = None
            if self.mode == "joystick":
                command = self.gui.get_joystick_axis()
            elif self.mode == "keyboard":
                command = self.gui.get_keyboard_command()
            command = (
                pwm(-command[0]),
                pwm(-command[1]),
                pwm(-command[2]),
                pwm(-command[3]),
            )
            state["command"] = command

        pub_link = self.sub_to_pub[link]
        self.publish(pub_link, json.dumps(state, separators=(",", ":")))
        logging.info("Published to %s message: %s", link, state)

    def handle_round(self):
        self.gui.render()


class AutoOverlord(Overlord):
    def __init__(
        self,
    ):
        super().__init__()
        self.mode = None
        self.gui = None
        self.sub_to_pub = {}

    @classmethod
    def from_config(cls, path: str):
        # pylint: disable=arguments-differ
        overlord = super().from_config(path)
        with open(path, "r") as file:
            configuration = json.load(file)
            for bot in configuration["bots"]:
                # pylint: disable=no-member
                overlord.sub_to_pub[bot["sub_link"]] = bot["pub_link"]
        return overlord

    def handle_message(self, link: str, msg: str):
        state = json.loads(msg.decode(encoding="UTF-8"))
        if not state["alive"]:
            self.stop()
            return
        command = {"lat": 1, "lon": 1, "alt": 1}
        state["command"] = command
        self.publish(link, json.dumps(state, separators=(",", ":")))



class GuidedOverlord(Overlord):
    def __init__(
        self,
    ):
        super().__init__()
        self.mode = None
        self.gui = None
        self.sub_to_pub = {}

    @classmethod
    def from_config(cls, path: str, coords):
        # pylint: disable=arguments-differ
        overlord = super().from_config(path)
        overlord.mode = "guided"
        overlord.gui = None
        overlord.pixyController = pixyController()
        with open(path, "r") as file:
            configuration = json.load(file)
            for bot in configuration["bots"]:
                # pylint: disable=no-member
                overlord.sub_to_pub[bot["sub_link"]] = bot["pub_link"]
        return overlord

    def handle_message(self, link: str, msg: str):
        logging.info("Received %s message from: %s", msg, link)

        state = json.loads(msg.decode())
        if not state["alive"]:
            self.stop()
            return

        else:
            command = {}
            bots, count = self.pixyController.get_all_bot_positions()
            for i in range(count):
                bot_id = self.pixyController.identify_bot(bots[i].m_signature)
                if (str(bot_id) in link): #bot_id will be the index of the bot in the COLOR_CODES dict in pixyController
                    # This is telling the bot where to go
                    command["goto"] = TEST_GUIDED_COMMAND

                    # Compute bot's lat on lon based on position in pixyCam
                    bot = self.pixyController.get_bot_position(bots[i].m_signature)
                    dist_x, dist_y = self.pixyController.get_bot_position_units(bot)
                    lat, lon = new_coordinate_relative_origin(self.coords["lat"], self.coords["lon"], dist_x, dist_y)
                    command["coords"] = {
                        "lat": lat, 
                        "lon": lon
                    }
                    command["camera"] = {
                        "lat": self.coords["lat"],
                        "lon": self.coords["lon"]
                    }
                    command["dist"] = {
                        "x": dist_x,
                        "y": dist_y
                    }
                    
            state["command"] = command

        pub_link = self.sub_to_pub[link]
        self.publish(pub_link, json.dumps(state, separators=(",", ":")))
        logging.info("Published to %s message: %s", link, state)


def pwm(value):
    max_pwm = 1590  # 1832
    min_pwm = 1390  # 1148
    center = (max_pwm + min_pwm) / 2
    diff = (max_pwm - min_pwm) / 2
    return int(center + (diff * value))


if __name__ == "__main__":
    main()