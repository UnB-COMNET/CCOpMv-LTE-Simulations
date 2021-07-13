import helper as hp
import random
import typing as ty

def main():

  filename = 'teste.ini'
  numUEs = 30
  directions = 2

  with open(filename, 'wt') as f:
    # General
    defaultGeneral(f)
    hp.makeNewConfig(f, name= 'Config Teste')
    hp.writeNetwork(f, network= 'networks.SimpleNet')
    hp.writeTime(f, time= 10, repeat= 10)
    hp.writeSeeds(f, num_rngs= 2, seeds= [123])
    hp.nl(f)
    hp.writeOutput(f, "${resultdir}/${configname}/${repetition}")
    hp.writeSeparation(f, "UEs")
    hp.writeComment(f, text= "Conecting UEs to eNodeB")
    hp.writeConnectUE(f, numENB= 1)
    hp.writeComment(f, text= "Scheduler")
    hp.writeSchedulingOptions(f, sched= ['MAXCI', 'DRR', 'PF', 'ALLOCATOR_BESTFIT'])
    hp.writeSeparation(f, "Mobility")
    hp.writeComment(f, text= "eNodeB")
    hp.writeIniMobility(f,object_name= 'eNB', iniX= 500, iniY= 500)
    hp.writeConstraint(f, object_name= 'eNB')
    hp.writeComment(f, text= "UEs")
    hp.writeNumUEs(f, numUEs)
    hp.nl(f)
    hp.writeUesMobilityType(f, type= "StationaryMobility")
    hp.writeUeMobilityPerso(f, number= numUEs, iniX=[100,300,300], iniY=[200,400,400], iniZ=[0,0,0])
    hp.writeConstraint(f, object_name= 'ue[*]')
    hp.writeSeparation(f, "Apps")
    hp.writeNumApps(f, numUEs= numUEs, directions= directions)
    hp.writeComment(f, text= "VoIP UL")
    hp.writeAppVoipUL(f, numUEs, n_app= 0)
    hp.writeComment(f, text= "VoIP DL")
    hp.writeAppVoipDL(f, numUEs, n_app= 1)
    hp.writeSeparation(f, "Channel Control")
    hp.writePropagation(f, model= "FreeSpaceModel")


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
  f.write("**.ueTxPower = 24\n**.eNodeBTxPower = 46\n")
  #Resource blocks
  hp.writeSeparation(f, "Resource Blocks")
  f.write('''**.numRbDl = 6\n**.numRbUl = 6
**.binder.numBands = 6 # this value should be kept equal to the number of RBs\n''')

if __name__ == "__main__":
  main()
  print("Done")