import json
import logging
import math
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
        dt: float,
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
                broker_ip, broker_port, node_descriptor, space, position, rotation, dt
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
        wait = 0
        if state["alive"]:
            if "waypoint" in state:
                waypoint = state["waypoint"]
                logging.info("New waypoint %s", waypoint)
                wait = self.go_to_waypoint(waypoint)
        else:
            logging.info("Stopping...")
            self.stop()
        state = {
            "alive": True,
            "position": self.get_position(),
            "orientation": self.get_orientation(),
            "wait": wait,
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
        dt: float,
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
                broker_ip, broker_port, node_descriptor, space, position, rotation, dt
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
    parser.add_argument(
        "--mode", type=str, choices=["auto", "manual"], default="manual"
    )
    args = parser.parse_args()
    pygame.init()

    screen = pygame.display.set_mode((600, 600))
    clock = pygame.time.Clock()
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    logging.info("Simulation initialized")

    space = simulation.initialize_space((600, 600))
    fps = 50
    dt = 1.0 / fps
    drone = None
    if args.mode == "manual":
        pygame.display.set_caption("Manual bot simulation")
        drone = ManualSimulatedDrone.from_config(space, (300, 300), 0, args.config, dt)
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

            drone.step(dt)
            space.step(dt)

            screen.fill((255, 255, 255))
            space.debug_draw(draw_options)

            pygame.display.flip()
            clock.tick(fps)

    elif args.mode == "auto":
        pygame.display.set_caption("Auto bot simulation")
        drone1 = AutoSimulatedDrone.from_config(space, (300, 200), 0, args.config, dt)
        drone2 = AutoSimulatedDrone.from_config(
            space, (300, 400), -math.pi, args.config, dt
        )

        state = {"alive": True}
        # Send the initial condition
        drone1.publish_all(json.dumps(state, separators=(",", ":")))
        drone2.publish_all(json.dumps(state, separators=(",", ":")))
        drone1.start()
        drone2.start()

        drone1.go_to_waypoint((500, 300))
        drone2.go_to_waypoint((100, 300))
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                ):
                    state = {"alive": False}
                    drone1.publish_all(json.dumps(state, separators=(",", ":")))
                    drone2.publish_all(json.dumps(state, separators=(",", ":")))
                    drone1.stop()
                    drone2.stop()
                    sys.exit(0)
                    return

            drone1.step(dt)
            drone2.step(dt)
            space.step(dt)

            screen.fill((255, 255, 255))
            space.debug_draw(draw_options)

            pygame.display.flip()
            clock.tick(fps)


if __name__ == "__main__":
    main()
