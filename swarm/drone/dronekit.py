"""
Simplify connection to Pixhawk and communication though the MQTT broker
"""

import logging
import json
import time
from typing import Dict

from dronekit import connect, VehicleMode

from dronekit_sitl import SITL

from . import Drone


class DronekitDrone(Drone):
    """
    To use this class, you must override handle_start, handle_armed, handle_message and handle_stop.
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
            drone = cls(
                connection_string, vehicle_mode, broker_ip, broker_port, node_descriptor
            )
            return drone

    def __init__(
        self,
        connection_string: str,
        vehicle_mode: str,
        broker_ip: str,
        broker_port: int,
        node_descriptor: Dict,
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
        # while not self.vehicle.is_armable:
        #    time.sleep(1)
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


class DronekitSitlDrone(DronekitDrone):
    """
    To use this class, you must override handle_start, handle_armed, handle_message and handle_stop.
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
            return cls(
                sitl,
                vehicle_mode,
                broker_ip,
                broker_port,
                node_descriptor,
            )

    def __init__(
        self,
        sitl: SITL,
        vehicle_mode: str,
        broker_ip: str,
        broker_port: int,
        node_descriptor: Dict,
    ):
        self.sitl = sitl
        super().__init__(
            self.sitl.connection_string,
            vehicle_mode,
            broker_ip,
            broker_port,
            node_descriptor,
        )