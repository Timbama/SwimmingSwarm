import logging
import json
from argparse import ArgumentParser
from typing import Dict

from swarm import VizierAgent

import pyGui

logging.basicConfig(level=logging.INFO)


def main():
    # Parse Command Line Arguments
    parser = ArgumentParser()
    parser.add_argument("configuration", type=str, help=".json configuration file")
    parser.add_argument(
        "-mode",
        choices=["keyboard", "joystick"],
        help="control mode: auto, keyboard or joystick",
    )
    args = parser.parse_args()

    if args.mode == "joystick" or args.mode == "keyboard":

        # Initializer GUI
        gui = pyGui.Gui(list(range(3)), hasJoystick=args.mode == "joystick")
        overlord = ManualOverlord.from_config(args.configuration, args.mode, gui)
        gui.render()
        overlord.start()
        while overlord.active:
            overlord.step()
            gui.render()
        gui.stop()


class ManualOverlord(VizierAgent):
    def __init__(
        self,
        broker_ip: str,
        broker_port: int,
        node_descriptor: Dict,
        input_mode: str,
        bots: Dict,
        gui: pyGui.Gui,
    ):
        super().__init__(broker_ip, broker_port, node_descriptor)
        self.input_mode = input_mode
        self.sub_to_pub = {}
        for bot in bots:
            # pylint: disable=no-member
            self.sub_to_pub[bot["sub_link"]] = bot["pub_link"]
        self.gui = gui

    @classmethod
    def from_config(cls, path: str, input_mode: str, gui: pyGui.Gui):
        # pylint: disable=arguments-differ
        with open(path, "r") as file:
            configuration = json.load(file)
            broker_ip = configuration["broker"]["ip"]
            broker_port = configuration["broker"]["port"]
            node_descriptor = configuration["node"]
            bots = configuration["bots"]
            overlord = cls(
                broker_ip, broker_port, node_descriptor, input_mode, bots, gui
            )
        return overlord

    def handle_message(self, link: str, msg: str):
        if msg == "":
            return

        logging.info("Received %s message from: %s", msg, link)

        state = json.loads(msg.decode())
        if not state["alive"]:
            self.stop()
            return

        state = {"alive": True}
        if self.gui.has_quit():
            state["alive"] = False
            self.stop()
        else:
            command = None
            if self.input_mode == "joystick":
                command = self.gui.get_joystick_axis()
            elif self.input_mode == "keyboard":
                command = self.gui.get_keyboard_command()
            else:
                raise RuntimeError("Unrecognized input mode")
            command = (
                pwm(-command[0]),
                pwm(-command[1]),
                pwm(-command[2]),
                pwm(-command[3]),
            )
            state["command"] = command

        pub_link = self.sub_to_pub[link]
        self.publish(pub_link, json.dumps(state, separators=(",", ":")))


def pwm(value):
    max_pwm = 1590  # 1832
    min_pwm = 1390  # 1148
    center = (max_pwm + min_pwm) / 2
    diff = (max_pwm - min_pwm) / 2
    return int(center + (diff * value))


if __name__ == "__main__":
    main()