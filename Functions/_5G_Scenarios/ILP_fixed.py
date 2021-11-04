import numpy
import helper as hp
import random
import geometry as geo

def ilp_fixed_info(filename, seed, d_height:int =1000, d_width:int =1000, d_region:int =100):
  random.seed(seed)
  scen = start_scenario_chess(d_height, d_width, d_region)

  ues_x_y = scen.getUEsPositionList()
  regions_x_y = scen.getRegionsCentersList()

  with open(filename, 'wt') as f:
    hp.writeCommentConfigILP(f, "ilp_fixed_info", filename, seed, d_height, d_width, d_region)

    hp.defaultGeneral(f)
    hp.makeNewConfig(f, name= 'Config ilp_fixed_info')
    hp.writeNetwork(f, network= '_5G.networks.UrbanMacro5G')


def start_scenario_chess(d_height:int =1000, d_width:int =1000, d_region:int =100):

  scen = geo.MapChess(d_height, d_width, d_region)
  scen.placeTestUEs()

  return scen

def getMicroAntennasPositions(macrocells):
  positions = [[],[]]
  for m in macrocells:
    for s in m.smallcells:
      tmp = s.getAntennasPositionList()
      positions[0] += tmp[0]
      positions[1] += tmp[1]
  return positions