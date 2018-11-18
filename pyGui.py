import pygame
import math

# Define some colors
BLACK    = (   0,   0,   0)
WHITE    = ( 255, 255, 255)
OFFWHITE = ( 235, 235, 235)
GREEN    = (   0, 255,   0)
RED      = ( 255,   0,   0)
BLUE     = (   0,   0, 255)
GREY     = (   160, 160,  160)

class Gui:
    def __init__(self, hasJoystick=True):
        # Initialize pygame and draw window
        pygame.font.init()
        pygame.init()
        size = (640, 480)
        self.screen = pygame.display.set_mode(size)
        self.hasJoystick = hasJoystick

        # Used to manage how fast the screen updates
        self.clock = pygame.time.Clock()

        # Initialize joysticks
        if (self.hasJoystick):
            pygame.joystick.init()
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()

        # Not done yet
        self.done = False

    def draw_joystick(self, x, y, xv, yv):
        #Draws the Circular Joystick value indicator
        radius = 100
        pygame.draw.circle(self.screen, OFFWHITE, (x, y), radius)

        #Large amount of math to convert  the joystick input from a square looking map (where the top right is 1.0, 1.0)
        #to a circle where the top right is sqrt(2), sqrt(2)
        magnitude = radius * (xv**2 + yv**2)**.5
        angle = 0

        if xv == 0:
            if yv > 0:
                angle = math.radians(90)
            elif yv < 0:
                angle = math.radians(270)
            else:
                angle = 0
        else:
            angle = math.atan(yv/xv)
            
        if magnitude > radius:
            magnitude = radius

        if xv < 0:
            cx = int(x - magnitude*math.cos(angle))
            cy = int(y - magnitude*math.sin(angle))
        else:
            cx = int(x + magnitude*math.cos(angle))
            cy = int(y + magnitude*math.sin(angle))

        pygame.draw.circle(self.screen, RED, (cx, cy), 5)

    def draw_throttle(self, x, y, value, color):
        # Draws a vertical indicator
        height = 200
        pygame.draw.rect(self.screen, OFFWHITE, [x, y, 20, 2*height])
        ty = int(height*value)
        pygame.draw.rect(self.screen, color, [x, y + height, 20, ty])
    
    def draw_steering(self, x, y, value):
        #Draws a horizontal indicator
        width = 200
        pygame.draw.rect(self.screen, OFFWHITE, [x, y, 2*width, 20])
        tx = int(width*value)
        pygame.draw.rect(self.screen, BLUE, [x + width, y, tx, 20])

    def draw_labels(self):
        myfont = pygame.font.SysFont('Arial', 30)
        self.screen.blit(myfont.render('Throttle', False, (0, 0, 0)),(5,10))
        self.screen.blit(myfont.render('Yaw', False, (0, 0, 0)),(300,375))
        self.screen.blit(myfont.render('Depth', False, (0, 0, 0)),(570,10))
        
    def get_joystick_axis(self):
        if (self.hasJoystick):
            return (self.joystick.get_axis(0),
                    self.joystick.get_axis(1),
                    self.joystick.get_axis(2),
                    self.joystick.get_axis(3))
        else:
            return (0,0,0,0)

    def render(self):
        (yaw, throttle, depth_yaw, depth) = self.get_joystick_axis()

        self.screen.fill(GREY)
        self.draw_joystick(215, 210, yaw, throttle)
        self.draw_joystick(425, 210, depth_yaw, depth)
        self.draw_throttle(20, 40, throttle, GREEN)
        self.draw_throttle(600, 40, depth,RED)
        self.draw_steering(120, 400, yaw)
        self.draw_labels()

        pygame.display.flip()

        self.clock.tick(60)
    
    def start(self, callable = None):
        while not self.done:
            try:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        done = True

                # Calling function
                if (callable != None):
                    callable(self.stop)

                self.render()
            except KeyboardInterrupt:
                break
        pygame.quit()
    
    def stop(self):
        self.done = True