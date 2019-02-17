import argparse
import json
import vizier.node
import queue

import pyGui

def main():
    # Parse Command Line Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-node_descriptor", help = ".json file node information",
                         default = "node_desc_controller.json")
    parser.add_argument("-port", type = int, help = "MQTT Port", default = 8080)
    parser.add_argument("-host", help = "MQTT Host IP", default = "localhost")
    parser.add_argument("-test", help = "test mode, disable joystick", action = "store_true")
    parser.add_argument("-keyboard", help = "keyboard mode, used arrow keys", action="store_true")

    args = parser.parse_args()

    # Ensure that Node Descriptor File can be Opened
    node_descriptor = None
    try:
        f = open(args.node_descriptor, 'r')
        node_descriptor = json.load(f)
        f.close()
    except Exception as e:
        print(repr(e))
        print("Couldn't open given node file " + args.node_descriptor)
        return -1

    # Start the Node
    node = vizier.node.Node(args.host, args.port, node_descriptor)
    node.start()

    # Get the links for Publishing/Subscribing
    publishable_link = list(node.publishable_links)[0]
    subscribable_link = list(node.subscribable_links)[0]
    msg_queue = node.subscribe(subscribable_link)

    # Initializer GUI
    if (args.test or args.keyboard):
        gui = pyGui.Gui(False)
    else:
        gui = pyGui.Gui(True)
    done = False

    def communicate(callable):
        try:
            message = msg_queue.get(timeout=0.1).decode(encoding = 'UTF-8')
            state = int(message)
            if (state == 0):
                callable()
            if not args.keyboard:
                command =  gui.get_joystick_axis()
            else:
                command = gui.get_keyboard_command()
            print('Control input =\t{0},\t{1},\t{2},\t{3}'.format(command[0],command[1],command[2],command[3]), end = '\r')
            node.publish(publishable_link, str(command))
        except KeyboardInterrupt:
            callable()
        except queue.Empty:
            pass
        except Exception as e:
            print(e)
            callable()

    gui.start(communicate)
    node.stop()


if(__name__ == "__main__"):
    main()