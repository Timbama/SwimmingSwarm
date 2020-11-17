import pixy
import sys
from ctypes import *
from pixy import *
import math
import argparse

COLOR_CODES = {
    "bot0": (1, 2),
    "bot1": (2, 3),
    "bot2": (3, 4),
    "bot3": (1, 4),
    "bot4": (2, 5)
}

class Blocks (Structure):
    _fields_ = [
        ("m_signature", c_uint),
        ("m_x", c_uint),
        ("m_y", c_uint),
        ("m_width", c_uint),
        ("m_height", c_uint),
        ("m_angle", c_uint),
        ("m_index", c_uint),
        ("m_age", c_uint)]


class PixyController:
    def __init__(self):
        if pixy.init() != 0:
            print("Error initializing pixy2")
            sys.exit(0)
        self.bots = BlockArray(10)

    # Returns a tuple (width, height)
    def get_frame_dimensions_pixels(self):
        return (pixy.get_frame_width(), pixy.get_frame_height())

    # returns an array of up to 10 detected bots and the number of bots
    # via a tuple (bots, count)
    def get_all_bot_positions(self):
        pixy.change_prog("color_connected_components")
        count = pixy.ccc_get_blocks(10, self.bots)
        return (self.bots, count)

    # returns a specific bot by its color code signature, if found,
    # else None
    def get_bot_position(self, signature):
        self.get_all_bot_positions()
        for bot in self.bots:
            if bot.m_signature == signature:
                return bot
        else:
            return None

    def get_frame_dimensions_units(self, h):
        #width
        width_angle_radians = 60 * math.pi / 180
        width = 2 * h / math.tan(width_angle_radians)
        #height
        height_angle_radians = 70 * math.pi / 180
        height = 2 * h / math.tan(height_angle_radians)
        return (width, height)

    def get_pixel_size(self, h):
        pixels = self.get_frame_dimensions_pixels()
        units = self.get_frame_dimensions_units(h)
        #pixel width in real units
        pixel_width = units[0]/pixels[0] #real units per pixel
        #pixel height in real units
        pixel_height = units[1]/pixels[1] #real units per pixel
        return (pixel_width, pixel_height)


    def identify_bot(self, signature_int):
        signature = str(oct(signature_int))
        for i in COLOR_CODES:
            color_code_values = COLOR_CODES[i]
            if (str(color_code_values[0]) in signature and str(color_code_values[1]) in signature):
                return i
        return None


if(__name__ == "__main__"):

    #set up arg parser to get height
    parser = argparse.ArgumentParser(description='Get height for pixy controller')
    parser.add_argument('--height',required=True)
    parser.add_argument('--units', required=True)
    args = parser.parse_args()
    h = float(args.height)
    GRID_UNIT = args.units

    #initilialize pixy
    pixyController = PixyController()

    pixels = pixyController.get_frame_dimensions_pixels()
    units = pixyController.get_frame_dimensions_units(h)
    print("The grid is %s %ss wide and %s %ss tall" %(units[0], GRID_UNIT, units[1], GRID_UNIT))
    pixel_size = pixyController.get_pixel_size(h)
    print("Each pixel is %s %ss wide and %s %ss tall" %(pixel_size[0], GRID_UNIT pixel_size[1], GRID_UNIT))

    while 1:
        (bots, count) = pixyController.get_all_bot_positions()

        if count > 0:
            print('%d bots found' % count)
            for idx in range(0, count):
                #print('[BLOCK: SIG=%o X=%3d Y=%3d WIDTH=%3d HEIGHT=%3d]' % (bots[idx].m_signature, bots[idx].m_x, bots[idx].m_y, bots[idx].m_width, bots[idx].m_height))

                #position in pixels
                bot_x = bots[idx].m_x
                bot_y = bots[idx].m_y

                #bot width and height
                bot_width = bots[idx].m_width
                bot_height = bots[idx].m_height

                #size of pixy grid in pixels and then in the units the height were given
                pixels = pixyController.get_frame_dimensions_pixels()
                units = pixyController.get_frame_dimensions_units(h)

                #get height and width of each unit
                pixel_width = units[0] / pixels[0]
                pixel_height = units[1] / pixels[1]

                #convert pixels into units
                dist_x = bot_x * pixel_width
                dist_y = bot_y * pixel_height

                bot_id = pixyController.identify_bot(bots[idx].m_signature)
                if bot_id is not None:
                    print("Unidentified bot at (%s, %s) pixels from the origin" % (bot_x, bot_y))
                else:
                    print("%s is (%s, %s) pixels from the origin" % (bot_id, bot_x, bot_y))
                    #print("%s is (%s, %s) %ss from the origin" % (bot_id, dist_x, dist_y, GRID_UNIT))