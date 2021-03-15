import json
import logging
import sys
from argparse import ArgumentParser
from typing import Tuple

import pymunk
import pygame
from swarm.drone import simulation

# logging.basicConfig(level=logging.INFO)


class AutoSimulatedDrone(simulation.SimulatedDrone):
    @classmethod
    def from_config(
        cls,
        space: pymunk.Space,
        position: Tuple[float, float],
        rotation: float,
        path: str,
    ):
        """
        Create new Drone from a configuration file.
        """
        with open(path, "r") as file:
            configuration = json.load(file)
            broker_ip = configuration["broker"]["ip"]
            broker_port = configuration["broker"]["port"]
            node_descriptor = configuration["node"]
            drone = cls(
                broker_ip,
                broker_port,
                node_descriptor,
                space,
                position,
                rotation,
            )
            return drone

    def handle_message(self, link: str, msg: str):
        """
        Execute MQTT message
        """
        if msg == "":
            return

        logging.info("Received %s message from: %s", msg, link)
        state = json.loads(msg.decode())
        if state["alive"]:
            if "command" in state:
                command = state["command"]
                logging.info("New command %s", command)
                linear_velocity = command["velocity"]["linear"]
                angular_velocity = command["velocity"]["angular"]
                self.set_motor_force(left_force, right_force)
        else:
            logging.info("Stopping...")
            self.stop()
        state = {
            "alive": True,
            "position": self.get_position(),
            "orientation": self.get_orientation(),
        }
        self.publish_all(json.dumps(state, separators=(",", ":")))
        logging.info("Published to %s message: %s", link, state)


class ManualSimulatedDrone(simulation.SimulatedDrone):
    @classmethod
    def from_config(
        cls,
        space: pymunk.Space,
        position: Tuple[float, float],
        rotation: float,
        path: str,
    ):
        """
        Create new Drone from a configuration file.
        """
        with open(path, "r") as file:
            configuration = json.load(file)
            broker_ip = configuration["broker"]["ip"]
            broker_port = configuration["broker"]["port"]
            node_descriptor = configuration["node"]
            drone = cls(
                broker_ip,
                broker_port,
                node_descriptor,
                space,
                position,
                rotation,
            )
            return drone

    def handle_message(self, link: str, msg: str):
        """
        Execute MQTT message
        """
        if msg == "":
            return

        logging.info("Received %s message from: %s", msg, link)
        state = json.loads(msg.decode())
        if state["alive"]:
            command = state["command"]
            logging.info("New command %s", command)
            pitch = command[0]
            yaw = command[2]
            right_force = 0
            left_force = 0
            if pitch > 1490:
                right_force += 100
                left_force += 100
            elif pitch < 1490:
                right_force -= 100
                left_force -= 100
            if yaw < 1490:
                right_force -= 50
                left_force += 50
            elif yaw > 1490:
                right_force += 50
                left_force -= 50
            self.set_motor_force(left_force, right_force)
        else:
            logging.info("Stopping...")
            self.stop()
        state = {
            "alive": True,
            "position": self.get_position(),
            "orientation": self.get_orientation(),
        }
        self.publish_all(json.dumps(state, separators=(",", ":")))
        logging.info("Published to %s message: %s", link, state)


def main():
    # Parse Command Line Arguments
    parser = ArgumentParser()
    parser.add_argument("config", type=str, help="Config file")
    args = parser.parse_args()
    pygame.init()

    screen = pygame.display.set_mode((600, 600))
    pygame.display.set_caption("Single bot simulation")
    clock = pygame.time.Clock()
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    logging.info("Simulation initialized")

    space = simulation.initialize_space((600, 600))
    drone = ManualSimulatedDrone.from_config(space, (300, 300), 0, args.config)

    state = {"alive": True}
    # Send the initial condition
    drone.publish_all(json.dumps(state, separators=(",", ":")))
    drone.start()
    state = {"alive": True}
    # Send the initial condition
    drone.publish_all(json.dumps(state, separators=(",", ":")))
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                state = {"alive": False}
                drone.publish_all(json.dumps(state, separators=(",", ":")))
                drone.stop()
                sys.exit(0)
                return

        fps = 50
        dt = 1.0 / fps

        drone.step(dt)
        space.step(dt)

        screen.fill((255, 255, 255))
        space.debug_draw(draw_options)

        pygame.display.flip()
        clock.tick(fps)


if __name__ == "__main__":
    main()
