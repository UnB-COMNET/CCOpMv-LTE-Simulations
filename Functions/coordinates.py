class Coordinate:
    def __init__(self, x, y, z = 0):
        self.x = x
        self.y = y
        self.z = z
    
    def setCoordinate(self, x, y, z = 0):
        self.x = x
        self.y = y
        self.z = z

class PolarCoordinate:
    def __init__(self, r, phi):
        self.r = r
        self.phi = phi
    
    def setCoordinate(self, r, phi):
        self.r = r
        self.phi = phi