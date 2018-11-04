import json
import vizier.node as vizier_nod

# Ensure that Node Descriptor File can be Opened
node_descriptor = None
try:
        f = open("node_desc_robot.json", 'r')
        node_descriptor = json.load(f)
        f.close()
except Exception as e:
    print(repr(e))
    print("Couldn't open given node file node_desc_robot.json")

# Start the Node
node = vizier_node.Node("128.61.72.236", 1884, node_descriptor)
node.start()


# Get the links for Publishing/Subscribing
publishable_link = list(node.publishable_links)[0]
subscribable_link = list(node.subscribable_links)[0]
msg_queue = node.subscribe(subscribable_link)

#Initialize Connection
print("Connecting to Controller")

node.publish(publishable_link,"1")
message = msg_queue.get(timeout = 10).decode(encoding='UTF-8')

recieved = False

while True:
    try:
        # Recieve Vizier Messages
        message = msg_queue.get(timeout = 1).decode(encoding='UTF-8')
    except KeyboardInterrupt:
        break
    except:
        if recieved:
            print("Connection to Controller Lost")
            node.publish(publishable_link, "0")
            break
        else:
            recieved = True

    # Send Vizier Message
    node.publish(publishable_link,"1")

# Clean up the connection
node.publish(publishable_link,"0")
node.stop()
