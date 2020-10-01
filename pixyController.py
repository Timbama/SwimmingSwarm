import pixy
import sys
from ctypes import *
from pixy import *


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
    def get_frame_dimensions(self):
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


if(__name__ == "__main__"):
    print("Pixy2 Controller Test")
    pixyController = PixyController()

    print(pixyController.get_frame_dimensions())

    while 1:
        (bots, count) = pixyController.get_all_bot_positions()

        if count > 0:
            print('%d bots found' % count)
            for idx in range(0, count):
                print('[BLOCK: SIG=%d X=%3d Y=%3d WIDTH=%3d HEIGHT=%3d]' % (bots[idx].m_signature,
                                                                            bots[idx].m_x, bots[idx].m_y, bots[idx].m_width, bots[idx].m_height))
