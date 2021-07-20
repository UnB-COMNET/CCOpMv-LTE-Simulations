import helper as hp
import random
import typing as ty
import numpy as np

import geometry as geo

def main():

  filename = 'teste.ini'
  numUEs = 30
  directions = 2
  pos_macrocell = (500,500)
  random.seed(123)

  with open(filename, 'wt') as f:
    # General
    defaultGeneral(f)
    hp.makeNewConfig(f, name= 'Config Teste')
    hp.writeNetwork(f, network= 'networks.UrbanMacro')
    hp.writeTime(f, time= 10, repeat= 10)
    hp.writeSeeds(f, num_rngs= 2, seeds= [123])
    hp.nl(f)
    hp.writeOutput(f, "${resultdir}/${configname}/${sched}-${repetition}")
    hp.writeSeparation(f, "Transmission Power")
    hp.writeTransmissionPower(f)
    hp.writeSeparation(f, "UEs")
    hp.writeNumUEs(f, numUEs)
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
    pos_hotspot, pos_ues = genUEsPos(numUEs, pos_macrocell)
    hp.writeUesMobilityType(f, type= "StationaryMobility")
    hp.writeUeMobilityPerso(f, number= numUEs, iniX= [x for x,y in pos_ues], iniY=[y for x,y in pos_ues], iniZ=np.zeros(len(pos_ues)))
    hp.writeConstraint(f, object_name= 'ue[*]')
    hp.writeComment(f, text= "Micro-cell")
    hp.writeIniMobility(f,object_name= 'microCell', iniX= pos_hotspot[0], iniY= pos_hotspot[1])
    hp.writeConstraint(f, object_name= 'microCell')
    hp.writeSeparation(f, "Apps")
    hp.writeNumApps(f, numUEs= numUEs, directions= directions)
    hp.writeComment(f, text= "VoIP UL")
    hp.writeAppVoipUL(f, numUEs, n_app= 0)
    hp.writeComment(f, text= "VoIP DL")
    hp.writeAppVoipDL(f, numUEs, n_app= 1)
    hp.writeSeparation(f, "Channel Control")
    hp.writePropagation(f, model= "LogNormalShadow")

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

def genUEsPos(numUEs, pos_macrocell):
  result = []
  pos_hotspot = dropObject(pos_macrocell, 425, 105)
  for n in range(numUEs):
    if random.random() < 0.6666:
      result.append(dropObject(pos_hotspot, 70, 0))
    else:
      result.append(dropObject(pos_macrocell, 425, 35)) #425
  return pos_hotspot, result

def dropObject(center: tuple, radius, min_distance):
  not_done = True
  while not_done:
    radius_ue = radius * np.sqrt(random.random())
    theta_ue = 2 * np.pi * random.random()
    result = (radius_ue*np.cos(theta_ue) + center[0], radius_ue*np.sin(theta_ue) + center[1])
    not_done = np.linalg.norm(np.array(result) - np.array(center)) < min_distance #distancia euclidiana
  return result

if __name__ == "__main__":
  main()
  print("Done")