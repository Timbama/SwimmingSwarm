import json
from typing import Dict

from dronekit_sitl import SITL

# pylint: disable=import-error
from swarm.drone.ardusub import DronekitDrone


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
                broker_ip,
                broker_port,
                node_descriptor,
                sitl,
                vehicle_mode,
            )

    def __init__(
        self,
        broker_ip: str,
        broker_port: int,
        node_descriptor: Dict,
        sitl: SITL,
        vehicle_mode: str,
    ):
        self.sitl = sitl
        super().__init__(
            self.sitl.connection_string,
            vehicle_mode,
            broker_ip,
            broker_port,
            node_descriptor,
        )