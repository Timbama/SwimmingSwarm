#socket_echo_server.py

from dronekit import connect, VehicleMode

import argparse
import json
import vizier.node as vizier_node
import time

def main():
    # Parse Command Line Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-node_descriptor", help=".json file node descriptor",
                        default="node_desc_robot.json")
    parser.add_argument("-port", type=int, help="MQTT Port", default=8080)
    parser.add_argument("-connection_string", type=str, help="Pixhawk connection stirng",
                        default="/dev/serial/by-id/usb-3D_Robotics_PX4_FMU_v2.x_0-if00")
    parser.add_argument("host", help="MQTT Host IP")

    args = parser.parse_args()

    #Dronekit connection
    print("Connecting to vehicle on: %s" % (args.connection_string,))
    connected = False
    while not connected:
        try:
            vehicle = connect(args.connection_string, wait_ready=True)
            connected = True
        except Exception as e:
            print(e)
            print("Retrying connection")

    print("Waiting for vehicle to initialize...", end="")
    while not vehicle.is_armable:
        print(".", end="")
        time.sleep(1)
    print("\n")

    print("Arming motors...")
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True
    print("Waiting for arming...", end="")
    while not vehicle.armed:
        print(".", end="")
        time.sleep(1)
    print("\n")

    # Vizier connection
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
    node = vizier_node.Node(args.host, args.port, node_descriptor)
    
    # Start the node
    node.start()

    # Get the links for Publishing/Subscribing
    publishable_link = list(node.publishable_links)[0]
    subscribable_link = list(node.subscribable_links)[0]
    msg_queue = node.subscribe(subscribable_link)

    # Set the initial condition
    state = 1
    node.publish(publishable_link, str(state))
    while state == 1:
        input = [0,0,0,0]
        try:
            message = msg_queue.get(timeout=0.1).decode(encoding='UTF-8')
            input = message[1:-1].split(',')
            yaw = float(input[0])
            throttle = float(input[1])
            depth_yaw = float(input[2])
            depth = float(input[3])
            #commandMavLink(vehicle, yaw, throttle, depth_yaw, depth)
        except KeyboardInterrupt:
            state = 0
        except Exception as e:
            print(e)
            state = 0
        node.publish(publishable_link, str(state))

    # Stop node
    print("Disconnecting...")
    node.stop()

    # Stop vehicle
    vehicle.armed = False
    while vehicle.armed:
        print("Waiting for disarm...", end="\r")
        time.sleep(1)
    print("Disconnected")

if (__name__ == "__main__"):
    main()