import json
import numpy as np
import vizier.node
import pygame
import math
import time

import pyGui 

# Ensure that Node Descriptor File can be Opened
node_descriptor = None
try:
        f = open("node_desc_controller.json", 'r')
        node_descriptor = json.load(f)
        f.close()
except Exception as e:
    print(repr(e))
    print("Couldn't open given node file node_desc_controller.json")

# Start the Node
node = vizier.node.Node("localhost", 1884, node_descriptor)
node.start()

# Get the links for Publishing/Subscribing
publishable_link = list(node.publishable_links)[0]
subscribable_link = list(node.subscribable_links)[0]
msg_queue = node.subscribe(subscribable_link)

# Initialize Gui
gui = pyGui.Gui(False)

def monitor_vizier(callable):
    # Recieve data here
    try:
        #Recieve Vizier Messages
        message = msg_queue.get(timeout = 1).payload.decode(encoding='UTF-8')
        state = int(message)
    except:
        print("Connection to robot lost")
        node.publish(publishable_link,"0,0,0")
        callable()

gui.start(monitor_vizier)

#Clean up Connection
node.stop()