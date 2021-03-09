import logging
import queue

from abc import ABC, abstractmethod
from typing import Dict
from vizier import node


class Drone(ABC):
    """
    A Drone abstract class have a lifetime like so:
    1. Initialization: drone = Done()
    2. The MQTT node is started: drone.start()
    3. Repeatedly call drone.step() which will call drone.handle_message() for each message
    4. drone.handle_message() can call drone.stop() which will stop the MQTT node
        and set self.active = False
    """

    def __init__(
        self,
        broker_ip: str,
        broker_port: int,
        node_descriptor: Dict,
    ):
        """
        Create new Drone from connection_string, vehicle_mode,
        broker ip, broker port and a node descriptor dict
        """
        self.drone_node = node.Node(broker_ip, broker_port, node_descriptor)
        self.subscribables = {}
        self.active = False

    def start(self):
        """
        Start the MQTT node, subscribe to all links and set self.active = True
        """
        # Start Vizier node
        self.drone_node.start()

        logging.info("Publishable links %s", self.drone_node.publishable_links)

        # Subscribe to all links
        for link in self.drone_node.subscribable_links:
            logging.info("Subscribing to %s", link)
            self.subscribables[link] = self.drone_node.subscribe(link)

        self.active = True

    def stop(self):
        """
        Stop the MQTT node and set self.active = False
        """
        self.drone_node.stop()
        self.active = False

    def step(self):
        """
        A step of message handling, which tries to receives 1 message from every
        subscribed link and process them
        """
        if self.active:
            for link in self.subscribables:
                sub_queue = self.subscribables[link]
                try:
                    msg = sub_queue.get_nowait()
                    self.handle_message(link, msg)
                except queue.Empty:
                    self.handle_message(link, "")

    def publish(self, link: str, message: str):
        """
        Publish a message through this link
        """
        self.drone_node.publish(link, message)

    def publish_all(self, message: str):
        """
        Publish a message through all links connected to this node
        """
        for link in self.drone_node.publishable_links:
            self.drone_node.publish(link, message)

    @abstractmethod
    def handle_message(self, link: str, msg: str):
        """
        You must implement this method to handle messages sent to each link.
        If there are no message, msg will be an empty string.
        This only runs when self.active = True
        """
        return
