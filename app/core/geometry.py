from app.core.sinr_comput import MapScenarioConfig
from dataclasses import dataclass
from math import cos, pi, sqrt, sin
from typing import List, Union, Tuple
from random import random, seed, normalvariate
import matplotlib.pyplot as plt
import numpy as np
from numpy import arctan
from app.core.sinr_comput import compute_sinr
from app.core.coordinates import Coordinate, PolarCoordinate


@dataclass(frozen=True, slots=True, kw_only=True)
class MapSimulationConfig:
    num_slices: int
    simtime_move: int
    slice_time: int

@dataclass(frozen=True, slots=True, kw_only=True)
class MapSizeConfig:
    size_x: int
    size_y: int
    size_sector: int



class Region:
    def __init__(self, index, num_users, max_users, serving_antennas):
        """
        Initialize a Region instance.

        Args:
            index (int): Region index.
            num_users (int): Number of users in the region.
            max_users (int): Maximum number of users served by antenna of the respective region.
            serving_antennas (List[int]): List of serving antennas region ID in the region.
        """
        self.index = index
        self.num_users = num_users
        self.max_users = max_users
        self.serving_antennas = serving_antennas
        self.num_serving_antennas = len(serving_antennas)

    def setServingAntennas(self, serving_antennas):
        """
        Set the serving antennas for the region.

        Args:
            serving_antennas (List[int]): List of serving antenna region ID in the region.
        """
        self.serving_antennas = serving_antennas
        self.num_serving_antennas = len(serving_antennas)

    def __str__(self) -> str:
        """
        Return a string representation of the Region instance.
        The format is:
            Region {index}
            Num users: {number of users}
            Serving antennas: {serving antenna region ID}

        Returns:
            str: String representation of the Region instance.
        """
        return f"Region {self.index}\n\tNum users: {self.num_users}\n\tServing antennas: {self.serving_antennas}"


class Smallcell:
    """Represents a Smallcell region, composed of a center, antennas and UEs"""
    
    def __init__(self, center: Coordinate):
        """Initializes a Smallcell around the informed center"""
        self.center = center
        self.antennas = []
        self.ues = []

    def getAntennasPositionList(self) -> List[Coordinate]:
        """Returns the coordinates of the antennas"""
        if not self.antennas:
            print("There are no antennas in the smallcell")
            return []

        list_coordinate = []
        for i in range(len(self.antennas)):
            list_coordinate.append(
                self.antennas[i].position)
        
        return list_coordinate

    def getUEsPositionList(self) -> List[Coordinate]:
        """Returns the coordinates of the UEs"""
        if not self.ues:
            print("There are no UEs in the smallcell")
            return []
    
        list_coordinate = []
        for i in range(len(self.ues)):
            list_coordinate.append(self.ues[i].position)  

        return list_coordinate

class Macrocell:
    """Returns the a Macrocell region, composed of a center, antennas, UEs and Smallcells"""
    
    def __init__(self, center: Coordinate) :
        """Initializes a Macrocell around the informed center"""
        self.center = center
        self.smallcells = []
        self.ues = []
        self.antennas = []

    def getSmallcellsPositionList(self) -> List[Coordinate]:
        """Returns the coordinates of the Smallcells centers"""
        if not self.smallcells:
            print("There are no smallcell in the macrocell")
            return []

        list_coordinate = []
        for i in range(len(self.smallcells)):
            list_coordinate.append(self.smallcells[i].center)
        
        return list_coordinate
    
    def getUEsPositionList(self) -> List[Coordinate]:
        """Returns the coordinates of the UEs"""
        if not self.ues:
            print("There are no UE in the macrocell")
            return []
    
        list_coordinate = []
        for i in range(len(self.ues)):
            list_coordinate.append(self.ues[i].position)

        return list_coordinate

    def getAntennasPositionList(self) -> List[Coordinate]:
        """Returns the coordinates of the antennas"""
        if not self.antennas:
            print("There are no antenna in the macrocell")
            return []
    
        list_coordinate = []
        for i in range(len(self.antennas)):
            list_coordinate.append(self.antennas[i].position)
        
        return list_coordinate

