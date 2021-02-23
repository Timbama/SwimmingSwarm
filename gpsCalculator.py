from geographiclib.geodesic import Geodesic
import math

#theta is radians counter clockwise from due east (so basically angles on the unit circle)
#R must be in meters
#this formula uses plane geometry which should be fine becase we're using small distances but if it isn't we should switch to the haversine formula or use the geodesic direct algorithm
def new_coorindate(latitude, longitude, R, theta):

    dx = R*math.sin(theta)  #theta measured clockwise from due north
    dy = R*math.cos(theta)  #dx, dy same units as R


    delta_longitude = dx/(111320*cos(latitude)) #dx, dy in meters
    delta_latitude = dy/110540       

    return (latitude + delta_latitude, longitude + delta_longitude)


#this calculates a new lat/lon given the top left corner lat/lon and a distance down(dy) and to the right(dx) which are the values given by pixyController.get_bot_position_units
def new_coordinate_relative_origin(latitude, longitude, dx, dy):

    delta_longitude = dx/(111320*cos(latitude)) #dx, dy in meters
    delta_latitude = dy/110540

    # The lat value is subtracted because the origin is in the top and pixyCam coords grow downwards; longitude grows right so it is still added like normal
    return (latitude - delta_latitude, longitude + delta_longitude)
