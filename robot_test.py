#socket_echo_server.py

from dronekit import connect, VehicleMode

import argparse
import dronekit_sitl
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
    parser.add_argument("-test", action="store_true")
    parser.add_argument("host", help="MQTT Host IP")

    args = parser.parse_args()

    connection_string = args.connection_string

    if (args.test):
        sitl = dronekit_sitl.start_default()
        connection_string = sitl.connection_string()

    #Dronekit connection
    print("Connecting to vehicle on: %s" % (connection_string,))
    connected = False
    while not connected:
        try:
            vehicle = connect(connection_string, wait_ready=True)
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

    def stop(dronekit_sitl = None):
        # Stop node
        print("Disconnecting...")
        node.stop()

        #Stop vehicle
        vehicle.armed = False
        print("Waiting for disarm...", end="")
        while vehicle.armed:
            print(".", end="")
            time.sleep(1)

        # If it's a test, stop dronekit_sistl
        if (dronekit_sitl != None):
            dronekit_sitl.stop()

        print("Disconnected")

    if (args.test):
        stop(sitl)
    else:
        stop()

def joystickToChannel(value):
    #Channels range from 1200 to 1700 with 1500 being the center value
    center = (1300 + 1700)/2
    diff = (1700 - 1300)/2
    return int(center + (diff * value))

# Overriding channel is discouraged and throws error, TODO: find alternate way
def commandMavLink(vehicle, yaw, throttle, depth_yaw, depth):
    #Send Commands over Mavlink
    vehicle.channels.overrides = {'4': joystickToChannel(yaw), '5': joystickToChannel(throttle), '3': joystickToChannel(depth)}
    print('Command = {0},{1},{2},{3}'.format(int(yaw),int(throttle),int(depth_yaw),int(depth)), end='\r')

# Example velocity control code on Dronekit
def send_ned_velocity(velocity_x, velocity_y, velocity_z, duration):
    """
    Move vehicle in direction based on specified velocity vectors.
    """
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0,       # time_boot_ms (not used)
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_FRAME_LOCAL_NED, # frame
        0b0000111111000111, # type_mask (only speeds enabled)
        0, 0, 0, # x, y, z positions (not used)
        velocity_x, velocity_y, velocity_z, # x, y, z velocity in m/s
        0, 0, 0, # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
        0, 0)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)

    # send command to vehicle on 1 Hz cycle
    for x in range(0,duration):
        vehicle.send_mavlink(msg)
        time.sleep(1)

if (__name__ == "__main__"):
    main()