class MapHexagonal:
    """Represents a scenario with a hexagonal format containing Macrocells"""

    def __init__(self, center: Coordinate, n_site: int = 7, n_antennas: int = 10, n_ues: int = 30) :
        """Initializes the scenario bases on the center Coordinates and other parameters"""
        self.d_macromacro = 1000
        self.d_macrocluster = 105
        self.d_macroue = 35
        self.d_smallsmall = 20
        self.dropradius_mc = 250
        self.dropradius_sc = 500
        self.dropradius_sc_cluster = 50
        self.dropradius_ue_cluster = 70

        self.n_site = n_site
        self.n_cluster = 1
        self.n_antennas = n_antennas
        self.n_ues = n_ues
        
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

    def getMacrocellsPositionList(self) -> List[Coordinate]:
        """Returns the coordinates of the Macrocells centers"""
        if not self.macrocells:
            print("There are no macrocells in the hexagonal map")
            return []

        list_coordinate = []
        for i in range(len(self.macrocells)):
            list_coordinate.append(self.macrocells[i].center)
        
        return list_coordinate

    def placeSmallCell(self, macrocell: Macrocell, radius, min_distance) :
        """Places a Smallcell in the informed Macrocell"""
        position = placeObject(macrocell,radius,min_distance)
        smallcell = Smallcell(position)
        macrocell.smallcells.append(smallcell)
                
    def placeUEs(self):
        """Places the necessary UEs 
        
        The UEs are placed based on the informed number of UEs
        per Macrocell, acording with the 3GPP TR 36.814 Annex A.2.1.1.2
        Configuration 4b.
        
        This configuration assumes the existence of one Smallcell inside each Macrocell."""
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
        """Places the necessary antennas of the informed Smallcell"""
        for i in range(n_antennas):
            position = placeObject(smallcell, radius, min_distance)
            antenna = Antenna(position, None)
            smallcell.antennas.append(antenna)

class Antenna:
    """Represents a antenna (eNodeB)"""

    def __init__(self, position: Coordinate, index) :
        """Initializes the antenna based on its coordinates"""
        self.position = position
        self.index = index

class Ue:
    """Represents a UE"""

    def __init__(self, position: Coordinate, index, speed = 0, dir = 0, startTime = 0):
        """Initializes the UE based on its coordinates, speed and direction"""
        self.position = position
        self.index = index
        self.movement = Movement(speed, dir, startTime)

    def __str__(self):
        return f'Ue> Id: {self.index}; Position: {self.position}; Movement: {self.movement}.'

class Movement:
    """Represents a movement made by an entity"""

    def __init__(self, speed, dir, startTime):
        """Initializes the class based on the its speed and direction"""
        self.speed = speed
        self.direction = dir
        self.startTime = startTime

    def __str__(self):
        return f'({self.speed} m/s, {self.direction}°)'

def placeObject(obj: Union[Macrocell,Smallcell], radius, min_distance) -> Coordinate:
    """Determines the position of an object randomly based on the radius
    and minimal distance informed"""
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
    """Computes the euclidian distance between two coordinates"""
    d = sqrt(pow(a.x - b.x,2) + pow(a.y - b.y,2) + pow(a.z - b.z,2))
    return d

def polar2rect(r, phi) -> Tuple[float, float]:
    """Converts a polar coordinate to its retangular form"""
    x = r * cos(phi)
    y = r * sin(phi)
    return x, y

