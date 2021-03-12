import random
import json
import logging
import sys
from argparse import ArgumentParser
from typing import Tuple

import pymunk
import pygame
from swarm.drone import simulation

logging.basicConfig(level=logging.INFO)


class SingleSimulatedDrone(simulation.SimulatedDrone):
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
                space, position, rotation, broker_ip, broker_port, node_descriptor
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
            if pitch > 1490:
                self.pulse_left_motor()
                self.pulse_right_motor()
            elif yaw < 1490:
                self.pulse_left_motor()
            elif yaw > 1490:
                self.pulse_right_motor()
        else:
            logging.info("Stopping...")
            self.stop()
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
    drone = SingleSimulatedDrone.from_config(space, (300, 300), 0, args.config)

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

        drone.step()

        space.step(1 / 50.0)

        screen.fill((255, 255, 255))
        space.debug_draw(draw_options)

        pygame.display.flip()
        clock.tick(50)


if __name__ == "__main__":
    main()
