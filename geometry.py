from math import cos, pi, sqrt, sin
from typing import List, Union
from random import random
import matplotlib
import matplotlib.pyplot as plt

class Coordinate:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def setCoordinate(self, x, y):
        self.x = x
        self.y = y

class Smallcell:
    def __init__(self, center: Coordinate) -> None:
        self.center = center
        self.antennas = []

    def getAntennasPositionList(self) -> List[List[float]]:
        '''Documentation...'''
        if not self.antennas:
            print("There are no antennas in the smallcell")
            return [None,None]

        list_coordinateX = []
        list_coordinateY = []
        for i in range(len(self.antennas)):
            list_coordinateX.append(self.antennas[i].position.x)
            list_coordinateY.append(self.antennas[i].position.y)
        
        return [list_coordinateX,list_coordinateY]


class Macrocell:
    def __init__(self, center: Coordinate) -> None:
        self.center = center
        self.smallcells = []

    def getSmallcellsPositionList(self) -> List[List[float]]:
        '''Documentation...'''
        if not self.smallcells:
            print("There are no antennas in the smallcell")
            return [None,None]

        list_coordinateX = []
        list_coordinateY = []
        for i in range(len(self.smallcells)):
            list_coordinateX.append(self.smallcells[i].center.x)
            list_coordinateY.append(self.smallcells[i].center.y)
        
        return [list_coordinateX,list_coordinateY]
    
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

    def getMacrocellsPositionList(self) -> List[List[float]]:
        '''Documentation...'''
        if not self.macrocells:
            print("There are no macrocells in the hexagonal map")
            return [None,None]

        list_coordinateX = []
        list_coordinateY = []
        for i in range(len(self.macrocells)):
            list_coordinateX.append(self.macrocells[i].center.x)
            list_coordinateY.append(self.macrocells[i].center.y)
        
        return [list_coordinateX,list_coordinateY]
            
        
class Antenna:
    def __init__(self, position: Coordinate, index) -> None:
        self.position = position
        self.index = index


class Ue:
    position = Coordinate

    def __init__(self, x, y, index):
        self.position.x = x
        self.position.y = y
        self.index = index

def placeSmallCell(macrocell: Macrocell, radius, min_distance) -> None:
    position = placeObject(macrocell,radius,min_distance)
    smallcell = Smallcell(position)
    macrocell.smallcells.append(smallcell)

def placeAntennas(smallcell: Smallcell, radius, min_distance, n_antennas: int) -> None:
    for i in range(n_antennas):
        position = placeObject(smallcell, radius, min_distance)
        antenna = Antenna(position, None)
        smallcell.antennas.append(antenna)

def placeObject(obj: Union[Macrocell,Smallcell], radius, min_distance) -> Coordinate:
    not_Done = True
    while not_Done:
        x = radius * (1 - 2 * random()) + obj.center.x
        y = radius * (1 - 2 * random()) + obj.center.y
        position = Coordinate(x,y)
        not_Done = euclidianDistance(position, obj.center) < min_distance
    
    return position
#def placeUe(macrocell, smallcell):

def euclidianDistance(a: Coordinate, b: Coordinate) -> float:
    d = sqrt(pow(a.x - b.x,2) + pow(a.y - b.y,2))
    return d

def startScenario() -> None:
    # Creating hexagonal map
    center = Coordinate(1500,1500)
    map = MapHexagonal(center)

    for i in range(len(map.macrocells)):
        # For each macrocell, it places the smallcells
        placeSmallCell(map.macrocells[i], map.d_macromacro*0.425, map.d_macrocluster)
        # For each smallcell in a given macrocell, it places the antennas
        for j in range(len(map.macrocells[i].smallcells)):
            placeAntennas(map.macrocells[i].smallcells[j],map.dropradius_sc_cluster,0,map.n_antennas)            

    plotMap(map)
    None

def plotMap(map: MapHexagonal) -> None:
    [macrocells_eixoX, macrocells_eixoY] = map.getMacrocellsPositionList() 
    plt.plot(macrocells_eixoX, macrocells_eixoY, linestyle='', marker='o', color='red')
    for i in range(len(map.macrocells)):        
        [smallcells_eixoX, smallcells_eixoY] = map.macrocells[i].getSmallcellsPositionList()
        plt.plot(smallcells_eixoX, smallcells_eixoY, linestyle='', marker='.', color='green')
        for j in range(len(map.macrocells[i].smallcells)):
            [antennas_eixoX, antennas_eixoY] = map.macrocells[i].smallcells[j].getAntennasPositionList()
            plt.plot(antennas_eixoX, antennas_eixoY, linestyle='', marker='.', color='blue')
        
    plt.show()
    print("Plot")