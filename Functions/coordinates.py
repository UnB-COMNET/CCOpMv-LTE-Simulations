class Coordinate:
    def __init__(self, x, y, z = 0):
        self.x = x
        self.y = y
        self.z = z
    
    def setCoordinate(self, x, y, z = 0):
        self.x = x
        self.y = y
        self.z = z

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    def __str__(self):
        return (f'({self.x}, {self.y}, {self.z})')

class PolarCoordinate:
    def __init__(self, r, phi):
        self.r = r
        self.phi = phi
    
    def setCoordinate(self, r, phi):
        self.r = r
        self.phi = phi