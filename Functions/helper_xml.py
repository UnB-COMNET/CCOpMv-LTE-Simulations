from calendar import c
from genericpath import exists
from math import atan, sqrt, degrees
from random import randrange
from typing import List

from geometry import Ue, Movement
from coordinates import Coordinate
from geometry import MapChess
import xml.etree.ElementTree as ET
import re

def get_map_ues_time(scen: MapChess, xml_filename: str, ues_per_slice: list) -> List[List[int]]:
  """This function parses a snapshot file (.sna) returning quantity of UEs in the map sections over time."""
  accumulated_xml = ''
  map_ues_time = [[len(region) for region in scen.map_ues]]
  coords_obj = []
  count = 0
  ue_target = 0
  last_simTime = 1
  current_simTime = None
  
  with open(xml_filename) as temp:
    while True:
      line = temp.readline()
      if line:
        if line.startswith('<?xml'):
            if accumulated_xml != '':
                root = ET.XML(accumulated_xml)
                
                current_simTime = int(root.get('simtime'))
                if current_simTime != last_simTime:
                  ue_target = 0

                while(int(root.get('simtime')) > len(map_ues_time)):
                  map_ues_time.append([])
                  for i in range(scen.n_sectors):
                    map_ues_time[-1].append(0)
                    
                #startTime_obj = root.findall(".//*[@class='omnetpp::cPar']")
                #startTime_text = startTime_obj[-6].find("./info").text              
                #startTime_text = startTime_text.split('s')[0]
                for ue in ues_per_slice[current_simTime - 1]:
                  if ue == ue_target:
                    coords_obj = root.findall(".//*[@class='inet::Coord']")
                    #Supoe que a "lastPosition" seja o penultimo objeto com essa classe
                    coords_text = coords_obj[-2].find("./info").text
                    coords_numbers = [float(s) for s in coords_text.split('(')[1].split(')')[0].split(', ') if s[0].isdigit()]
                    coord = Coordinate(x= coords_numbers[0], y= coords_numbers[1], z= coords_numbers[2])
                    
                    if not scen.existUe(ue):
                      print("Colocando UE[{}] na posicao {} no slice {}".format(ue, coord, int(root.get('simtime'))-1))
                      scen.placeUE(coord, ue, 0, 0)

                    map_ues_time[int(root.get('simtime'))-1][scen.coord2Region(coord)] += 1

                ue_target += 1
                accumulated_xml = ''
        elif not line.startswith('<!--'):#Not a comment
            accumulated_xml += line
      else:
        root = ET.XML(accumulated_xml)

        current_simTime = int(root.get('simtime'))
        if current_simTime != last_simTime:
          ue_target = 0

        while(int(root.get('simtime')) > len(map_ues_time)):
          map_ues_time[-1].append(0)

        for ue in ues_per_slice[current_simTime - 1]:
          if ue == ue_target:
            coords_obj = root.findall(".//*[@class='inet::Coord']")
            #Supoe que a "lastPosition" seja o penultimo objeto com essa classe
            coords_text = coords_obj[-2].find("./info").text
            coords_numbers = [float(s) for s in coords_text.split('(')[1].split(')')[0].split(', ') if s[0].isdigit()]
            coord = Coordinate(x= coords_numbers[0], y= coords_numbers[1], z= coords_numbers[2])
          
            if not scen.existUe(ue):
              scen.placeUE(coord, ue, 0, 0)

            map_ues_time[int(root.get('simtime'))-1][scen.coord2Region(coord)] += 1

        accumulated_xml = ''
        
        break
      
      last_simTime = current_simTime
      count += 1
  
  # Verifying
  for i in range(len(ues_per_slice)):
    if len(ues_per_slice[i]) != sum(map_ues_time[i]):
      return None
    
  return map_ues_time
  

