# This file runs the Joystick GUI without connecting to the robot

import pyGui

gui = pyGui.Gui(hasJoystick=False)

while True:
    gui.render()

pyGui.quit()