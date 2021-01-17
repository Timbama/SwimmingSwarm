import logging
import json
from argparse import ArgumentParser

from swarm.overlord import Overlord

import pyGui


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
        logging.info("Received %s message from: %s", msg, link)

        state = json.loads(msg.decode())
        if not state["alive"]:
            self.stop()
            return

        if self.gui.has_quit():
            state["alive"] = False
            self.stop()
        else:
            self.gui.render()
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

        link = self.sub_to_pub[link]
        self.publish(link, json.dumps(state, separators=(",", ":")))
        logging.info("Published to %s message: %s", link, state)


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


def pwm(value):
    max_pwm = 1590  # 1832
    min_pwm = 1390  # 1148
    center = (max_pwm + min_pwm) / 2
    diff = (max_pwm - min_pwm) / 2
    return int(center + (diff * value))


if __name__ == "__main__":
    main()