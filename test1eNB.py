from math import pi
import helper as hp
import random
import typing as ty
import numpy as np

import geometry as geo

def main():

  filename = 'teste.ini'
  directions = 2
  center = geo.Coordinate(500,500)
  numUEs = 30
  random.seed(123)
  scen = startSimpleScenario(numUEs, center)
  pos_macrocell = (scen.macrocells[0].center.x, scen.macrocells[0].center.y)
  pos_microcell = (scen.macrocells[0].smallcells[0].center.x, scen.macrocells[0].smallcells[0].center.y)

  with open(filename, 'wt') as f:
    # General

    defaultGeneral(f)
    hp.makeNewConfig(f, name= 'Config Teste')
    hp.writeNetwork(f, network= 'networks.UrbanMacro')
    hp.writeTime(f, time= 10, repeat= 10)
    hp.writeSeeds(f, num_rngs= 2, seeds= [123])
    hp.nl(f)
    hp.writeOutput(f, "${resultdir}/${configname}/${sched}-${repetition}")
    hp.writeSeparation(f, "Micro Cell")
    hp.writeNodeIsMicro(f, "microCell")
    hp.writeSeparation(f, "Transmission Power")
    hp.writeTransmissionPower(f)
    hp.writeSeparation(f, "UEs")
    hp.writeNumUEs(f, scen.n_ues)
    hp.writeComment(f, text= "Conecting UEs to eNodeB")
    hp.writeConnectUE(f, numUEs= numUEs, ENBs= [1])
    hp.writeComment(f, text= "Scheduler")
    hp.writeSchedulingOptions(f, sched= ['MAXCI', 'DRR', 'PF', 'ALLOCATOR_BESTFIT'])
    hp.writeSeparation(f, "Mobility")
    hp.writeComment(f, text= "eNodeB")
    hp.writeIniMobility(f,object_name= 'eNB', iniX= pos_macrocell[0], iniY= pos_macrocell[1])
    hp.writeConstraint(f, object_name= 'eNB')
    hp.writeComment(f, text= "UEs")
    hp.nl(f)    
    hp.writeUesMobilityType(f, type= "StationaryMobility")
    hp.writeUeMobilityPerso(f, map= scen)
    hp.writeConstraint(f, object_name= 'ue[*]')
    hp.writeComment(f, text= "Micro-cell")
    hp.writeIniMobility(f,object_name= 'microCell', iniX= pos_microcell[0], iniY= pos_microcell[1])
    hp.writeConstraint(f, object_name= 'microCell')
    hp.writeSeparation(f, "Apps")
    hp.writeNumApps(f, numUEs= scen.n_ues, directions= directions)
    hp.writeComment(f, text= "VoIP UL")
    hp.writeAppVoipUL(f, scen.n_ues, n_app= 0)
    hp.writeComment(f, text= "VoIP DL")
    hp.writeAppVoipDL(f, scen.n_ues, n_app= 1)
    hp.writeSeparation(f, "Channel Control")
    hp.writePropagation(f, model= "LogNormalShadow")
'''   
def main():
  geo.startScenario()

  None
'''
def defaultGeneral(f):
  # General
  f.write("[General]\n")
  #Time
  f.write("sim-time-limit = 10s\n")
  # Statistics
  f.write('\n' + hp.separation + " Statistics " + hp.separation + '\n')
  hp.writeOutput(f, "${resultdir}/${configname}/${repetition}")
  f.write("seed-set = ${repetition}\n")
  #Transmission power
  hp.writeSeparation(f, "Transmission Power")
  f.write("**.ueTxPower = 24\n**.eNodeBTxPower = 46\n**.microTxPower = 30\n")
  #Resource blocks
  hp.writeSeparation(f, "Resource Blocks")
  f.write('''**.numRbDl = 6\n**.numRbUl = 6
**.binder.numBands = 6 # this value should be kept equal to the number of RBs\n''')

def startSimpleScenario(numUEs, center):

  scen = geo.MapHexagonal(center)
  scen.n_site = 1
  scen.macrocells = scen.macrocells[0:1]
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



if __name__ == "__main__":
  main()
  print("Done")
