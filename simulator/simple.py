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
    pygame.display.set_caption("Joints. Just wait and the L will tip over")
    clock = pygame.time.Clock()

    space = pymunk.Space()

    add_border(space, screen.get_size())
    add_robot(space, (250, 300), 0.5)
    add_robot(space, (350, 300), math.pi // 2)

    draw_options = pymunk.pygame_util.DrawOptions(screen)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                sys.exit(0)

        space.step(1 / 50.0)

        screen.fill((255, 255, 255))
        space.debug_draw(draw_options)

        pygame.display.flip()
        clock.tick(50)


def add_border(space, size):
    width, height = size
    borders = [
        pymunk.Segment(space.static_body, (0, 0), (width, 0), 0),
        pymunk.Segment(space.static_body, (width, 0), size, 0),
        pymunk.Segment(space.static_body, size, (0, height), 0),
        pymunk.Segment(space.static_body, (0, height), (0, 0), 0),
    ]
    space.add(*borders)


def add_robot(space, position, rotation=0):
    body_mass = 3
    radius = 25
    motor_mass = 1

    robot = pymunk.Body()  # 1
    robot.position = position  # 2
    robot.angle = rotation

    body = pymunk.Circle(robot, radius)  # 3
    body.mass = body_mass  # 4
    body.friction = 1

    motor_length = math.floor(1.5 * radius)

    left_motor = pymunk.Segment(robot, (-radius, 0), (-motor_length, 0), radius // 2)
    left_motor.mass = motor_mass
    left_motor.friction = 1

    right_motor = pymunk.Segment(robot, (radius, 0), (motor_length, 0), radius // 2)
    right_motor.mass = motor_mass
    right_motor.friction = 1

    # space.add(robot, body)  # 5
    space.add(robot, body, left_motor, right_motor)
    return robot


if __name__ == "__main__":
    main()