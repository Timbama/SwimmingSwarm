"""
Simplify connection to Pixhawk and communication though the MQTT broker
"""

import logging
import json
import time
import queue
from typing import Dict

from vizier import node
from dronekit import connect, VehicleMode


class Drone:
    """
    To use this class, you must override handle_start, handle_message and/or handle_stop.
    Then, create this class either through new() or from_config().
    DO NOT use __init__().
    Finally, run start(). stop() must be arranged to
    be called else start() will block forever
    """

    @classmethod
    def from_config(cls, path: str):
        """
        Create new Drone from a configuration file.
        """
        with open(path, "r") as file:
            configuration = json.load(file)
            connection_string = configuration["connection_string"]
            vehicle_mode = configuration["vehicle_mode"]
            broker_ip = configuration["broker"]["ip"]
            broker_port = configuration["broker"]["port"]
            node_descriptor = configuration["node"]
            return cls.new(
                connection_string, vehicle_mode, broker_ip, broker_port, node_descriptor
            )

    @classmethod
    def new(
        cls,
        connection_string: str,
        vehicle_mode: str,
        broker_ip: str,
        broker_port: int,
        node_descriptor: Dict,
    ):
        """
        Create new Overlord from connection_string, vehicle_mode,
        broker ip, broker port and a node descriptor dict
        """
        drone = Drone()
        drone.drone_node = node.Node(broker_ip, broker_port, node_descriptor)
        drone.vehicle = connect(connection_string, wait_ready=True, baud=57600)
        drone.set_vehicle_mode(vehicle_mode)

    def __init__(self):
        self.drone_node = None
        self.vehicle = None
        self.active = False
        self.subscribables = {}

    def start(self):
        """
        Arm vehicle and start listening and responding to MQTT commands
        """
        # Wait for vehicle armable
        self.wait_vehicle_armable()
        # Arm verhicle
        self.set_vehicle_armed(True)
        # Start Vizier node
        self.drone_node.start()
        # Trigger overriden function after vehicle had been armed and Vizier node set up
        self.handle_start()
        # Subscribe to all links
        for link in self.drone_node.subscribable_links:
            self.subscribables[link] = self.drone_node.subscribe(link)

        # Send the initial condition
        state = {"alive": True}

        for link in self.drone_node.publishable_links:
            self.drone_node.publish(link, json.dumps(state, separators=(",", ":")))

        while self.active:
            for link in self.subscribables:
                sub_queue = self.subscribables[link]
                try:
                    msg = sub_queue.get(block=False).decode(encoding="UTF-8")
                    self.handle_message(link, msg)
                except queue.Empty:
                    pass

        # Disarm verhicle
        self.set_vehicle_armed(False)
        self.handle_stop()
        self.drone_node.stop()

        # Disarm vehicle
        self.set_vehicle_armed(False)

    def handle_start(self):
        """
        You must implement this method to handle what happens
        AFTER the MQTT node is started and the vehicle is armed
        but BEFORE the event loop is started.
        """
        # pylint: disable=no-self-use
        return

    def handle_message(self, link: str, msg: str):
        """
        You must implement this method to handle messages sent by the controller.
        """
        # pylint: disable=unused-argument, no-self-use
        return

    def handle_stop(self):
        """
        You must implement this method to handle what happens
        AFTER the event loop is stopped and the vehicle is disarmed
        but BEFORE the MQTT node is stopped.
        """
        # pylint: disable=no-self-use
        return

    def stop(self):
        """
        Stop event loop for the MQTT client, then disarm the vehicle
        """
        self.active = False

    def set_vehicle_mode(self, new_mode: str):
        """
        Set the vehicle mode. Will block until mode changed successfully.
        """
        logging.info("Set vehice mode: %s", new_mode)
        self.vehicle.mode = VehicleMode(new_mode)
        while self.vehicle.mode.name != new_mode:
            time.sleep(1)

    def set_vehicle_armed(self, armed: bool):
        """
        Arm the vehicle. Will block until vehicle is armed.
        """
        logging.info("Arming motors" if armed else "Disarming motors")
        self.vehicle.armed = armed
        while not self.vehicle.armed:
            time.sleep(1)

    def wait_vehicle_armable(self):
        """
        Block until the vehicle is armable.
        """
        logging.info("Basic pre-arm checks")
        while not self.vehicle.is_armable:
            time.sleep(1)

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

    def channel_command(self, pitch: int, roll: int, yaw: int, throttle: int):
        """
        Directly control the vehicle through motor channels
        """
        # Ch1 =Roll, Ch 2=Pitch, Ch 3=Horizontal throttle, Ch 4=Yaw, Ch 5=Forward throttle
        self.vehicle.channels.overrides["1"] = roll
        self.vehicle.channels.overrides["2"] = pitch
        self.vehicle.channels.overrides["5"] = throttle
        self.vehicle.channels.overrides["4"] = yaw