def rect2polar(x, y) -> Tuple[float, float]:
    """Converts a rectangular coordinate to its polar form"""
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
    """Starts a MapHexagonal scenario creating its class and positioning the necessary entities"""
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
    """Plot a map of the MapHexagonal scenario using matplotlib"""

    if n_macrocells != 1 and n_macrocells != 7:
        print("Invalid number of macrocells. Insert 1 or 7.")        
        return

    macrocells = map.getMacrocellsPositionList() 
    if n_macrocells == 1:
        plt.plot([coord.x for coord in macrocells][0], [coord.y for coord in macrocells][0], linestyle='', marker='o', color='red')
    else:
        plt.plot([coord.x for coord in macrocells], [coord.y for coord in macrocells], linestyle='', marker='o', color='red')
    
    for i in range(n_macrocells):
        smallcells = map.macrocells[i].getSmallcellsPositionList()
        if n_macrocells == 1:
            plt.plot([coord.x for coord in smallcells][0], [coord.y for coord in smallcells][0], linestyle='', marker='.', color='green')
        else:
            plt.plot([coord.x for coord in smallcells], [coord.y for coord in smallcells], linestyle='', marker='.', color='green')
        
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
    """Represents a scenario that divides the map into multiple square shaped regions (sectors)"""
    def __init__(
        self,
        chosen_seed: int,
        simulation_config: MapSimulationConfig, 
        size_config: MapSizeConfig, 
        scenario_config: MapScenarioConfig
        ) :
        """Initializes the scenario based on multiple parameters"""

        self.size_config = size_config
        self.max_length = sqrt(size_config.size_x**2 + size_config.size_y**2)
        self.centre_coord = Coordinate(size_config.size_x/2, size_config.size_y/2)
        self.n_sectors_x = int(size_config.size_x/size_config.size_sector)
        self.n_sectors_y = int(size_config.size_y/size_config.size_sector)
        self.n_sectors = self.n_sectors_y*self.n_sectors_x
        self.chosen_seed = chosen_seed
        
        self.map_antennas = []
        self.map_ues: list[Ue] = []

        self.scenario_config = scenario_config

        self.simulation_config=simulation_config 


    def region2Coord(self, region_id: int, z: float = 0) -> Coordinate:
        """Returns the central coordinate of a region (sector)"""
        coord = Coordinate(
            self.size_config.size_sector*(region_id%self.n_sectors_x)+self.size_config.size_sector/2,
            self.size_config.size_sector*int(region_id/self.n_sectors_y)+self.size_config.size_sector/2,
            z)
        return coord

    def coord2Region(self, coord: Coordinate) -> int:
        """Returns the number of the region (sector) that contains the informed coordinate"""
        line = int(coord.y/self.size_config.size_sector)
        line = line if line < self.n_sectors_x else self.n_sectors_x-1
        column = int(coord.x/self.size_config.size_sector)
        column = column if column < self.n_sectors_y else self.n_sectors_y-1

        region_id = line*self.n_sectors_x + column
        return region_id

    def placeTestUEs(self):
        """Places one UE in the center of each region (sector)"""
        #self.map_ues = np.array(
        #                [[Ue(self.region2Coord(m), m)] 
        #                for m in range(self.n_sectors)])
        self.map_ues = np.empty(self.n_sectors, dtype= np.dtype(object))
        self.map_ues.fill([])
        for m in range(self.n_sectors):
            coord = self.region2Coord(m)
            self.map_ues[m] = [Ue(coord, m)]

    def placeUE(self, coord: Coordinate, index, speed, dir):
        """Places one UE at the informed coordinate"""
        if len(self.map_ues) != self.n_sectors:
            for r in range(self.n_sectors):
                self.map_ues.append([])
        
        self.map_ues[coord2Region(coord, self.size_config.size_sector, self.size_config.size_x, self.size_config.size_y)].append(Ue(coord,index,speed,dir))

    def placeUEs(self, type: str = "Full", small_per_macro: int = 1, fixed: bool = False, n_macros = 5, n_ues_macro = 60, ues_per_slice: list = []):
        """Places UEs across the map based on the informed type"""
        #Full = 4320 UEs
        slice_time_move = int(self.simulation_config.simtime_move/self.simulation_config.num_slices)

        startTimeArray = n_ues_macro*[-1]
        for slice in range(len(ues_per_slice)):
            for ue in ues_per_slice[slice]:
                if startTimeArray[ue] == -1:
                    startTimeArray[ue] = slice*(slice_time_move)
         
        count = 0
        mean_speed = int(3000/slice_time_move)                  # base velocity: 3000 mps
        var_speed = int(1000/slice_time_move)            
        self.map_ues = []
        seed(self.chosen_seed)

        for r in range(self.n_sectors):
            self.map_ues.append([])

        if type == "Full":
            ues = self.uesFullMapHexa_(small_per_macro=small_per_macro, n_ues_macro=n_ues_macro)
        elif type == "Random":
            ues = self.uesRandomMapHexa_(small_per_macro=small_per_macro, n_macros=n_macros, n_ues_macro=n_ues_macro)
        else: 
            ues = []

        for ue in ues:
            region = self.coord2Region(ue.position)
            if region < self.n_sectors:
                if not fixed:
                    #Defining inital movement of the ues
                    ue.movement.speed = normalvariate(mu= mean_speed, sigma= var_speed)
                    ue.movement.direction = random() * 360
                    ue.movement.startTime = startTimeArray[ue.index]
                self.map_ues[region].append(ue)
                count += 1

    def loadUEs(self, ues: List[Ue]):
        self.map_ues = []
        for r in range(self.n_sectors):
            self.map_ues.append([])
            
        for ue in ues:
            region = self.coord2Region(ue.position)
            if region < self.n_sectors:
                self.map_ues[region].append(ue)

    def placeAntennas(self, list_regions: List[int]) :
        """Places antennas in the center of the regions (sectors) informed"""
        count = 0
        self.map_antennas = np.empty(self.n_sectors, dtype= np.dtype(object))
        self.map_antennas.fill(None)
        for m in list_regions:
            if m < self.map_antennas.size:
                coord = self.region2Coord(m)
                self.map_antennas[m] = Antenna(coord, count)
                count += 1

    def uesRandomMapHexa_(self, small_per_macro = 1, n_macros = 20, n_ues_macro = 60)-> List[Ue]:
        """Places UEs using fictional macrocells placed randomly in space delimited by a margin
        
        The UEs are placed based on the informed number of UEs
        per Macrocell, acording with the 3GPP TR 36.814 Annex A.2.1.1.2
        Configuration 4b."""
        d_macromacro = 1000
        d_macrocluster = 105
        d_macroue = 35
        dropradius_ue_cluster = 70
        n_ues = n_ues_macro
        margin = 500

        tmp_smc: List[Smallcell] = []
        tmp_mcs: List[Macrocell] = []

        for i in range(n_macros):
            tmp_mcs.append(Macrocell(Coordinate(random()*(self.size_config.size_x - 2*margin)+margin, random()*(self.size_config.size_y - 2*margin)+margin)))
            for i in range (small_per_macro):
                    pos_small = placeObject(tmp_mcs[-1],d_macromacro*0.425,d_macrocluster)
                    tmp_smc.append(Smallcell(pos_small))

        ues = self.placeHexaUes_(tmp_mcs, tmp_smc, n_ues, dropradius_ue_cluster, d_macromacro, d_macroue, small_per_macro)

        return ues

    #Place UEs using macrocells placed across all space
    def uesFullMapHexa_(self, small_per_macro = 1, n_ues_macro = 60) -> List[Ue]:
        """Places UEs using macrocells placed across all space trying to maximize their quantity
        without overlaping macrocells.
        
        The UEs are placed based on the informed number of UEs
        per Macrocell, acording with the 3GPP TR 36.814 Annex A.2.1.1.2
        Configuration 4b."""
        d_macromacro = 1000
        d_macrocluster = 105
        d_macroue = 35
        dropradius_ue_cluster = 70
        n_ues = n_ues_macro


        tmp_smc: List[Smallcell] = []
        tmp_mcs: List[Macrocell] = []

        d_x = d_macromacro*cos(1*pi/6)
        d_y = d_macromacro*sin(1*pi/6)
        
        coord_x = self.size_config.size_sector/2
        while(coord_x < self.size_config.size_x):
            coord_y = self.size_config.size_sector/2
            while(coord_y < self.size_config.size_y):
                tmp_mcs.append(Macrocell(Coordinate(coord_x, coord_y)))
                for i in range (small_per_macro):
                    pos_small = placeObject(tmp_mcs[-1],d_macromacro*0.425,d_macrocluster)
                    pos_small = self.verifyCoord_(pos_small)
                    tmp_smc.append(Smallcell(pos_small))
                coord_y += d_macromacro
            coord_x += 2*d_x

        coord_x = self.size_config.size_sector/2+d_x
        while(coord_x < self.size_config.size_x):
            coord_y = self.size_config.size_sector/2+d_y
            while(coord_y < self.size_config.size_y):
                tmp_mcs.append(Macrocell(Coordinate(coord_x, coord_y)))
                for i in range (small_per_macro):
                    pos_small = placeObject(tmp_mcs[-1],d_macromacro*0.425,d_macrocluster)
                    pos_small = self.verifyCoord_(pos_small)
                    tmp_smc.append(Smallcell(pos_small))
                coord_y += d_macromacro
            coord_x += 2*d_x

        ues = self.placeHexaUes_(tmp_mcs, tmp_smc, n_ues, dropradius_ue_cluster, d_macromacro, d_macroue, small_per_macro)

        return ues

    def placeHexaUes_(self, tmp_mcs: List[Macrocell], tmp_smc: List[Smallcell], n_ues:int, dropradius_ue_cluster: int,
                      d_macromacro: int, d_macroue: int, small_per_macro: int) -> List[Ue]:
        """Places the UEs according with the macrocells and smallcells informed.
        
        The UEs are placed based on the informed number of UEs
        per Macrocell, acording with the 3GPP TR 36.814 Annex A.2.1.1.2
        Configuration 4b."""
        
        count = 0
        ues: List[Ue] = []
        for i in range(len(tmp_mcs)):
            macrocell = tmp_mcs[i]
            smallcells = tmp_smc[i*small_per_macro: i*small_per_macro+small_per_macro]
            for n in range(n_ues):
                if random() < 0.6666:
                    # Place into smallcells
                    position = placeObject(smallcells[int(random()*small_per_macro)], dropradius_ue_cluster, 0)
                    position = self.verifyCoord_(position)
                    ue = Ue(position, count)
                    ues.append(ue)
                    count += 1
                    smallcells[int(random()*small_per_macro)].ues.append(ue)
                else:
                    # Place into macrocell
                    position = placeObject(macrocell, d_macromacro*0.425, d_macroue)
                    position = self.verifyCoord_(position)
                    ue = Ue(position, count)
                    ues.append(ue)
                    count += 1
                    macrocell.ues.append(ue)

        return ues
    
    def verifyCoord_(self, coord: Coordinate):
        """Verifies if the coordinate is within the delimited map"""
        if (coord.x < 0):
            coord.x = 0
        if (coord.x > self.size_config.size_x):
            coord.x = self.size_config.size_x
        if (coord.y < 0):
            coord.y = 0
        if (coord.y > self.size_config.size_y):
            coord.y = self.size_config.size_y
        return coord

    def plotUes(self, external: bool = False, ues_positions: List[Coordinate] = None):
        """Plots the existing UEs using matplotlib"""
        if not external: ues = self.getUEsPositionList()
        else: ues = ues_positions

        plt.plot([coord.x for coord in ues], [coord.y for coord in ues], linestyle='', marker='.', color='orange', markersize= 2)
        plt.gca().invert_yaxis()
        plt.show()
        print("Plot")

    def getRegionsCentersList(self) -> List[Coordinate]:
        """Returns the coordinates of each region (sector) center."""
        list_coordinate = []
        for m in range(self.n_sectors):
            coord = self.region2Coord(m)
            list_coordinate.append(coord)
        
        return list_coordinate

    def getRegionsDistanceMatrix(self) -> List[List[float]]:
        """Returns the distance between every region."""
        matrix_distances: List[List[float]] = []
        list_coordinates = self.getRegionsCentersList()
        for a in list_coordinates:
            matrix_distances.append([])
            for b in list_coordinates:
                matrix_distances[-1].append(euclidianDistance(a, b))

        return matrix_distances

    def getAntennasPositionList(self) -> List[Coordinate]:
        """Returns the coordinates of all antennas."""
        list_coordinate = []
        for ant in self.map_antennas:
            if (ant != None):
                list_coordinate.append(ant.position)
        
        return list_coordinate

    def getUEsPositionList(self) -> List[Coordinate]:
        """Returns the coordinates of all UEs."""
        list_coordinate = []
        for region in self.map_ues:
            for ue in region:
                list_coordinate.append(ue.position)
        
        return list_coordinate

    def getUEsList(self) -> List[Ue]:
        """Returns all UEs."""
        list_ues = []
        for region in self.map_ues:
            for ue in region:
                list_ues.append(ue)
        return list_ues

    def existUe(self, index) -> bool:
        """TODO: Return true if exists ue"""
        result = False
        for region in self.map_ues:
            for ue in region:
                if ue.index == index:
                    result = True

        return result


    def getUEsMovementList(self) -> List[Movement]:
        """Returns the movement atribute of all UEs."""
        list_movement = []
        for region in self.map_ues:
            if (region != []):
                for ue in region:
                    list_movement.append(ue.movement)
        
        return list_movement

    def getSinrMap(self) -> List[List[float]]:
        """Returns the sinr map in Watts.
        
        The sinr map is composed of the received sinr values at each region (section)
        for a antenna (eNodeB) positioned at each one of the regions (sections)"""
        regions_centers = self.getRegionsCentersList()
        sinr_map = []
        seed(self.chosen_seed+1)

        for enb_region in range(self.n_sectors):
            sinr_map.append([])
            enb_coord = self.region2Coord(enb_region)
            for ue_coord in regions_centers:

                # Considering Downlink
                tx_gain = self.scenario_config.gain_enb
                rx_gain = self.scenario_config.gain_ue

                noise_figure = self.scenario_config.ue_noise_figure

                sinr = compute_sinr(
                    speed= 0,
                    ue_coord= ue_coord,
                    tx_coord= enb_coord,
                    scenario_config=self.scenario_config
                )
                sinr_map[enb_region].append(sinr)

        return sinr_map

