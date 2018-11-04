
import time
import json
import argparse
import random
import vizier.node as vizier_node

def main():

    # Parse Command Line Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("node_descriptor", help=".json file node information",
                        default="node_desc_robot.json")
    parser.add_argument("-port", type=int, help="MQTT Port", default=8080)
    parser.add_argument("-host", help="MQTT Host IP", default="localhost")

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
    node = vizier_node.Node(args.host, args.port, node_descriptor)
    node.start()

    # Get the links for Publishing/Subscribing
    publishable_link = list(node.publishable_links)[0]
    subscribable_link = list(node.subscribable_links)[0]
    msg_queue = node.subscribe(subscribable_link)

    # Set the initial condition
    state = 10*random.random() - 5
    dt = 0.0
    node.publish(publishable_link, str(state))
    print('\n')
    while abs(state - 5) >= 0.001:
        tick = time.time()
        try:
            message = msg_queue.get(timeout=0.1).decode(encoding='UTF-8')
            input = float(message)
        except KeyboardInterrupt:
            break
        except Exception:
            input = 0.0
        tock = time.time()
        dt = tock - tick
        state = state + dt * input
        print('\t\t\t\t\t\tState = {}'.format(state), end='\r')
        node.publish(publishable_link, str(state))
    print('\n')
    node.stop()


if (__name__ == "__main__"):
    main()

# # Start the Node
# node = vizier_node.Node("128.61.72.236", 1884, node_descriptor)
# node.start()

# #Initialize Connection
# print("Connecting to Controller")

# node.publish(publishable_link,"1")
# message = msg_queue.get(timeout = 10).decode(encoding='UTF-8')

# recieved = False

# while True:
#     try:
#         # Recieve Vizier Messages
#         message = msg_queue.get(timeout = 1).decode(encoding='UTF-8')
#     except KeyboardInterrupt:
#         break
#     except:
#         if recieved:
#             print("Connection to Controller Lost")
#             node.publish(publishable_link, "0")
#             break
#         else:
#             recieved = True

#     # Send Vizier Message
#     node.publish(publishable_link,"1")

# # Clean up the connection
# node.publish(publishable_link,"0")
# node.stop()
