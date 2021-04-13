import logging
import json
from argparse import ArgumentParser

#from swarm.overlord import Overlord

import pyGui


def main():
    # Parse Command Line Arguments
    parser = ArgumentParser()
    #parser.add_argument("configuration", type=str, help=".json configuration file")
    parser.add_argument(
        "-mode",
        choices=["auto", "keyboard", "joystick"],
        help="control mode: auto, keyboard or joystick",
    )
    args = parser.parse_args()

    if args.mode == "joystick" or args.mode == "keyboard":

        #fake list of bots
        #signature, x coord, y coord
        bots_first_part = []
        for i in range(4):
            bots_first_part.append([i, (i+1)*30, (i+2)*30])
        bots = bots_first_part

        # Initializer GUI
        gui = pyGui.Gui(bots, hasJoystick=args.mode == "joystick")
        #overlord = ManualOverlord.from_config(args.configuration, args.mode, gui)

        running = True
        while running:
            gui.render()
            if gui.has_quit(): running = False
        #overlord.start()

        gui.stop()

    elif args.mode == "auto":
        overlord = AutoOverlord.from_config(args.configuration)
        overlord.start()

if __name__ == "__main__":
    main()