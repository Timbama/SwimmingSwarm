import sys, random
import pygame
import pymunk
import math

random.seed(1)  # make the simulation the same each time, easier to debug
import pymunk.pygame_util

# def add_ball(space):


def main():
    pygame.init()
    screen = pygame.display.set_mode((600, 600))
    pygame.display.set_caption("Simple single bot simulation")
    clock = pygame.time.Clock()

    space = pymunk.Space()

    add_border(space, screen.get_size())
    robot = add_robot(space, (300, 300), 0)

    draw_options = pymunk.pygame_util.DrawOptions(screen)

    ticks_to_next_pulse = 10
    pulse_left_motor(robot)
    pulse_right_motor(robot)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                sys.exit(0)

        ticks_to_next_pulse -= 1
        if ticks_to_next_pulse <= 0:
            ticks_to_next_pulse = 25
            if random.random() < 0.5:
                pulse_left_motor(robot)
            if random.random() < 0.5:
                pulse_right_motor(robot)

        space.step(1 / 50.0)

        screen.fill((255, 255, 255))
        space.debug_draw(draw_options)

        pygame.display.flip()
        clock.tick(50)


def linear_drag_callback(body: pymunk.Body, gravity, damping, dt):
    pymunk.Body.update_velocity(body, gravity, damping, dt)
    b = 0.5  # drag constant
    F = b * body.velocity
    a = F / body.mass
    body.velocity -= a * dt


def add_border(space, size):
    width, height = size
    borders = [
        pymunk.Segment(space.static_body, (0, 0), (width, 0), 0),
        pymunk.Segment(space.static_body, (width, 0), size, 0),
        pymunk.Segment(space.static_body, size, (0, height), 0),
        pymunk.Segment(space.static_body, (0, height), (0, 0), 0),
    ]
    for b in borders:
        b.friction = 1
    space.add(*borders)


def add_robot(space, position, rotation=0):
    body_mass = 3
    radius = 25
    motor_mass = 1

    robot = pymunk.Body()  # 1
    robot.position = position  # 2
    robot.angle = rotation
    robot.velocity_func = linear_drag_callback

    body = pymunk.Circle(robot, radius)  # 3
    body.mass = body_mass  # 4
    body.friction = 1

    motor_length = 1.5 * radius

    left_motor = pymunk.Segment(robot, (-radius, 0), (-motor_length, 0), radius / 2)
    left_motor.mass = motor_mass
    left_motor.friction = 1

    right_motor = pymunk.Segment(robot, (radius, 0), (motor_length, 0), radius / 2)
    right_motor.mass = motor_mass
    right_motor.friction = 1

    # space.add(robot, body)  # 5
    space.add(robot, body, left_motor, right_motor)
    return robot


def pulse_left_motor(robot: pymunk.Body):
    radius = 25
    motor_position = 1.25 * radius
    force = (0, 1000)
    robot.apply_force_at_local_point(force, (-motor_position, 0))


def pulse_right_motor(robot: pymunk.Body):
    radius = 25
    motor_position = 1.25 * radius
    force = (0, 1000)
    robot.apply_force_at_local_point(force, (motor_position, 0))


if __name__ == "__main__":
    main()