class Centroid:
    def __init__(self, center: Coordinate):
        self.center = center
        self.ues = []

    def placeUEs(self,numUE, radius, radius_ues):
        """
        Place UEs around the centroid (circular region).

        Args:
            numUE (int): Number of UEs to place.
            radius (float): Radius for Macrocell placement.
            radius_ues (float): Radius for UEs placement around macrocell.

        Returns:
            None
        """
        for n in range(numUE):
            macrocell = Macrocell(self.center)
            coord_macrocell = placeObject(macrocell,radius,0)
            macrocell = Macrocell(coord_macrocell)

            position = placeObject(macrocell,radius_ues,0)
            ue = Ue(position,n)
            self.ues.append(ue)
    
    def getUEsPositionList(self) -> List[Coordinate]:
        """
        Get the positions of UEs in the centroid (circular region).

        Returns:
            List[Coordinate]: List of UE positions.
        """
        if not self.ues:
            print("There are no UEs in the smallcell")
            return []
    
        list_coordinate = []
        for i in range(len(self.ues)):
            list_coordinate.append(self.ues[i].position)  

        return list_coordinate

def region2Coord( region_id: int, size_sector: float, size_x: float, size_y: float, z: float = 0) -> Coordinate:
    """
    Convert a region ID to coordinates (x,y,z) corresponding.

    Args:
        region_id (int): Region ID.
        size_sector (float): Side size of the square sector in meters.
        size_x (float): x dimension size of the considered map in meters.
        size_y (float): y dimension size of the considered map in meters.
        z (float, optional): z dimension coordinate (default is 0).

    Returns:
        Coordinate: Corresponding coordinates (x,y,z).
    """
    n_sectors_x = int(size_x/size_sector)
    n_sectors_y = int(size_y/size_sector)
    coord = Coordinate(
        size_sector*(region_id%n_sectors_x)+size_sector/2,
        size_sector*int(region_id/n_sectors_y)+size_sector/2,
        z)
    return coord

def coord2Region( coord: Coordinate, size_sector: float, size_x: float, size_y: float) -> int:
    """
    Convert coordinates (x,y,z) to the corresponding region ID.

    Args:
        coord (Coordinate): Coordinates.
        size_sector (float): Side size of the square sector in meters.
        size_x (float): x dimension size of the considered map in meters.
        size_y (float): y dimension size of the considered map in meters.

    Returns:
        int: Corresponding region ID.
    """
    n_sectors_x = int(size_x/size_sector)
    n_sectors_y = int(size_y/size_sector)
    line = int(coord.y/size_sector)
    line = line if line < n_sectors_x else n_sectors_x-1
    column = int(coord.x/size_sector)
    column = column if column < n_sectors_y else n_sectors_y-1

    region_id = line*n_sectors_x + column
    return region_id