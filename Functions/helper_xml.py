from math import atan, sqrt, degrees
from typing import List

from geometry import Ue, Movement
from coordinates import Coordinate
from geometry import MapChess
import xml.etree.ElementTree as ET
import re

def get_map_ues_time(scen: MapChess, xml_filename: str) -> List[List[int]]:
  """This function parses a snapshot file (.sna) returning quantity of UEs in the map sections over time."""
  accumulated_xml = ''
  map_ues_time = [[len(region) for region in scen.map_ues]]
  coords_obj = []
  count = 0

  with open(xml_filename) as temp:
    while True:
      line = temp.readline()
      if line:
        if line.startswith('<?xml'):
            if accumulated_xml != '':
                root = ET.XML(accumulated_xml)
                while(int(root.get('simtime')) >= len(map_ues_time)):
                  map_ues_time.append([])
                  for i in range(scen.n_regions):
                    map_ues_time[-1].append(0)
                coords_obj = root.findall(".//*[@class='inet::Coord']")
                #Supoe que a "lastPosition" seja o penultimo objeto com essa classe
                coords_text = coords_obj[-2].find("./info").text
                coords_numbers = [float(s) for s in coords_text.split('(')[1].split(')')[0].split(', ') if s[0].isdigit()]
                coord = Coordinate(x= coords_numbers[0], y= coords_numbers[1], z= coords_numbers[2])
                map_ues_time[int(root.get('simtime'))][scen.coord2Region(coord)] += 1
                accumulated_xml = ''
        else:
            accumulated_xml += line
      else:
        root = ET.XML(accumulated_xml)
        while(int(root.get('simtime')) >= len(map_ues_time)):
          map_ues_time[-1].append(0)
        coords_obj = root.findall(".//*[@class='inet::Coord']")
        #Supoe que a "lastPosition" seja o penultimo objeto com essa classe
        coords_text = coords_obj[-2].find("./info").text
        coords_numbers = [float(s) for s in coords_text.split('(')[1].split(')')[0].split(', ') if s[0].isdigit()]
        coord = Coordinate(x= coords_numbers[0], y= coords_numbers[1], z= coords_numbers[2])
        map_ues_time[int(root.get('simtime'))][scen.coord2Region(coord)] += 1
        accumulated_xml = ''
        
        break

      count += 1

  return map_ues_time

def get_ues_time(ues_list, xml_filename: str) -> List[List[Ue]]:
  """This function parses a snapshot file (.sna) returning the UEs location over time."""
  accumulated_xml = ''
  ues_time = [ues_list]

  with open(xml_filename) as temp:
    while True:
      line = temp.readline()
      if line:
        if line.startswith('<?xml'):
            if accumulated_xml != '':
                root = ET.XML(accumulated_xml)
                while(int(root.get('simtime')) >= len(ues_time)):
                  ues_time.append([])
                coords_obj = root.findall(".//*[@class='inet::Coord']")
                #Supoe que a "lastPosition" seja o penultimo objeto com essa class inet::Coord
                coords_text = coords_obj[-2].find("./info").text
                coords_numbers = [float(s) for s in coords_text.split('(')[1].split(')')[0].split(', ') if s[0].isdigit()]
                coord = Coordinate(x= coords_numbers[0], y= coords_numbers[1], z= coords_numbers[2])
                #Supoe que a "lastVelocity" seja o ultimo objeto com essa class inet::Coord
                #lasVelocity diz a velocidade inicial do slice anterior
                speed_text = coords_obj[-1].find("./info").text
                speed_numbers = [float(s) for s in speed_text.split('(')[1].split(')')[0].split(', ') if s[0].isdigit() or (len(s) > 1 and s[0] == '-' and s[1].isdigit())]
                speed = sqrt(speed_numbers[0]**2 + speed_numbers[1]**2)
                direction = degrees(atan(speed_numbers[1]/speed_numbers[0]))
                mov = Movement(speed, direction)
                ues_time[int(root.get('simtime'))].append(Ue(coord, [int(s) for s in re.findall(r'\d+', root.get('object'))][-1]))
                ues_time[int(root.get('simtime'))-1][len(ues_time[int(root.get('simtime'))])-1].movement = mov

                accumulated_xml = ''
        else:
            accumulated_xml += line
      else:
        root = ET.XML(accumulated_xml)
        while(int(root.get('simtime')) >= len(ues_time)):
          ues_time.append([])
        coords_obj = root.findall(".//*[@class='inet::Coord']")
        #Supoe que a "lastPosition" seja o penultimo objeto com essa class inet::Coord
        coords_text = coords_obj[-2].find("./info").text
        coords_numbers = [float(s) for s in coords_text.split('(')[1].split(')')[0].split(', ') if s[0].isdigit()]
        coord = Coordinate(x= coords_numbers[0], y= coords_numbers[1], z= coords_numbers[2])
        #Supoe que a "lastVelocity" seja o ultimo objeto com essa class inet::Coord
        speed_text = coords_obj[-1].find("./info").text
        speed_numbers = [float(s) for s in speed_text.split('(')[1].split(')')[0].split(', ') if s[0].isdigit() or (len(s) > 1 and s[0] == '-' and s[1].isdigit())]
        speed = sqrt(speed_numbers[0]**2 + speed_numbers[1]**2)
        direction = degrees(atan(speed_numbers[1]/speed_numbers[0]))
        mov = Movement(speed, direction)
        ues_time[int(root.get('simtime'))].append(Ue(coord, [int(s) for s in re.findall(r'\d+', root.get('object'))][-1]))
        ues_time[int(root.get('simtime'))-1][len(ues_time[int(root.get('simtime'))])-1].movement = mov

        accumulated_xml = ''
        
        break

  return ues_time[:-1]