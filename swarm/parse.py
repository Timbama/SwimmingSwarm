import argparse


parser = argparse.ArgumentParser(description='Get height for pixy controller')
parser.add_argument('--height',required=True)
parser.add_argument('--units', required=True)
args = parser.parse_args()
h = int(args.height)
GRID_UNIT = args.units
print("%s, %s" % (h, GRID_UNIT))