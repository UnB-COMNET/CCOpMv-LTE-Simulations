from math import cos, pi, sqrt, sin
from typing import Union
from random import random

class Coordinate:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def setCoordinate(self, x, y):
        self.x = x
        self.y = y

class Smallcell:
    def __init__(self, center: Coordinate, radius) -> None:
        self.center = center
        self.radius = radius
        self.antennas = []

class Macrocell:
    def __init__(self, center: Coordinate) -> None:
        self.center = center
        self.smallcells = []
    
class MapHexagonal:
    def __init__(self, center: Coordinate) -> None:
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

        self.placeMacrocells()
        
    def placeMacrocells(self) -> None:
        '''This method creates a hexagonal structure with six vertices
        around the atributte 'center' in class MapHexagonal'''
        # place macrocell center
        macrocell = Macrocell(self.center)
        self.macrocells.append(macrocell)

        # place vertices of the hexagon
        for i in range(1,(self.n_site*2)-2,2):
            position = Coordinate(self.center.x + self.d_macromacro*cos(i*pi/6), self.center.y + self.d_macromacro*sin(i*pi/6))
            macrocell = Macrocell(position)
            self.macrocells.append(macrocell)
            
        
        

class Ue:
    position = Coordinate

    def __init__(self, x, y, index):
        self.position.x = x
        self.position.y = y
        self.index = index

def placeObject(obj: Union[Macrocell,Smallcell], radius, min_Distance) -> Coordinate:
    not_Done = True
    while not_Done:
        x = radius * (1 - 2 * random()) + obj.center.x
        y = radius * (1 - 2 * random()) + obj.center.y
        position = Coordinate(x,y)
        not_Done = euclidianDistance(position, obj.center) < min_Distance
    
    return position
#def placeUe(macrocell, smallcell):

def euclidianDistance(a: Coordinate, b: Coordinate) -> float:
    d = sqrt(pow(a.x - b.x,2) + pow(a.y - b.y,2))
    return d

def startScenario() -> None:
    None