import math

class MockGPS:
    def __init__(self, lat: float, lon: float):
        self.lat = lat
        self.lon = lon
        self.target_lat = lat
        self.target_lon = lon
    
    def get_coord(self):
        return (self.lat, self.lon)
    
    def set_coord(self, lat: float, lon: float):
        self.lat = lat
        self.lon = lon
    
    def move(self, target_lat: float, target_lon: float):
        self.target_lat = target_lat
        self.target_lon = target_lon
    
    def step(self, magnitude: float):
        delta_lat = self.target_lat - self.lat
        if magnitude < math.fabs(delta_lat):
            self.lat += math.copysign(magnitude, self.target_lat - self.lat)
        else:
            self.lat = self.target_lat
        delta_lon = self.target_lon - self.lon
        if magnitude < math.fabs(delta_lon):
            self.lon += math.copysign(magnitude, self.target_lon - self.lon)
        else:
            self.lon = self.target_lon
    
    def encoded_coord(self):
        return (int(self.lat * (10**7)), int(self.lon * (10**7)))
