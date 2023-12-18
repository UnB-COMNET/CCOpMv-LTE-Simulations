class Coordinate:
    """ Define a structure for coordinates (x,y,z)"""
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

    def __add__(self, other):
        return Coordinate(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        return Coordinate(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, other):
        if isinstance(other, int) or isinstance(other,float):
            return Coordinate(self.x * other, self.y * other, self.z * other)

    def __rmul__(self, other):
        if isinstance(other, int) or isinstance(other,float):
            return Coordinate(self.x * other, self.y * other, self.z * other)

    def __abs__(self):
        return Coordinate(abs(self.x), abs(self.y), abs(self.z))

class PolarCoordinate:
    """
    Define a structure for polar coordinates (r, phi).
    """
    def __init__(self, r, phi):
        self.r = r
        self.phi = phi
    
    def setCoordinate(self, r, phi):
        self.r = r
        self.phi = phi