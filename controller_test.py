import argparse
import json
import vizier.node as vizier_node

def main():
    # Parse Command Line Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("node_descriptor", help=".json file node information",
                         default="node_desc_controller.json")
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

    # Control stuffs
    ref = 5.0
    state = 1.0e6
    print('\n')
    while abs(ref - state) >= 0.001:
        try:
            message = msg_queue.get(timeout=1).decode(encoding='UTF-8')
            state = float(message)
        except KeyboardInterrupt:
            break
        except Exception:
            continue
        print('Control input = {}'.format(ref-state), end='\r')
        node.publish(publishable_link, str(ref-state))
    print('\n')
    node.stop()


if(__name__ == "__main__"):
main()

# #Initialize Connection
# print("Connecting to Robot")

# node.publish(publishable_link,"0,0,0")
# state = 0

# done = False
# recieved = False

# while not done:
#     # Recieve data here
#     try:
#         #Recieve Vizier Messages
#         message = msg_queue.get(timeout = 1).payload.decode(encoding='UTF-8')
#         state = int(message)
#     except:
#         if recieved:
#             node.publish(publishable_link,"0,0,0")
#             break
#         else:
#             recieved = True
#             state = 1

#     if state != 1:
#         #Robot sent back bad status
#         print("Connection to robot lost")
#         node.publish(publishable_link,"0,0,0")
#         break

#     #Send Vizier Message
#     node.publish(publishable_link, "important stuff")

# print("Exiting")