def get_ues_time(xml_filename: str, time: float = 1, ues_per_slice: list = []) -> List[List[Ue]]:
  """This function parses a snapshot file (.sna) returning the UEs location over time (matrix)."""
  ue_target = 0
  last_simTime = 1
  current_simTime = None
  accumulated_xml = ''
  ues_time = []

  with open(xml_filename) as temp:
    while True:
      line = temp.readline()
      if line:
        if line.startswith('<?xml'):
            if accumulated_xml != '':
                root = ET.XML(accumulated_xml)

                current_simTime = int(root.get('simtime'))
                if current_simTime != last_simTime:

                  ue_target = 0

                while(int(root.get('simtime')) > len(ues_time)):
                  ues_time.append([])
                
                startTime_obj = root.findall(".//*[@class='omnetpp::cPar']")
                startTime_text = startTime_obj[-6].find("./info").text              
                startTime_text = startTime_text.split('s')[0]
                coords_obj = root.findall(".//*[@class='inet::Coord']")
                #Supoe que a "lastPosition" seja o penultimo objeto com essa class inet::Coord
                coords_text = coords_obj[-2].find("./info").text
                coords_numbers = [float(s) for s in coords_text.split('(')[1].split(')')[0].split(', ') if s[0].isdigit()]
                coord = Coordinate(x= coords_numbers[0], y= coords_numbers[1], z= coords_numbers[2])
                #Supoe que a "lastVelocity" seja o ultimo objeto com essa class inet::Coord
                #lasVelocity diz a velocidade inicial do slice anterior
                speed_text = coords_obj[-1].find("./info").text
                speed_numbers = [float(s) for s in speed_text.split('(')[1].split(')')[0].split(', ') if s[0].isdigit() or (len(s) > 1 and s[0] == '-' and s[1].isdigit())]
                speed = sqrt(speed_numbers[0]**2 + speed_numbers[1]**2)/time
                # Alguns casos a velocidade é nula, logo resulta numa divisao 0/0
                if speed_numbers[0] != 0:
                  direction = degrees(atan(speed_numbers[1]/speed_numbers[0]))
                else:
                  direction = degrees(0)
                mov = Movement(speed, direction,int(startTime_text))
                #print("Adicionando UE {} no tempo {}".format([int(s) for s in re.findall(r'\d+', root.get('object'))][-1], int(root.get('simtime'))-1))
                ues_time[int(root.get('simtime'))-1].append(Ue(coord, [int(s) for s in re.findall(r'\d+', root.get('object'))][-1]))
                ues_time[int(root.get('simtime'))-1][-1].movement = mov
                    
                ue_target += 1
                accumulated_xml = ''
        elif not line.startswith('<!--'):#Not a comment
            accumulated_xml += line
      else:
        root = ET.XML(accumulated_xml)

        current_simTime = int(root.get('simtime'))
        if current_simTime != last_simTime:
          ue_target = 0

        startTime_obj = root.findall(".//*[@class='omnetpp::cPar']")
        startTime_text = startTime_obj[-6].find("./info").text              
        startTime_text = startTime_text.split('s')[0]
        coords_obj = root.findall(".//*[@class='inet::Coord']")
        #Supoe que a "lastPosition" seja o penultimo objeto com essa class inet::Coord
        coords_text = coords_obj[-2].find("./info").text
        coords_numbers = [float(s) for s in coords_text.split('(')[1].split(')')[0].split(', ') if s[0].isdigit()]
        coord = Coordinate(x= coords_numbers[0], y= coords_numbers[1], z= coords_numbers[2])
        #Supoe que a "lastVelocity" seja o ultimo objeto com essa class inet::Coord
        speed_text = coords_obj[-1].find("./info").text
        speed_numbers = [float(s) for s in speed_text.split('(')[1].split(')')[0].split(', ') if s[0].isdigit() or (len(s) > 1 and s[0] == '-' and s[1].isdigit())]
        speed = sqrt(speed_numbers[0]**2 + speed_numbers[1]**2)/time
        direction = degrees(atan(speed_numbers[1]/speed_numbers[0]))
        mov = Movement(speed, direction,int(startTime_text))
        ues_time[int(root.get('simtime'))-1].append(Ue(coord, [int(s) for s in re.findall(r'\d+', root.get('object'))][-1]))
        ues_time[int(root.get('simtime'))-1][-1].movement = mov

        accumulated_xml = ''
        
        break
      
      last_simTime = current_simTime
  
  return ues_time