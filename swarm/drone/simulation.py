import math
from typing import Dict, Tuple, List

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
        time_tolerance: float,
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

        self.force_queue = []
        self.clock = 0
        self.time_tolerance = time_tolerance

    def step(self, dt):
        if len(self.force_queue) > 0:
            time, forces = self.force_queue[0]
            if abs(self.clock - time) <= self.time_tolerance or self.clock > time:
                self.force_queue = self.force_queue[1:]
                left, right = forces
                self.set_motor_force(left, right)

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

    def get_velocity_angle(self):
        return math.atan2(self.vehicle.velocity[1], self.vehicle.velocity[0])

    def get_linear_velocity(self):
        return math.sqrt(self.vehicle.velocity[0] ** 2 + self.vehicle.velocity[1] ** 2)

    def kill_movement(self, wait: float = 0, chain=False):
        wait += self.set_angular_velocity(0, wait, chain=True)
        if self.get_linear_velocity() > 0:
            wait += self.turn_to_orientation(
                self.get_velocity_angle(), wait, chain=True
            )
        wait += self.set_linear_velocity(0, wait, chain)
        return wait

    def go_to_waypoint(self, target_position: Tuple[float, float], wait: float = 0):
        # wait += self.kill_movement(wait, chain=True)
        position = self.get_position()
        diff_x = target_position[0] - position[0]
        diff_y = target_position[1] - position[1]
        target_orientation = math.atan2(diff_y, diff_x)
        distance = math.sqrt(diff_x ** 2 + diff_y ** 2)
        wait += self.turn_to_orientation(target_orientation, wait, chain=True)
        wait += self.move_linearly(distance, wait)
        return wait

    def set_linear_velocity(
        self, target_linear_velocity: float, wait: float = 0, chain: bool = False
    ):
        diff_linear_velocity = target_linear_velocity - self.get_linear_velocity()
        if diff_linear_velocity != 0:
            wait_time = (
                abs(diff_linear_velocity)
                * self.vehicle.mass
                / (2 * self.max_motor_force)
            )
            achievable_time = (
                wait_time - wait_time % self.time_tolerance + self.time_tolerance
            )
            force = diff_linear_velocity * self.vehicle.mass / achievable_time
            if wait == 0:
                self.set_motor_force(force, force)
            else:
                self.force_queue += [
                    (
                        self.clock + wait,
                        (force, force),
                    )
                ]
            if not chain:
                self.force_queue += [
                    (
                        self.clock + wait + achievable_time,
                        (0, 0),
                    )
                ]
            print("linear", achievable_time)
            wait += achievable_time
        return wait

    def set_angular_velocity(
        self, target_angular_velocity: float, wait: float = 0, chain: bool = False
    ):
        diff_angular_velocity = target_angular_velocity - self.vehicle.angular_velocity
        if diff_angular_velocity != 0:
            wait_time = abs(
                diff_angular_velocity
            ) / self.calculate_angular_acceleration(self.max_motor_force)
            achievable_time = (
                wait_time - wait_time % self.time_tolerance + self.time_tolerance
            )
            force = (
                diff_angular_velocity
                * self.vehicle.moment
                / (2 * achievable_time * self.side_motor_position)
            )
            if wait == 0:
                self.set_motor_force(-force, force)
            else:
                self.force_queue += [
                    (
                        self.clock + wait,
                        (-force, force),
                    )
                ]

            if not chain:
                self.force_queue += [
                    (
                        self.clock + wait + achievable_time,
                        (0, 0),
                    )
                ]
            print("angular", achievable_time)
            wait += achievable_time
        return wait

    def move_linearly(self, distance: float, wait: float = 0, chain: bool = False):
        if distance != 0:
            thrust_time = self.calculate_thrust_time(distance, self.max_motor_force)
            achievable_time = 2 * (
                (thrust_time / 2)
                - (thrust_time / 2) % self.time_tolerance
                + self.time_tolerance
            )
            force = self.calculate_thrust_force(distance, achievable_time)
            if wait == 0:
                self.set_motor_force(force, force)
            else:
                self.force_queue += [(self.clock + wait, (force, force))]
            self.force_queue += [
                (
                    self.clock + wait + achievable_time / 2,
                    (-force, -force),
                )
            ]
            if not chain:
                self.force_queue += [
                    (self.clock + wait + achievable_time, (0, 0)),
                ]
            wait += achievable_time
            print("move", wait)
        return wait

    def turn_to_orientation(
        self, target_orientation: float, wait: float = 0, chain: bool = False
    ):
        turn_angle = target_orientation - self.get_orientation()
        if turn_angle != 0:
            turn_time = self.calculate_turn_time(turn_angle, self.max_motor_force)
            achievable_time = 2 * (
                (turn_time / 2)
                - (turn_time / 2) % self.time_tolerance
                + self.time_tolerance
            )
            force = self.calculate_turn_force(turn_angle, achievable_time)
            if wait == 0:
                self.set_motor_force(force, -force)
            else:
                self.force_queue += [(self.clock + wait, (force, -force))]
            self.force_queue += [
                (
                    self.clock + wait + achievable_time / 2,
                    (-force, force),
                )
            ]
            if not chain:
                self.force_queue += [
                    (self.clock + wait + achievable_time, (0, 0)),
                ]
            wait += achievable_time
            print("turn", achievable_time)
        return wait

    def calculate_turn_force(self, turn_angle: float, turn_time: float):
        return (
            4
            * turn_angle
            * self.vehicle.moment
            / (self.side_motor_position * turn_time ** 2)
        )

    def calculate_thrust_force(self, distance: float, thrust_time: float):
        return 4 * distance * self.vehicle.mass / thrust_time ** 2

    def calculate_angular_acceleration(self, force_N: float):
        torque = 2 * force_N * self.side_motor_position
        angular_acc = torque / self.vehicle.moment
        return angular_acc

    def calculate_turn_time(self, turn_angle: float, force_N: float):
        turn_time = 2 * math.sqrt(
            abs(turn_angle) / self.calculate_angular_acceleration(force_N)
        )
        return turn_time

    def calculate_thrust_time(self, distance: float, force_N: float):
        acceleration = 2 * force_N / self.vehicle.mass
        thrust_time = 2 * math.sqrt(abs(distance) / acceleration)
        return thrust_time

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

    def set_motor_force(self, left_force_N: float, right_force_N: float):
        if left_force_N > 0:
            left_force_N = min(left_force_N, self.max_motor_force)
        elif left_force_N < 0:
            left_force_N = max(left_force_N, -self.max_motor_force)
        if right_force_N > 0:
            right_force_N = min(right_force_N, self.max_motor_force)
        elif right_force_N < 0:
            right_force_N = max(right_force_N, -self.max_motor_force)
        self.motor_force = (left_force_N, right_force_N)
