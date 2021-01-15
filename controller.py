from argparse import ArgumentParser
import json
import pyGui
from swarm.overlord import Overlord


class ManualOverlord(Overlord):
    def __init__(
        self,
        mode: str,
        gui: pyGui.Gui,
    ):
        super().__init__()
        self.mode = mode
        self.gui = gui

    @classmethod
    # pylint: disable=arguments-differ
    def from_config(cls, path: str, mode: str, gui: pyGui.Gui):
        overlord = super().from_config(path)
        overlord.mode = mode
        overlord.gui = gui
        return overlord

    def handle_message(self, link: str, msg: str):
        def pwm(value):
            max_pwm = 1590  # 1832
            min_pwm = 1390  # 1148
            center = (max_pwm + min_pwm) / 2
            diff = (max_pwm - min_pwm) / 2
            return int(center + (diff * value))

        state = json.loads(msg)
        if not state["alive"]:
            self.stop()
            return

        if self.gui.has_quit():
            state["alive"] = False
            self.stop()
        else:
            self.gui.render()

            try:
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
            except KeyboardInterrupt:
                state["alive"] = False
                self.stop()

        self.publish(link, json.dumps(state, separators=(",", ":")))


class AutoOverlord(Overlord):
    def handle_message(self, link: str, msg: str):
        state = json.loads(msg)
        if not state["alive"]:
            self.stop()
            return
        command = {"lat": 1, "lon": 1, "alt": 1}
        state["command"] = command
        self.publish(link, json.dumps(state, separators=(",", ":")))


def main():
    # Parse Command Line Arguments
    parser = ArgumentParser()
    parser.add_argument(
        "-configuration",
        type=str,
        help=".json configuration file",
        default="controller_config.json",
    )
    parser.add_argument(
        "-mode",
        choices=["auto", "keyboard", "joystick"],
        help="control mode: auto, keyboard or joystick",
    )
    parser.add_argument("-verbose", action="store_true")
    args = parser.parse_args()

    if args.mode == "joystick" or args.mode == "keyboard":
        # Initializer GUI
        gui = pyGui.Gui(list(range(3), hasJoystick=args.mode))
        overlord = ManualOverlord.from_config(args.configuration, args.mode, gui)
        overlord.start()
        gui.stop()

    elif args.mode == "auto":
        overlord = AutoOverlord.from_config(args.configuration)
        overlord.start()


if __name__ == "__main__":
    main()
