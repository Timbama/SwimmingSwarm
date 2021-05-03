"""
Simplify connection and communication through an MQTT broker
"""

import queue
import logging
from typing import Dict
from abc import ABC, abstractmethod

from vizier import node


class VizierAgent(ABC):
    """
    A Vizier Agent capable of sending and receiving messages over multiple links.

    To use this class, you must override handle_message.

    Its lifetime:
    1. Initialization: VizierAgent = VizierAgent()
    2. The Vizier node is started: VizierAgent.start()
    3. Repeatedly call VizierAgent.step() which will call VizierAgent.handle_message() for each message
    4. When VizierAgent.stop() is called, Vizier node is stopped and VizierAgent.step() will no longer do anything.
    """

    def __init__(self, broker_ip: str, broker_port: int, node_descriptor: Dict):
        self.vizier_node = node.Node(broker_ip, broker_port, node_descriptor)
        self.active = False
        self.subscribables = {}

    @abstractmethod
    def handle_message(self, link: str, msg: str):
        """
        You must implement this method to handle messages sent to each link.
        If there are no message, msg will be an empty string.
        This only runs when self.active = True
        """
        return

    def start(self):
        """
        Start the MQTT node, subscribe to all links and set self.active = True
        """
        self.vizier_node.start()
        logging.info("Started Vizier node")

        for link in self.vizier_node.subscribable_links:  # set
            logging.info("Subscribing to %s", link)
            self.subscribables[link] = self.vizier_node.subscribe(link)  # queue

        logging.info("Publishable links %s", self.vizier_node.publishable_links)

        self.active = True

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

    def stop(self):
        """
        Stop the MQTT node and set self.active = False
        """
        self.vizier_node.stop()
        logging.info("Stopped Vizier node")
        self.active = False

    def publish(self, link: str, message: str):
        """
        Publish a message through this link
        """
        logging.info("Published message: %s to link %s", message, link)
        self.vizier_node.publish(link, message)

    def publish_all(self, message: str):
        """
        Publish a message through all links connected to this node
        """
        logging.info("Published message: %s to all links", message)
        for link in self.vizier_node.publishable_links:
            self.vizier_node.publish(link, message)
