from argparse import ArgumentParser
import json
import pyGui
from swarm.overlord import Overlord

from vizier import node
import time

def main():
    # Parse Command Line Arguments
    parser = ArgumentParser()
    parser.add_argument("-configuration", type=str, help = ".json configuration file",
                        default = "controller_config.json")
    parser.add_argument("-mode", choices=["auto","keyboard","joystick"], help = "control mode: auto, keyboard or joystick")
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

    if args.mode == "joystick" or args.mode == "keyboard":
        gui = pyGui.Gui(hasJoystick = args.mode == "joystick")

        def setup():
            setup_config = {"vehicle_mode": "STABILIZE"}
            overlord.publish("TODO: MANUAL SETUP")

        def render_and_send_command():
            gui.render()
            manual_command(overlord.get_message(timeout=1))

        def manual_command(message):
            if gui.has_quit():
                overlord.stop()
                return ""
            else:
                state = json.loads(message)
                if (state["alive"] == False):
                    overlord.stop()
                    gui.stop()
                    return
                if (args.mode == "joystick"):
                    command = gui.get_joystick_axis()
                elif (args.mode == "keyboard"):
                    command = gui.get_keyboard_command()
                command = (int(-command[0]), int(-command[1]), int(-command[2]), int(-command[3]))
                print('Control input =\t{0},\t{1},\t{2},\t{3}'.format(command[0],command[1],command[2],command[3]), end = '\r')
                state["command"] = command
                overlord.publish(json.dumps(state, separators=(',',':')))
        overlord.add_event_listener("loop", render_and_send_command)
        overlord.add_event_listener("stop", gui.stop)
    elif args.mode == "auto":
        start_time = 0
        def setup():
            start_time = time.time()
            setup_config = {
                "vehicle_mode": "GUIDED",
                "start_time": start_time,
                "parameters": {
                    "EK3_ENABLE": 1,
                    "EK2_ENABLE": 0,
                    "AHRS_EKF_TYPE": 3,
                    "EK3_GPS_TYPE": 0,
                    "EK3_MAG_CAL": 5,
                    "EK3_ALT_SOURCE": 2,
                    "GPS_TYPE": 14,
                    "GPS_DELAY_MS": 50,
                    "COMPASS_USE": 0,
                    "COMPASS_USE2": 0,
                    "COMPASS_USE3": 0
                }
            }
            overlord.publish(json.dumps(setup_config, separators=(',',':')))
            state = json.loads(overlord.get_message(timeout=1))
            while "alive" not in state:
                start_time = time.time()
                setup_config["start_time"]  = start_time
                overlord.publish(setup_config)
                state = json.loads(overlord.get_message(timeout=1))
        
        def auto_command():
            state = json.loads(overlord.get_message(timeout=1))
            if state["alive"] == False:
                overlord.stop()
                return
            command = {"lat":1,"lon":1,"alt":1}
            overlord.publish(json.dumps(command, separators=(',',':')))
        
        overlord.add_event_listener("start", setup)
        overlord.add_event_listener("loop", auto_command)

    overlord.start()

if(__name__ == "__main__"):
    main()