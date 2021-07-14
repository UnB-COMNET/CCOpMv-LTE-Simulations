from math import cos, pi
from math import sin

class Coordinate:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def setPosition(self, x, y):
        self.x = x
        self.y = y

class Smallcell:
    center = Coordinate
    radius = float

class Macrocell:
    def __init__(self, center):
        self.center = Coordinate(center.x, center.y)
        self.smallcells = [Smallcell]

    def test():
        None

class MapHexagonal:
    def __init__(self, center):
        self.d_macromacro = 1000
        self.d_macrocluster = 105
        self.d_macroue = 35
        self.d_smallsmall = 20
        self.dropradius_mc = 250
        self.dropradius_sc = 500
        self.dropradius_sc_cluster = 50
        self.dropradius_ue_cluster = 70

        self.n_site = 7
        self.n_cluster = 1
        self.n_antennas = 10
        self.n_ues = 60
        
        self.center = center
        self.macrocells = []     
        
    def placeMacrocells(self):
        # place macrocell center
        macrocell = Macrocell(self.center)
        print(len(self.macrocells))
        self.macrocells.append(macrocell)

        # place vertices of the hexagon

        for i in range(1,(self.n_site*2)-2,2):
            position = Coordinate(self.center.x + self.d_macromacro*cos(i*pi/6), self.center.y + self.d_macromacro*sin(i*pi/6))
            macrocell = Macrocell(position)
            self.macrocells.append(macrocell)
            
        print(len(self.macrocells))
        
        

class Ue:
    position = Coordinate

    def __init__(self, x, y, index):
        self.position.x = x
        self.position.y = y
        self.index = index


#def placeUe(macrocell, smallcell):