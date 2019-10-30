import pygame
import math

pygame.font.init()
pygame.init()

# Define some colors
BLACK    = (   0,   0,   0)
WHITE    = ( 255, 255, 255)
OFFWHITE = ( 235, 235, 235)
GREEN    = (   0, 255,   0)
RED      = ( 255,   0,   0)
BLUE     = (   0,   0, 255)
CYAN     = (   0, 255, 255)
GREY     = ( 160, 160, 160)

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
            print(self.joystick)
            self.joystick.init()

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

    def draw_vbar(self, x, y, value, color):
        # Draws a vertical indicator
        height = 200
        pygame.draw.rect(self.screen, OFFWHITE, [x, y, 20, 2*height])
        ty = int(height*value)
        pygame.draw.rect(self.screen, color, [x, y + height, 20, ty])
    
    def draw_hbar(self, x, y, value, color):
        #Draws a horizontal indicator
        width = 200
        pygame.draw.rect(self.screen, OFFWHITE, [x, y, 2*width, 20])
        tx = int(width*value)
        pygame.draw.rect(self.screen, color, [x + width, y, tx, 20])

    def draw_labels(self):
        myfont = pygame.font.SysFont('Arial', 30)
        self.screen.blit(myfont.render('Throttle', False, (0, 0, 0)),(5,10))
        self.screen.blit(myfont.render('Yaw', False, (0, 0, 0)),(290,370))
        self.screen.blit(myfont.render('Pitch', False, (0, 0, 0)),(570,10))
        self.screen.blit(myfont.render('Roll', False, (0, 0, 0)),(290,10))
        
    def get_joystick_axis(self):
        if (self.hasJoystick):
            return (self.joystick.get_axis(3),
                    self.joystick.get_axis(2),
                    self.joystick.get_axis(0),
                    self.joystick.get_axis(1))
        else:
            return (0,0,0,0)
    
    def get_keyboard_command(self):
        '''
            Keyboard control inspired by Kerbal Space Program
                W-S: Pitch
                A-D: Yaw
                Q-R: Roll
                LShift-Control: Speed / Throttle
        '''
        commands = [0, 0, 0, 0]
        keys = pygame.key.get_pressed()  #checking pressed keys

        # Pitch
        if keys[pygame.K_s]:
            commands[0] = 1
        elif keys[pygame.K_w]:
            commands[0] = -1

        # Roll
        if keys[pygame.K_e]:
            commands[1] = 1
        elif keys[pygame.K_q]:
            commands[1] = -1

        # Yaw
        if keys[pygame.K_a]:
            commands[2] = 1
        elif keys[pygame.K_d]:
            commands[2] = -1

        # Speed
        if keys[pygame.K_LCTRL]:
            commands[3] = 1
        elif keys[pygame.K_LSHIFT]:
            commands[3] = -1

        return commands

    def render(self):
        pygame.event.wait()
        if self.hasJoystick:
            (pitch, roll, yaw, throttle) = self.get_joystick_axis()
        else:
            (pitch, roll, yaw, throttle) = self.get_keyboard_command()
        self.screen.fill(GREY)
        self.draw_joystick(215, 210, yaw, throttle)
        self.draw_joystick(425, 210, roll, pitch)
        self.draw_vbar(20, 40, throttle, GREEN)
        self.draw_vbar(600, 40, pitch, RED)
        self.draw_hbar(120, 400, yaw, BLUE)
        self.draw_hbar(120, 40, roll, CYAN)
        self.draw_labels()

        pygame.display.flip()

        self.clock.tick(60)
    
    def hasQuit(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True

    def stop(self):
        pygame.quit()