import sys
sys.path.append("..")

import helper as hp
import random
import geometry as geo

def main():

  filename = '../../Network_CCOpMv/LTE/simulations/eNB2_1.ini'#'Network_CCOpMv/simulations/eNB2_60.ini'
  directions = 2
  center = geo.Coordinate(425*7/2,425*7/2)
  numUEs = 1#60
  random.seed(123)
  scen = startScenario(numUEs, center)
  num_macros = len(scen.macrocells)
  microPositions = getMicroPositions(scen.macrocells)

  with open(filename, 'wt') as f:
    # General

    hp.defaultGeneral(f)
    hp.makeNewConfig(f, name= 'Config eNB2_Base')
    hp.writeNetwork(f, network= 'LTE.networks.UrbanMacro7')
    hp.writeTime(f, time= 10, repeat= 10)
    hp.writeSeeds(f, num_rngs= 2, seeds= [123])
    hp.nl(f)
    hp.writeOutput(f, "${resultdir}/${configname}/${sched}-${repetition}")
    hp.writeSeparation(f, "Micro Cell")
    hp.writeMultiMicro(f, number= 7)
    hp.writeSeparation(f, "Transmission Power")
    hp.writeTransmissionPower(f)
    hp.writeSeparation(f, "UEs")
    hp.writeNumUEs(f, scen.n_ues)
    hp.writeComment(f, text= "Conecting UEs to eNodeB")
    hp.writeConnectMultiUE(f, scen.macrocells)
    hp.writeComment(f, text= "Scheduler")
    hp.writeSchedulingOptions(f, sched= ['MAXCI', 'DRR', 'PF'])
    hp.writeSeparation(f, "Scenario")
    hp.writeComment(f, text= "eNodeB")
    hp.writeMultiScenarios(f, object_name= 'eNB', num= num_macros, scenario= 'URBAN_MACROCELL')
    hp.writeComment(f, text= "Microcell")
    hp.writeMultiScenarios(f, object_name= 'microCell', num = num_macros, scenario= 'URBAN_MICROCELL')
    hp.writeComment(f, text= "UEs")
    hp.writeMultiScenariosPerso(f, macrocells= scen.macrocells)
    hp.writeSeparation(f, "Mobility")
    hp.writeComment(f, text= "eNodeB")
    hp.writeMultiIniMobility(f,object_name= 'eNB', coordenates= scen.getMacrocellsPositionList())
    hp.writeConstraint(f, object_name= 'eNB*')
    hp.writeComment(f, text= "UEs")
    hp.nl(f)
    hp.writeMobilityType(f, type= "StationaryMobility", object_name= "ue*[*]")
    hp.writeUeMobilityPerso(f, scen= scen, multi= True)
    hp.writeConstraint(f, object_name= 'ue*[*]')
    hp.writeComment(f, text= "Microcell")
    hp.writeMultiIniMobility(f,object_name= 'microCell', coordenates= microPositions)
    hp.writeConstraint(f, object_name= 'microCell*')
    hp.writeSeparation(f, "Apps")
    hp.writeNumApps(f, numUEs= scen.n_ues, directions= directions, num_macros= num_macros, multi= True)
    hp.writeComment(f, text= "VoIP UL")
    hp.writeMultiAppVoipUL(f, numUEs= scen.n_ues, num_macros= num_macros, number_app= 0)
    hp.writeComment(f, text= "VoIP DL")
    hp.writeMultiAppVoipDL(f, numUEs= scen.n_ues, num_macros= num_macros, number_app= 1, num_apps = 2)
    hp.writeSeparation(f, "Channel Control")
    hp.writePropagation(f, model= "LogNormalShadow")

  #geo.plotMap(scen, False, 7)

def startScenario(numUEs, center):

  scen = geo.MapHexagonal(center)
  scen.n_ues = numUEs

  for i in range(len(scen.macrocells)):
    # For each macrocell, it places the smallcells
    scen.placeSmallCell(scen.macrocells[i], scen.d_macromacro*0.425, scen.d_macrocluster)
    # For each smallcell in a given macrocell, it places the antennas
    position = scen.macrocells[i].getSmallcellsPositionList()
    antenna = geo.Antenna(geo.Coordinate(position[0][0], position[1][0]), None)
    scen.macrocells[i].smallcells[0].antennas.append(antenna)          

  scen.placeUEs()

  return scen

def getMicroPositions(macrocells):
  positions = [[],[]]
  for m in macrocells:
    tmp = m.getSmallcellsPositionList()
    positions[0] += tmp[0]
    positions[1] += tmp[1]
  return positions

if __name__ == "__main__":
  main()
  print("Done")