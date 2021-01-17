"""
Simplify connection and communication through an MQTT broker
"""

import json
import queue
import logging
from typing import Dict

from vizier import node


class Overlord:
    """
    To use this class, you must override handle_start, handle_message and/or handle_stop.
    Then, create this class either through new() or from_config().
    DO NOT use __init__().
    Finally, run start(). stop() must be arranged to
    be called else start() will block forever
    """

    def __init__(self):
        self.host_node = None
        self.active = False
        self.subscribables = {}

    @classmethod
    def from_config(cls, path: str):
        """
        Create new Overlord from a configuration file.
        """
        with open(path, "r") as file:
            configuration = json.load(file)
            broker_ip = configuration["broker"]["ip"]
            broker_port = configuration["broker"]["port"]
            node_descriptor = configuration["node"]
            overlord = cls()
            overlord.host_node = node.Node(broker_ip, broker_port, node_descriptor)
            return overlord

    @classmethod
    def new(cls, broker_ip: str, broker_port: int, node_descriptor: Dict):
        """
        Create new Overlord from broker ip, broker port and a node descriptor dict
        """
        overlord = cls()
        overlord.host_node = node.Node(broker_ip, broker_port, node_descriptor)
        return overlord

    def handle_start(self):
        """
        You must implement this method to handle what happens
        AFTER the MQTT node is started but BEFORE the event loop is started.
        """
        # pylint: disable=no-self-use
        return

    def handle_message(self, link: str, msg: str):
        """
        You must implement this method to handle messages published by a robot.
        """
        # pylint: disable=unused-argument, no-self-use
        return

    def handle_stop(self):
        """
        You must implement this method to handle what happens
        AFTER the event loop is stopped but BEFORE the MQTT node is stopped.
        """
        # pylint: disable=no-self-use
        return

    def start(self):
        """
        Call this method to start the event loop for the MQTT client.
        """
        self.host_node.start()
        self.handle_start()

        logging.info("Publishable links %s", self.host_node.subscribable_links)

        for link in self.host_node.subscribable_links:
            logging.info("Subscribing to %s", link)
            self.subscribables[link] = self.host_node.subscribe(link)

        self.active = True
        while self.active:
            for link in self.subscribables:
                sub_queue = self.subscribables[link]
                try:
                    msg = sub_queue.get_nowait()
                    self.handle_message(link, msg)
                except queue.Empty:
                    continue
                except KeyboardInterrupt:
                    self.stop()
                    break

        self.handle_stop()
        self.host_node.stop()

    def stop(self):
        """
        Stop event loop for the MQTT client
        """
        self.active = False

    def publish(self, link: str, message: str):
        """
        Publish a message through this link
        """
        self.host_node.publish(link, message)

    def publish_all(self, message: str):
        """
        Publish a message through all links connected to this node
        """
        for link in self.host_node.publishable_links:
            self.host_node.publish(link, message)
