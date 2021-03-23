import math
from typing import Dict, Tuple

import pymunk
import pymunk.pygame_util

# pylint: disable=import-error
from swarm import VizierAgent


def initialize_space(size=(600, 600)):
    space = pymunk.Space()
    # Add borders
    width, height = size
    borders = [
        pymunk.Segment(space.static_body, (0, 0), (width, 0), 0),
        pymunk.Segment(space.static_body, (width, 0), size, 0),
        pymunk.Segment(space.static_body, size, (0, height), 0),
        pymunk.Segment(space.static_body, (0, height), (0, 0), 0),
    ]
    for b in borders:
        b.friction = 1  #   Asumme no surface friction
    space.add(*borders)
    return space


class SimulatedDrone(VizierAgent):
    def __init__(
        self,
        broker_ip: str,
        broker_port: int,
        node_descriptor: Dict,
        space: pymunk.Space,
        position: Tuple[float, float],
        rotation: float,
    ):
        super().__init__(broker_ip, broker_port, node_descriptor)
        self.body_drag_coefficient = 0.47  # drag coefficient of a sphere
        self.body_mass = 2.8  # kg
        self.body_radius = 8.75  # cm
        self.side_motor_mass = 0.1  # kg
        self.side_motor_width = 7  # cm
        self.side_motor_length = 5  # cm

        self.space = space
        self.vehicle = self.add_to_space(position, rotation)

        self.side_motor_position = self.body_radius + self.side_motor_width / 2
        self.max_motor_force = 10
        self.motor_force = (0, 0)

        self.clock = 0

    def step(self, dt):
        # Newly received commands have higher priority
        super().step()
        left_force_N, right_force_N = self.motor_force
        self.vehicle.apply_force_at_local_point(
            (left_force_N, 0), (0, self.side_motor_position)
        )
        self.vehicle.apply_force_at_local_point(
            (right_force_N, 0), (0, -self.side_motor_position)
        )
        self.clock += dt

    def get_position(self):
        return (self.vehicle.position.x, self.vehicle.position.y)

    def get_orientation(self):
        return self.vehicle.angle % (2 * math.pi)

    def add_to_space(self, position: Tuple[float, float], rotation: float):
        vehicle = pymunk.Body()  # 1
        vehicle.position = position  # 2
        vehicle.angle = rotation
        vehicle.velocity_func = self.drag_callback

        body = pymunk.Circle(vehicle, self.body_radius)  # 3
        body.mass = self.body_mass  # 4
        body.friction = 1  # Asumme no surface friction

        left_motor = pymunk.Poly(
            vehicle,
            [
                (self.side_motor_length / 2, self.side_motor_width / 2),
                (-self.side_motor_length / 2, self.side_motor_width / 2),
                (-self.side_motor_length / 2, -self.side_motor_width / 2),
                (self.side_motor_length / 2, -self.side_motor_width / 2),
            ],
            transform=pymunk.Transform(
                ty=self.body_radius + self.side_motor_length / 2
            ),
            radius=0.001,
        )
        left_motor.mass = self.side_motor_mass
        left_motor.friction = 1
        right_motor = pymunk.Poly(
            vehicle,
            [
                (self.side_motor_length / 2, self.side_motor_width / 2),
                (-self.side_motor_length / 2, self.side_motor_width / 2),
                (-self.side_motor_length / 2, -self.side_motor_width / 2),
                (self.side_motor_length / 2, -self.side_motor_width / 2),
            ],
            transform=pymunk.Transform(
                ty=-self.body_radius - self.side_motor_length / 2
            ),
            radius=0.001,
        )
        right_motor.mass = self.side_motor_mass
        right_motor.friction = 1

        self.space.add(vehicle, body, left_motor, right_motor)
        return vehicle

    def body_drag(self, body: pymunk.Body):
        # General drag equations
        radius = self.body_radius / 100  # m
        velocity = body.velocity / 100  # m
        water_density = 1
        constant = (
            water_density * self.body_drag_coefficient * (radius * radius * math.pi) / 2
        )
        x_force = constant * velocity[0] * velocity[0]  # N
        y_force = constant * velocity[1] * velocity[1]  # N
        return pymunk.Vec2d(x_force, y_force)

    def drag_callback(
        self, body: pymunk.Body, gravity: Tuple[float, float], damping: float, dt: float
    ):
        pymunk.Body.update_velocity(body, gravity, damping, dt)
        # F = ma
        acceleration = self.body_drag(body) / body.mass  # m/s^2
        acceleration *= 100  # cm/s^2
        body.velocity -= acceleration * dt

    def set_velocity(self, velocity_m_s: Tuple[float, float]):
        pass

    def set_angular_velocity(self, velocity_rad_s: Tuple[float, float]):
        pass

    def set_linear_velocity(self, velocity_m_s: float):
        pass

    def set_motor_force(self, left_force_N: float, right_force_N: float):
        self.motor_force = (left_force_N, right_force_N)
