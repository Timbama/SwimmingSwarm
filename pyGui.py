import pygame
import math

pygame.font.init()
pygame.init()

# Define some colors
BLACK     = (   0,   0,   0)
WHITE     = ( 255, 255, 255)
OFFWHITE  = ( 235, 235, 235)
GREEN     = (   0, 255,   0)
RED       = ( 255,   0,   0)
BLUE      = (   0,   0, 255)
CYAN      = (   0, 255, 255)
GREY      = ( 192, 192, 192)
DARK_GREY = ( 140, 140, 140)

SCRN_WIDTH  = 800
SCRN_HEIGHT = 600

TABS = [
    'Manual',
    'Guided'
]

robo_img = pygame.image.load('Documentation/Images/robo_small.png')

class Gui:
    def __init__(self, hasJoystick=True):
        # Initialize pygame and draw window
        pygame.font.init()
        pygame.init()
        size = (SCRN_WIDTH, SCRN_HEIGHT)
        pygame.display.set_caption('Roboquarium Controller')
        self.screen = pygame.display.set_mode(size)
        self.hasJoystick = hasJoystick

        # Set up state
        self.tabState = TABS[0]
        self.bots = [
            ['bot_id', 'location'],
            ['bot_id', 'location']
        ]

        # Used to manage how fast the screen updates
        self.clock = pygame.time.Clock()

        # Initialize joysticks
        if (self.hasJoystick):
            pygame.joystick.init()
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()

    def draw_joystick(self, x, y, xv, yv):
        #Draws the Circular Joystick value indicator
        radius = 100
        pygame.draw.circle(self.screen, DARK_GREY, (x, y), radius+2)
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
        pygame.draw.rect(self.screen, DARK_GREY, [x-2, y-2, 24, (2*height)+4])
        pygame.draw.rect(self.screen, OFFWHITE, [x, y, 20, 2*height])
        ty = int(height*value)
        pygame.draw.rect(self.screen, color, [x, y + height, 20, ty])
    
    def draw_hbar(self, x, y, value, color):
        #Draws a horizontal indicator
        width = 200
        pygame.draw.rect(self.screen, DARK_GREY, [x-2, y-2, (2*width)+4, 24])
        pygame.draw.rect(self.screen, OFFWHITE, [x, y, 2*width, 20])
        tx = int(width*value)
        pygame.draw.rect(self.screen, color, [x + width, y, tx, 20])

    def draw_labels(self):
        myfont = pygame.font.SysFont('Arial', 30)
        self.screen.blit(myfont.render('Throttle', True, BLACK),(75,110))
        self.screen.blit(myfont.render('Yaw', True, BLACK),(380,480))
        self.screen.blit(myfont.render('Pitch', True, BLACK),(665,110))
        self.screen.blit(myfont.render('Roll', True, BLACK),(380,30))
        
    def draw_bot_list(self):
        font = pygame.font.SysFont('Arial', 16)
        pygame.draw.rect(self.screen, DARK_GREY, [98, 98, 604, 384])
        pygame.draw.rect(self.screen, WHITE, [100, 100, 600, 380])
        self.screen.blit(font.render('Bot ID | Current Location', True, BLACK), (105, 80))
        for x in range(len(self.bots)):
            self.screen.blit(font.render(self.bots[x][0], True, BLACK), (105, 105 + (x*20)))

    def draw_menubar(self):
        menuFont = pygame.font.SysFont('Arial', 12)
        pygame.draw.rect(self.screen, DARK_GREY, [0, 0, SCRN_WIDTH, 22])
        manual_color = GREY
        guided_color = GREY
        if self.tabState == TABS[1]:
            guided_color = GREEN
        else:
            manual_color = GREEN
        self.button('Manual', 2, 2, 60, 18, manual_color, DARK_GREY, menuFont, self.toggle_tab_state, 0)
        self.button('Guided', 64, 2, 60, 18, guided_color, DARK_GREY, menuFont, self.toggle_tab_state, 1)
        self.button('Quit', 738, 2, 60, 18, GREY, DARK_GREY, menuFont, self.stop)

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
    
    def button(self, msg, x, y, w, h, ic, ac, font, action=None, *args): # ic: inactive color, ac: active color
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()

        if x+w > mouse[0] > x and y+h > mouse[1] > y:
            pygame.draw.rect(self.screen, ac,(x,y,w,h))
            if click[0] == 1 and action != None:
                action(*args)
        else:
            pygame.draw.rect(self.screen, ic,(x,y,w,h))

        textSurf, textRect = text_objects(msg, font)
        textRect.center = ( (x+(w/2)), (y+(h/2)) )
        self.screen.blit(textSurf, textRect)

    def render(self):
        pygame.event.wait()
        self.screen.fill(GREY)
        self.draw_menubar()

        if self.tabState == TABS[1]:
            self.draw_bot_list()
        else:
            if self.hasJoystick:
                (pitch, roll, yaw, throttle) = self.get_joystick_axis()
            else:
                (pitch, roll, yaw, throttle) = self.get_keyboard_command()
            self.screen.blit(robo_img, (304, 110))
            self.draw_joystick(293, 320, yaw, throttle)
            self.draw_joystick(513, 320, roll, pitch)
            self.draw_vbar(108, 150, throttle, GREEN)
            self.draw_vbar(688, 150, pitch, RED)
            self.draw_hbar(208, 530, yaw, BLUE)
            self.draw_hbar(208, 70, roll, CYAN)
            self.draw_labels()

        pygame.display.flip()

        self.clock.tick(60)
    
    def toggle_tab_state(self, idx):
        self.tabState = TABS[idx]
    
    def has_quit(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True

    def stop(self):
        pygame.quit()

    def get_selected_bot():
        #todo, need this to return a number ranging from 0 to n - 1 where n is the number of bots; the number represents the current bot selected
        return 0

def text_objects(text, font):
    textSurface = font.render(text, True, BLACK)
    return textSurface, textSurface.get_rect()