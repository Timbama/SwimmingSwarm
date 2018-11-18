#socket_echo_server.py

from dronekit import connect

import json
import vizier.node as vizier_node

def main():
    # Parse Command Line Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-node_descriptor", help=".json file node information",
                        default="node_desc_robot.json")
    parser.add_argument("-port", type=int, help="MQTT Port", default=8080)
    parser.add_argument("host", help="MQTT Host IP")

    args = parser.parse_args()

    #PymavLink connection
    connection_string = "/dev/serial/by-id/usb-3D_Robotics_PX4_FMU_v2.x_0-if00"
    vehicle = connect(connection_string, wait_ready=True) #connect over mavlink
    vehicle.armed = True

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
            commandMavLink(yaw, throttle, depth_yaw, depth)
        except KeyboardInterrupt:
            break
        except Exception:
            print("Connection Error")
            state = 0
        node.publish(publishable_link, str(state))
    
    # Stop node and Pymavlink
    node.stop()
    vehicle.armed = False
    vehicle.channels.overrides = {}

def joystickToChannel(value):
    #Channels range from 1200 to 1700 with 1500 being the center value
    center = (1300 + 1700)/2
    diff = (1700 - 1300)/2
    return int(center + (diff * value))

def commandMavLink(yaw, throttle, depth_yaw, depth):
    #Send Commands over Mavlink
    vehicle.channels.overrides = {'4': joystickToChannel(yaw), '5': joystickToChannel(throttle), '3': joystickToChannel(depth)}
    print('Command = {0},{1},{2},{3}'.format(int(yaw),int(throttle),int(depth_yaw),int(depth)), end='\r')

if (__name__ == "__main__"):
    main()