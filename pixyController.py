import pixy
import sys
from ctypes import *
from pixy import *
import math
import argparse

COLOR_CODES = {
    "2": "bot0",
    "3": "bot1",
    "4": "bot2",
    "5": "bot3"
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
        
    #map y values from 0 -> pixel_height to pixel_height -> 0; this is so that we have a grid that grows up instead of down with y values
    #this function takes in an x and y that are centered relative to t the bottom left and shifts
    #them to the middle of the grid. By default,
    #the pixy is centered in the top left and 
    def offset_values(self, x, y):
        pixels = self.get_frame_dimensions_pixels()
        half_width = pixels[0] / 2
        half_height = pixels[1] / 2
        return (x - half_width, y - half_height)

    #the x and y values must have an origin at the center of the grid with x growing from
    #left to right and y growing from the bottom up. use the map_y_value and offset_values functions
    #to translate the default pixycam coordinates this way
    def offset_by_bot_dimensions(self, x, y, bot_width, bot_height):
        bot_width_half = bot_width / 2
        bot_height_half = bot_height / 2
        return (x + bot_width_half, y - bot_height_half)

    def identify_bot(self, signature_int):
        signature = str(oct(signature_int))
        if (not ("1" in signature)):
            return -1
        else:
            if ("2" in signature):
                #should check that others aren't
                return COLOR_CODES["2"]
            elif ("3" in signature):
                return COLOR_CODES["3"]
            elif ("4" in signature):
                return COLOR_CODES["4"]
            elif ("5" in signature):
                return COLOR_CODES["5"]
            else:
                return -1



if(__name__ == "__main__"):
    print("Pixy2 Controller Test")
    pixyController = PixyController()

    #set up arg parser to get height
    parser = argparse.ArgumentParser(description='Get height for pixy controller')
    parser.add_argument('height')
    args = parser.parse_args()
    h = int(args.height)

    pixels = pixyController.get_frame_dimensions_pixels()
    units = pixyController.get_frame_dimensions_units(h)
    print("The grid is %s units wide and %s units tall" %(units[0], units[1]))
    pixel_size = pixyController.get_pixel_size(h)
    print("Each pixel is %s units wide and %s units tall" %(pixel_size[0], pixel_size[1]))

    #0,0 for pixy is the top left but we probably want it to be the middle
    #we also want y values to grow up, not down; we have to flip y values and then offset them
    #x values grow in the right direction; just need to offset them
    #thats what the offset_values and map_y_value functions are for
    #then we need to account for the fact that the pixy also gives us the top left coordinate
    #for each detected block

    while 1:
        (bots, count) = pixyController.get_all_bot_positions()

        if count > 0:
            print('%d bots found' % count)
            for idx in range(0, count):
                print('[BLOCK: SIG=%o X=%3d Y=%3d WIDTH=%3d HEIGHT=%3d]' % (bots[idx].m_signature,
                                                                            bots[idx].m_x, bots[idx].m_y, bots[idx].m_width, bots[idx].m_height))
                print(bots[idx].m_signature)
                bot_x = bots[idx].m_x
                bot_y = bots[idx].m_y
                bot_width = bots[idx].m_width
                bot_height = bots[idx].m_height
                pixels = pixyController.get_frame_dimensions_pixels()
                units = pixyController.get_frame_dimensions_units(h)
                #first flip y
                #flipped_y = pixyController.map_y_value(bot_y)
                #then offset x and y to go from bottom left being origin to middle being origin
                #origin_pair = pixyController.offset_values(bot_x, flipped_y)
                #then account for bot size
                #true_coords = pixyController.offset_by_bot_dimensions(origin_pair[0], origin_pair[1], bots[idx].m_width, bots[idx].m_height)
                #print('SIG=%d: True coords are %s, %s' % (bots[idx].m_signature, true_coords[0], true_coords[1]))
                pixel_width = units[0] / pixels[0]
                pixel_height = units[1] / pixels[1]
                dist_x = bot_x * pixel_width
                dist_y = bot_y * pixel_height
                bot_id = pixyController.identify_bot(bots[idx].m_signature)
                print("%s is (%s, %s) pixels from the origin" % (bot_id, bot_x, bot_y))
                print("%s is (%s, %s) units from the origin" % (bot_id, dist_x, dist_y))