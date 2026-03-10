from math import atan, sqrt, degrees
from typing import List

from app.core.geometry import Ue, Movement
from app.core.coordinates import Coordinate
from app.core.geometry import MapChess
import xml.etree.ElementTree as ET
import re

def get_map_ues_time(scen: MapChess, xml_filename: str, ues_per_slice: list) -> List[List[int]]:
  """This function parses a snapshot file (.sna) returning quantity of UEs in the map sections over time."""

  ues_in_time = get_ues_time(scen, xml_filename)
  map_ues_time = []
  
  for i in range(len(ues_in_time)):
    map_ues_time.append(scen.n_sectors*[0])
  
  for slice in range(len(ues_in_time)):
    for ue in ues_per_slice[slice]:
      coord = Coordinate(x = ues_in_time[slice][ue].position.x, y = ues_in_time[slice][ue].position.y)
      region = scen.coord2Region(coord)
      map_ues_time[slice][region] += 1
       
  # Verifying
  for i in range(len(ues_per_slice)):
    if len(ues_per_slice[i]) != sum(map_ues_time[i]):
      print("ERROR in get_map_ues_time")
      return None
    
  return map_ues_time

def get_ues_time(scen: MapChess, xml_filename: str) -> List[List[Ue]]:
  """This function parses a snapshot file (.sna) returning the UEs location over time (matrix)."""
  ue_target = 0
  accumulated_xml = ''
  ues_time: List[List[Ue]] = []
  
  simtime_slice = int(scen.simulation_config.simtime_move/scen.simulation_config.num_slices)
  num_slices = scen.simulation_config.num_slices

  last_simTime = 1*simtime_slice
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

            while (int(root.get('simtime'))/(1*simtime_slice) > len(ues_time)):
              ues_time.append([])
            
            cPar_obj = root.findall(".//*[@class='omnetpp::cPar']")

            startTime_text = cPar_obj[-6].find("./info").text              
            startTime_text = startTime_text.split('s')[0]

            initialX_text = cPar_obj[-11].find("./info").text
            initialX = float(initialX_text.split('m')[0])

            initialY_text = cPar_obj[-10].find("./info").text
            initialY = float(initialY_text.split('m')[0])
            
            coords_obj = root.findall(".//*[@class='inet::Coord']")

            #Supoe que a "lastPosition" seja o quarto ultimo objeto com essa class inet::Coord
            coords_text = coords_obj[-4].find("./info").text
            coords_numbers = [float(s) for s in coords_text.split('(')[1].split(')')[0].split(', ') if s[0].isdigit()]
            coord = Coordinate(x= coords_numbers[0], y= coords_numbers[1], z= coords_numbers[2])
            
            #Supoe que a "initialSpeed" seja o ultimo objeto com essa class inet::Coord
            initial_speed_text = coords_obj[-1].find("./info").text                  
            initial_speed_numbers = [float(s) for s in initial_speed_text.split('(')[1].split(')')[0].split(', ') if s[0].isdigit() or (len(s) > 1 and s[0] == '-' and s[1].isdigit())]
            initial_speed = sqrt(initial_speed_numbers[0]**2 + initial_speed_numbers[1]**2)

            #Supoe que a "initialSpeedLastSlice" seja o terceiro ultimo objeto com essa class inet::Coord
            initial_speed_last_slice_text = coords_obj[-3].find("./info").text                  
            initial_speed_last_slice_numbers = [float(s) for s in initial_speed_last_slice_text.split('(')[1].split(')')[0].split(', ') if s[0].isdigit() or (len(s) > 1 and s[0] == '-' and s[1].isdigit())]
            initial_speed_last_slice = sqrt(initial_speed_last_slice_numbers[0]**2 + initial_speed_last_slice_numbers[1]**2)
            
            if int(root.get('simtime')) == 1*simtime_slice:
              speed_numbers = initial_speed_numbers
              speed = initial_speed
            else:
              speed_numbers = initial_speed_last_slice_numbers
              speed = initial_speed_last_slice
            
            index = [int(s) for s in re.findall(r'\d+', root.get('object'))]

            try:
              direction = degrees(atan(speed_numbers[1]/speed_numbers[0]))  #FIXME
              # if velocity  vector is 2th or 3h quadrant
              if speed_numbers[0] < 0:
                direction += 180
              
            except ZeroDivisionError:
              direction = degrees(0)

            mov = Movement(speed, direction,int(startTime_text))
            ue = Ue(coord, index = [int(s) for s in re.findall(r'\d+', root.get('object'))][-1])
            index = [int(s) for s in re.findall(r'\d+', root.get('object'))][-1]

            ues_time[int(int(root.get('simtime'))/(1*simtime_slice))-1].append(ue)
            ues_time[int(int(root.get('simtime'))/(1*simtime_slice))-1][-1].movement = mov  
            
            if int(root.get('simtime')) >= 2*simtime_slice:
              tmp = ues_time[int(int(root.get('simtime'))/(1*simtime_slice))-1][index].position
              ues_time[int(int(root.get('simtime'))/(1*simtime_slice))-1][index].position = ues_time[0][index].position
              ues_time[0][index].position = tmp

              if int(root.get('simtime')) == (num_slices*simtime_slice):
                ues_time[0][index].position = Coordinate(initialX, initialY)                
                
            ue_target += 1
            accumulated_xml = ''
        elif not line.startswith('<!--'):#Not a comment
            accumulated_xml += line
      else:
        root = ET.XML(accumulated_xml)

        current_simTime = int(root.get('simtime'))
        if current_simTime != last_simTime:
          ue_target = 0

        cPar_obj = root.findall(".//*[@class='omnetpp::cPar']")

        startTime_text = cPar_obj[-6].find("./info").text              
        startTime_text = startTime_text.split('s')[0]

        initialX_text = cPar_obj[-11].find("./info").text
        initialX = float(initialX_text.split('m')[0])

        initialY_text = cPar_obj[-10].find("./info").text
        initialY = float(initialY_text.split('m')[0])

        coords_obj = root.findall(".//*[@class='inet::Coord']")

        #Supoe que a "lastPosition" seja o quarto ultimo objeto com essa class inet::Coord
        coords_text = coords_obj[-4].find("./info").text
        coords_numbers = [float(s) for s in coords_text.split('(')[1].split(')')[0].split(', ') if s[0].isdigit()]
        coord = Coordinate(x= coords_numbers[0], y= coords_numbers[1], z= coords_numbers[2])
        
        #Supoe que a "initialSpeed" seja o ultimo objeto com essa class inet::Coord
        initial_speed_text = coords_obj[-1].find("./info").text                  
        initial_speed_numbers = [float(s) for s in initial_speed_text.split('(')[1].split(')')[0].split(', ') if s[0].isdigit() or (len(s) > 1 and s[0] == '-' and s[1].isdigit())]
        initial_speed = sqrt(initial_speed_numbers[0]**2 + initial_speed_numbers[1]**2)

        #Supoe que a "initialSpeedLastSlice" seja o terceiro ultimo objeto com essa class inet::Coord
        initial_speed_last_slice_text = coords_obj[-3].find("./info").text                  
        initial_speed_last_slice_numbers = [float(s) for s in initial_speed_last_slice_text.split('(')[1].split(')')[0].split(', ') if s[0].isdigit() or (len(s) > 1 and s[0] == '-' and s[1].isdigit())]
        initial_speed_last_slice = sqrt(initial_speed_last_slice_numbers[0]**2 + initial_speed_last_slice_numbers[1]**2)
        
        if int(root.get('simtime')) == 1*simtime_slice:
          speed_numbers = initial_speed_numbers
          speed = initial_speed
        else:
          speed_numbers = initial_speed_last_slice_numbers
          speed = initial_speed_last_slice

        try:
          direction = degrees(atan(speed_numbers[1]/speed_numbers[0]))  #FIXME
          if speed_numbers[0] < 0:
            direction += 180
        except ZeroDivisionError:
          direction = degrees(0)

        mov = Movement(speed, direction,int(startTime_text))
        ue = Ue(coord, index = [int(s) for s in re.findall(r'\d+', root.get('object'))][-1])
        index = [int(s) for s in re.findall(r'\d+', root.get('object'))][-1]

        ues_time[int(int(root.get('simtime'))/(1*simtime_slice))-1].append(ue)
        ues_time[int(int(root.get('simtime'))/(1*simtime_slice))-1][-1].movement = mov  
      
        if int(root.get('simtime')) >= 2*simtime_slice:
          tmp = ues_time[int(int(root.get('simtime'))/(1*simtime_slice))-1][index].position
          ues_time[int(int(root.get('simtime'))/(1*simtime_slice))-1][index].position = ues_time[0][index].position
          ues_time[0][index].position = tmp

          if int(root.get('simtime')) == (num_slices*simtime_slice):
            ues_time[0][index].position = Coordinate(initialX, initialY)                

        accumulated_xml = ''
        
        break
      
      last_simTime = current_simTime
  
  return ues_time