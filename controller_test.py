import vizier.node as vizier_node
import json

# Ensure that Node Descriptor File can be Opened
node_descriptor = None
try:
        f = open("node_desc_controller.json", 'r')
        node_descriptor = json.load(f)
        print(node_descriptor)
        f.close()
except Exception as e:
    print(repr(e))
    print("Couldn't open given node file node_desc_controller.json")

node = vizier_node.Node("localhost", 1884, node_descriptor)

# Get the links for Publishing/Subscribing
publishable_link = list(node.publishable_links)[0]
subscribable_link = list(node.subscribable_links)[0]
msg_queue = node.subscribe(subscribable_link)
print("Got the links")

#Initialize Connection
print("Connecting to Robot")

node.publish(publishable_link,"0,0,0")
state = 0

done = False
recieved = False

while not done:
    # Recieve data here
    try:
        #Recieve Vizier Messages
        message = msg_queue.get(timeout = 1).payload.decode(encoding='UTF-8')
        state = int(message)
    except:
        if recieved:
            node.publish(publishable_link,"0,0,0")
            break
        else:
            recieved = True
            state = 1

    if state != 1:
        #Robot sent back bad status
        print("Connection to robot lost")
        node.publish(publishable_link,"0,0,0")
        break

    #Send Vizier Message
    node.publish(publishable_link, "important stuff")

print("Exiting")

