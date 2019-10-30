from argparse import ArgumentParser
import json
import pyGui
from swarm.overlord import Overlord

from vizier import node

def main():
    # Parse Command Line Arguments
    parser = ArgumentParser()
    parser.add_argument("-configuration", help = ".json configuration file",
                        default = "controller_config.json")
    parser.add_argument("-joystick", action = "store_true")
    args = parser.parse_args()

    # Ensure that Configuration File can be Opened
    configuration = None
    try:
        f = open(args.configuration, 'r')
        configuration = json.load(f)
        f.close()
    except Exception as e:
        print(repr(e))
        print("Cannot open configuration file" + args.configuration)
        return -1

    # Initializer GUI with keyboard
    overlord = Overlord(configuration)
    gui = pyGui.Gui(hasJoystick = args.joystick)

    def communicate(message):
        if gui.hasQuit():
            overlord.stop()
            return ""
        else:
            state = int(message)
            if (state == 0):
                overlord.stop()
            if (args.joystick):
                command = gui.get_joystick_axis()
            else:
                command = gui.get_keyboard_command()
            command = (int(-command[0]), int(-command[1]), int(-command[2]), int(-command[3]))
            print('Control input =\t{0},\t{1},\t{2},\t{3}'.format(command[0],command[1],command[2],command[3]), end = '\r')
            return str(command)

    overlord.addEventListener("message", communicate)
    overlord.addEventListener("loop", gui.render)
    overlord.addEventListener("stop", gui.stop)

    overlord.start()

if(__name__ == "__main__"):
    main()