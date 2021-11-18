from typing import List
from coordinates import Coordinate
from geometry import MapChess
import xml.etree.ElementTree as ET

def get_map_ues_time(scen: MapChess, xml_filename: str) -> List[List[int]]:
  accumulated_xml = ''
  map_ues_time = [[len(region) for region in scen.map_ues]]
  coords_objs = []

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
                coords_text = coords_obj[-1].find("./info").text
                coords_numbers = [float(s) for s in coords_text.split('(')[1].split(')')[0].split(', ') if s[0].isdigit()]
                #print(coords_text.split('(')[1].split(')')[0].split(', '))
                coord = Coordinate(x= coords_numbers[0], y= coords_numbers[1], z= coords_numbers[2])
                #Supoe que a "lastPosition" seja o ultimo objeto com essa classe
                map_ues_time[int(root.get('simtime'))][scen.coord2Region(coord)] += 1
                accumulated_xml = ''
        else:
            accumulated_xml += line
      else:
        root = ET.XML(accumulated_xml)
        while(int(root.get('simtime')) >= len(map_ues_time)):
          map_ues_time.append([])
        map_ues_time[int(root.get('simtime'))].append(0)
        accumulated_xml = ''
        
        break

  return map_ues_time