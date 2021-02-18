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

from dronekit_sitl import SITL


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
            drone = cls()
            drone.drone_node = node.Node(broker_ip, broker_port, node_descriptor)
            drone.vehicle = connect(connection_string, wait_ready=True, baud=57600)
            drone.set_vehicle_mode(vehicle_mode)
            return drone

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
        Create new Drone from connection_string, vehicle_mode,
        broker ip, broker port and a node descriptor dict
        """
        drone = cls()
        drone.drone_node = node.Node(broker_ip, broker_port, node_descriptor)
        drone.vehicle = connect(connection_string, wait_ready=True, baud=57600)
        drone.set_vehicle_mode(vehicle_mode)
        return drone

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
        self.arm_vehicle()
        # Start Vizier node
        self.drone_node.start()
        # Trigger overriden function after vehicle had been armed and Vizier node set up
        self.handle_start()
        # Subscribe to all links
        for link in self.drone_node.subscribable_links:
            logging.info("Subscribing to %s", link)
            self.subscribables[link] = self.drone_node.subscribe(link)

        state = {"alive": True}

        # Send the initial condition
        self.publish_all(json.dumps(state, separators=(",", ":")))

        self.active = True

        logging.info("Listening for messages")
        while self.active:
            for link in self.subscribables:
                sub_queue = self.subscribables[link]
                try:
                    msg = sub_queue.get(timeout=0.1)
                    self.handle_message(link, msg)
                except queue.Empty:
                    time.sleep(0.1)
                except KeyboardInterrupt:
                    self.stop()

        # Stop verhicle
        self.vehicle.close()

        self.handle_stop()
        self.drone_node.stop()

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

    def arm_vehicle(self):
        """
        Arm the vehicle. Will block until vehicle is armed.
        """
        logging.info("Arming motors")
        self.vehicle.armed = True
        while not self.vehicle.armed:
            time.sleep(1)
        logging.info("Arming complete")

    def wait_vehicle_armable(self):
        """
        Block until the vehicle is armable.

        There are some problem with this check when testing without batteries, needs more investigation
        """
        logging.info("Basic pre-arm checks")
        while not self.vehicle.is_armable:
            time.sleep(1)
        logging.info("Pre-arm checks complete")

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


class DroneSitl(Drone):
    """
    To use this class, you must override handle_start, handle_message and/or handle_stop.
    Then, create this class either through new() or from_config().
    DO NOT use __init__().
    Finally, run start(). stop() must be arranged to
    be called else start() will block forever
    """

    @classmethod
    def from_config(cls, config_path: str, sitl_path: str):
        """
        Create new Drone from a configuration file. Ignores connection_string to use SITL.
        """
        # pylint: disable=arguments-differ
        with open(config_path, "r") as file:
            configuration = json.load(file)
            sitl = SITL(path=sitl_path)
            sitl.launch([])
            vehicle_mode = configuration["vehicle_mode"]
            broker_ip = configuration["broker"]["ip"]
            broker_port = configuration["broker"]["port"]
            node_descriptor = configuration["node"]
            return cls.new(
                sitl,
                vehicle_mode,
                broker_ip,
                broker_port,
                node_descriptor,
            )

    @classmethod
    def new(
        cls,
        sitl: SITL,
        vehicle_mode: str,
        broker_ip: str,
        broker_port: int,
        node_descriptor: Dict,
    ):
        """
        Create new Drone from SITL simulator, vehicle_mode,
        broker ip, broker port and a node descriptor dict
        """
        # pylint: disable=arguments-differ
        drone = cls()
        drone.sitl = sitl
        drone.drone_node = node.Node(broker_ip, broker_port, node_descriptor)
        drone.vehicle = connect(drone.sitl.connection_string(), wait_ready=True)
        drone.set_vehicle_mode(vehicle_mode)
        return drone

    def __init__(self):
        super().__init__()
        self.sitl = None
