from math import cos, pi, sqrt, sin
from typing import List, Mapping, Union, Tuple
from random import random
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from numpy import arctan, not_equal

class Coordinate:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def setCoordinate(self, x, y):
        self.x = x
        self.y = y

class PolarCoordinate:
    def __init__(self, r, phi):
        self.r = r
        self.phi = phi
    
    def setCoordinate(self, r, phi):
        self.r = r
        self.phi = phi

class Smallcell:
    def __init__(self, center: Coordinate):
        self.center = center
        self.antennas = []
        self.ues = []

    def getAntennasPositionList(self) -> List[Coordinate]:
        '''Documentation...'''
        if not self.antennas:
            print("There are no antennas in the smallcell")
            return [None]

        list_coordinate = []
        for i in range(len(self.antennas)):
            list_coordinate.append(
                self.antennas[i].position)
        
        return list_coordinate

    def getUEsPositionList(self) -> List[Coordinate]:
        '''Documentation'''
        if not self.ues:
            print("There are no UEs in the smallcell")
            return [None,None]
    
        list_coordinate = []
        for i in range(len(self.ues)):
            list_coordinate.append(self.ues[i].position)  

        return list_coordinate

class Macrocell:
    def __init__(self, center: Coordinate) :
        self.center = center
        self.smallcells = []
        self.ues = []
        self.antennas = []

    def getSmallcellsPositionList(self) -> List[List[float]]:
        '''Documentation...'''
        if not self.smallcells:
            print("There are no smallcell in the macrocell")
            return [None,None]

        list_coordinateX = []
        list_coordinateY = []
        for i in range(len(self.smallcells)):
            list_coordinateX.append(self.smallcells[i].center.x)
            list_coordinateY.append(self.smallcells[i].center.y)
        
        return [list_coordinateX,list_coordinateY]
    
    def getUEsPositionList(self) -> List[List[float]]:
        '''Documentation'''
        if not self.ues:
            print("There are no UE in the macrocell")
            return [None]
    
        list_coordinate = []
        for i in range(len(self.ues)):
            list_coordinate.append(self.ues[i].position)

        return list_coordinate

    def getAntennasPositionList(self) -> List[Coordinate]:
        '''Documentation'''
        if not self.antennas:
            print("There are no antenna in the macrocell")
            return [None]
    
        list_coordinate = []
        for i in range(len(self.antennas)):
            list_coordinate.append(
                Coordinate(self.antennas[i].x, self.antennas[i].y))
        
        return list_coordinate

class MapHexagonal:
    def __init__(self, center: Coordinate) :
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
        self.n_ues = 30
        
        self.center = center
        self.macrocells = []     
        self.placeMacrocells()
        
    def placeMacrocells(self) :
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

    def placeSmallCell(self, macrocell: Macrocell, radius, min_distance) :
        position = placeObject(macrocell,radius,min_distance)
        smallcell = Smallcell(position)
        macrocell.smallcells.append(smallcell)
                
    def placeUEs(self):
        for i in range(len(self.macrocells)):
            macrocell = self.macrocells[i]
            smallcell = macrocell.smallcells[0]
            for n in range(self.n_ues):
                if random() < 0.6666:
                    # Place into smallcells
                    position = placeObject(smallcell, self.dropradius_ue_cluster, 0)
                    ue = Ue(position, 5)
                    smallcell.ues.append(ue)
                else:
                    # Place into macrocell
                    position = placeObject(macrocell, self.d_macromacro*0.425, self.d_macroue)
                    ue = Ue(position, 5)
                    macrocell.ues.append(ue)                                          

    def placeAntennas(self, smallcell: Smallcell, radius, min_distance, n_antennas: int) :
        for i in range(n_antennas):
            position = placeObject(smallcell, radius, min_distance)
            antenna = Antenna(position, None)
            smallcell.antennas.append(antenna)

class Antenna:
    def __init__(self, position: Coordinate, index) :
        self.position = position
        self.index = index

class Ue:
    def __init__(self, position: Coordinate, index):
        self.position = position
        self.index = index

def placeObject(obj: Union[Macrocell,Smallcell], radius, min_distance) -> Coordinate:
    not_Done = True
    while not_Done:
        radius_obj = radius * sqrt(random())
        angle_obj = 2 * pi * random()
        positionPolar = PolarCoordinate(radius_obj, angle_obj)
        x, y = polar2rect(positionPolar.r, positionPolar.phi)
        x = x + obj.center.x
        y = y + obj.center.y
        position = Coordinate(x,y)
        
        not_Done = euclidianDistance(position, obj.center) < min_distance
    
    return position

def euclidianDistance(a: Coordinate, b: Coordinate) -> float:
    d = sqrt(pow(a.x - b.x,2) + pow(a.y - b.y,2))
    return d

def polar2rect(r, phi) -> Tuple[float, float]:
    x = r * cos(phi)
    y = r * sin(phi)
    return x, y

def rect2polar(x, y) -> Tuple[float, float]:
    r = sqrt(pow(x,2) + pow(y,2))
    if r == 0:
        print("The radius must be greater than zero")
        return None, None

    if x == 0 and y > 0:
        phi = pi/2
    elif x == 0 and y < 0:
        phi = 3/2 * pi
    else:        
        phi = arctan(y/x)

    if (x < 0 and y >= 0) or (x < 0 and y <= 0):
        phi = phi + pi
    elif (x > 0 and y < 0):
        phi = phi + 2 * pi

    return r, phi

