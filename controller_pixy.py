from argparse import ArgumentParser
import json
import pyGui
from swarm.overlord import Overlord
import time
from pixyController import PixyController

def main():
    # Parse Command Line Arguments
    parser = ArgumentParser()
    parser.add_argument("-configuration", type=str, help = ".json configuration file",
                        default = "controller_config.json")
    parser.add_argument("-mode", choices=["auto","keyboard","joystick"], help = "control mode: auto, keyboard or joystick")
    parser.add_argument("-verbose", action = "store_true")
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
    overlord = Overlord(configuration, args.verbose)

    # Initialize PixyController
    pixyController = PixyController()

    if args.mode == "joystick" or args.mode == "keyboard":
        gui = pyGui.Gui(hasJoystick = args.mode == "joystick")

        def render_and_send_command():
            if gui.has_quit():
                overlord.stop()
                return
            gui.render()
            manual_command(overlord.get_message(timeout=0.1))

        def manual_command(message):
            def pwm(value):
                max_pwm = 1590 #1832
                min_pwm = 1390 #1148
                center = (max_pwm + min_pwm)/2
                diff = (max_pwm - min_pwm)/2
                return int(center + (diff * value))
            state = json.loads(message)
            if (state["alive"] == False):
                overlord.stop()
                return
            if (args.mode == "joystick"):
                command = gui.get_joystick_axis()
            elif (args.mode == "keyboard"):
                command = gui.get_keyboard_command()
            command = (pwm(-command[0]), pwm(-command[1]), pwm(-command[2]), pwm(-command[3]))
            print(command)
            state["command"] = command
            overlord.publish(json.dumps(state, separators=(',',':')))

        overlord.add_event_listener("loop", render_and_send_command)
        overlord.add_event_listener("stop", gui.stop)
    elif args.mode == "auto":
        def auto_command():
            state = json.loads(overlord.get_message(timeout=1))
            print(state)
            if state["alive"] == False:x
                overlord.stop()
                return
            command = {"lat":1,"lon":1,"alt":1}
            state["command"] = command
            overlord.publish(json.dumps(state, separators=(',',':')))
        
        overlord.add_event_listener("loop", auto_command)
    else:
        return

    overlord.start()
    if args.mode == "joystick" or args.mode == "keyboard":
        gui.stop()

if(__name__ == "__main__"):
    main()
