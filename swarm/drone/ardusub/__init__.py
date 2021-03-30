"""
Simplify connection to Pixhawk and communication though the MQTT broker
"""

import logging
import json
import time
from typing import Dict

from dronekit import connect, VehicleMode

# pylint: disable=import-error
from swarm import VizierAgent


class DronekitDrone(VizierAgent):
    """
    To use this class, you must override handle_message.
    Then, create this class either through new() or from_config().
    Finally, run start(), then step() in succession. stop() can be called
    so that the Vizier is stopped and further call to step() will do nothing.
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
            drone = cls(
                broker_ip,
                broker_port,
                node_descriptor,
                connection_string,
                vehicle_mode,
            )
            return drone

    def __init__(
        self,
        broker_ip: str,
        broker_port: int,
        node_descriptor: Dict,
        connection_string: str,
        vehicle_mode: str,
    ):
        super().__init__(broker_ip, broker_port, node_descriptor)
        self.vehicle = connect(connection_string, wait_ready=True, baud=57600)
        self.set_vehicle_mode(vehicle_mode)

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

    def channel_command(self, pitch: int, roll: int, yaw: int, throttle: int):
        """
        Directly control the vehicle through motor channels
        """
        # Ch1 =Roll, Ch 2=Pitch, Ch 3=Horizontal throttle, Ch 4=Yaw, Ch 5=Forward throttle
        self.vehicle.channels.overrides["1"] = roll
        self.vehicle.channels.overrides["2"] = pitch
        self.vehicle.channels.overrides["5"] = throttle
        self.vehicle.channels.overrides["4"] = yaw