def startScenario() -> MapHexagonal:
    # Creating hexagonal map
    center = Coordinate(1500,1500)
    map = MapHexagonal(center)

    for i in range(len(map.macrocells)):
        # For each macrocell, it places the smallcells
        map.placeSmallCell(map.macrocells[i], map.d_macromacro*0.425, map.d_macrocluster)
        # For each smallcell in a given macrocell, it places the antennas
        for j in range(len(map.macrocells[i].smallcells)):
            map.placeAntennas(map.macrocells[i].smallcells[j],map.dropradius_sc_cluster,0,map.n_antennas)            

    map.placeUEs()

    plotMap(map, plotUEs=True, n_macrocells=7)

    return map

def plotMap(map: MapHexagonal, plotUEs: bool, n_macrocells: int) :
    if n_macrocells != 1 and n_macrocells != 7:
        print("Invalid number of macrocells. Insert 1 or 7.")        
        return

    [macrocells_eixoX, macrocells_eixoY] = map.getMacrocellsPositionList() 
    if n_macrocells == 1:
        plt.plot(macrocells_eixoX[0], macrocells_eixoY[0], linestyle='', marker='o', color='red')
    else:
        plt.plot(macrocells_eixoX, macrocells_eixoY, linestyle='', marker='o', color='red')
    
    for i in range(n_macrocells):
        [smallcells_eixoX, smallcells_eixoY] = map.macrocells[i].getSmallcellsPositionList()
        if n_macrocells == 1:
            plt.plot(smallcells_eixoX[0], smallcells_eixoY[0], linestyle='', marker='.', color='green')
        else:
            plt.plot(smallcells_eixoX, smallcells_eixoY, linestyle='', marker='.', color='green')
        
        if plotUEs:            
            ues = map.macrocells[i].getUEsPositionList()
            plt.plot([coord.x for coord in ues], [coord.y for coord in ues], linestyle='', marker='*', color='orange')

        for j in range(len(map.macrocells[i].smallcells)):
            antennas = map.macrocells[i].smallcells[j].getAntennasPositionList()
            plt.plot([coord.x for coord in antennas], [coord.y for coord in antennas], linestyle='', marker='.', color='blue')

            if plotUEs:
                ues = map.macrocells[i].smallcells[j].getUEsPositionList()
                plt.plot([coord.x for coord in ues], [coord.y for coord in ues], linestyle='', marker='*', color='purple')

        if i == 0 and n_macrocells == 1:
            break
    
    plt.show()
    print("Plot")

class MapChess:
    def __init__(self, d_height: int = 1000, d_width: int = 1000, d_region: int = 100) :
        self.d_region = d_region
        self.d_width = d_width
        self.d_height = d_height
        self.n_width = int(d_width/d_region)
        self.n_height = int(d_height/d_region)
        self.n_regions = self.n_height*self.n_width
        
        self.map_antennas = np.empty(self.n_regions).fill(None)
        self.map_ues = np.empty(self.n_regions).fill(None)

    def region2Coord(self, region_id: int) -> Coordinate:
        coord = Coordinate(
            self.d_region*(region_id%self.n_width)+self.d_region/2,
            self.d_region*int(region_id/self.n_height)+self.d_region/2)
        return coord

    def coord2Region(self, coord: Coordinate) -> int:
        line = int(coord.y/self.d_region)
        line = line if line < self.n_width else self.n_width-1
        column = int(coord.x/self.d_region)
        column = column if column < self.n_height else self.n_height-1

        region_id = line*self.n_width + column
        return region_id

    def placeTestUEs(self):
        self.map_ues = np.array(
                        [[Ue(self.region2Coord(m), m)] 
                        for m in range(self.n_regions)])

    def placeAntennas(self, list_regions) :
        count = 0
        self.map_antennas = np.empty(self.n_regions).fill(None)
        for m in list_regions:
            if m < self.map_antennas.size:
                self.map_antennas[m] = Antenna(self.region2Coord(m), count)
                count += 1

    def getRegionsCentersList(self) -> List[List[float]]:
        list_coordinateX = []
        list_coordinateY = []
        for m in range(self.n_regions):
            coord = self.region2Coord(m)
            list_coordinateX.append(coord.x)
            list_coordinateY.append(coord.y)
        
        return [list_coordinateX,list_coordinateY]

    def getAntennasPositionList(self) -> List[Coordinate]:

        list_coordinate = []
        for ant in self.map_antennas:
            if (ant != None):
                list_coordinate.append(ant.position.x, ant.position.y)
        
        return [list_coordinate]

    def getUEsPositionList(self) -> List[List[float]]:
        list_coordinate = []
        for coord in self.map_ues:
            if (coord != None):
                for ue in coord:
                    list_coordinate.append(ue.position)
        
        return list_coordinate

    #def getSinrMap(self) -> List[List[float]]:
    #    regions_centers = self.getRegionsCentersList()
    #    for enb in range(self.n_regions):
    #        coord = self.region2Coord()
    #        for ue in regions_centers:
    #            pass


def exportMap():
    None