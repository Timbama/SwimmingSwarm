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

if(__name__ == "__main__"):
    print("Pixy2 Controller Test")
    if pixy.init() != 0:
        print("Error initializing pixy2")
        sys.exit(0)

    print(pixy.get_frame_width())
    print(pixy.get_frame_height())

    pixy.change_prog("color_connected_components")
    bots = BlockArray(10)

    while 1:
        count = pixy.ccc_get_blocks(10, bots)

        if count > 0:
            print('%d bots found' % count)
            for idx in range(0, count):
                print('[BLOCK: SIG=%d X=%3d Y=%3d WIDTH=%3d HEIGHT=%3d]' % (bots[idx].m_signature,
                                                                            bots[idx].m_x, bots[idx].m_y, bots[idx].m_width, bots[idx].m_height))
