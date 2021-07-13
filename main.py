import helper as hp
import random

def main():

  filename = 'teste.ini'

  with open(filename, 'wt') as f:
    # General
    defaultGeneral(f)
    makeNewConfig(f, name= 'Config Teste')
    writeNetwork(f, network= 'networks.SimpleNet')
    writeTime(f, time= 10, repeat= 10)
    writeSeeds(f, num_rngs= 2, seeds= [123])
    nl(f)
    writeOutput(f, "${resultdir}/${configname}/${repetition}")
    writeSeparation(f, "UEs")
    writeComment(f, text= "Conecting UEs to eNodeB")
    writeConnectUE(f, numENB= 1)
    writeComment(f, text= "Scheduler")
    writeSchedulingOptions(f, sched= ['MAXCI', 'DRR', 'PF', 'ALLOCATOR_BESTFIT'])
    writeSeparation(f, "Mobility")
    writeComment(f, text= "eNodeB")
    writeIniMobility(f,object_name= 'eNB', iniX= 500, iniY= 500)
    writeConstraint(f, object_name= 'eNB')
    writeComment(f, text= "UEs")
    writeUesMobilityType(f, type= "StationaryMobility")
    writeIniMobility(f,object_name= 'ue[*]', iniX= 500, iniY= 500)
    writeConstraint(f, object_name= 'ue[*]')

def nl(f):
  f.write('\n')

def defaultGeneral(f):
  # General
  f.write("[General]\n")
  #Time
  f.write("sim-time-limit = 10s\n")
  # Statistics
  f.write('\n' + hp.separation + " Statistics " + hp.separation + '\n')
  writeOutput(f, "${resultdir}/${configname}/${repetition}")
  f.write("seed-set = ${repetition}\n**.vector-recording = false\n")
  #Transmission power
  writeSeparation(f, "Transmission Power")
  f.write("**.ueTxPower = 24\n**eNodeBTxPower = 46\n")
  #Resource blocks
  writeSeparation(f, "Resource Blocks")
  f.write('''**.numRbDl = 6\n**.numRbUl = 6
**.binder.numBands = 6 # this value should be kept equal to the number of RBs\n''')

def writeSeparation(f, name):
  f.write('\n' + hp.separation + ' ' + name + ' ' + hp.separation + '\n')
  
def makeNewConfig(f,name, extends = False, extend_name = ''):
  f.write('\n[{}]\n'.format(name))
  if extends:
    f.write('extends = {}\n'.format(extend_name))

def writeOutput(f, path, vector_rec=False):
  f.write('''output-scalar-file = {}.sca
output-vector-file = {}.vec
**.vector-recording = {}\n'''.format(path, path, vector_rec))

def writeTime(f, time, repeat):
  f.write("sim-time-limit = {}s\nrepeat = {}\n".format(time, repeat))

def writeNetwork(f, network):
  f.write("network = {}\n".format(network))

def writeConnectUE(f, numENB = 1):
  f.write("**.ue[*].macCellId = {}\n**.ue[*].masterId = {}\n".format(numENB, numENB))

def writeComment(f, text):
  f.write("\n# {}\n".format(text))

def writeUesMobilityType(f, type):
  f.write('*.ue[*].mobilityType = "{}"\n'.format(type))

def writeIniMobility(f, object_name, iniX, iniY, display = False):
  f.write('''*.{name}.mobility.initialX = {iniX}m
*.{name}.mobility.initialY = {iniY}m
*.{name}.mobility.initFromDisplayString = {display}
'''.format(name= object_name, iniX = iniX, iniY = iniY, display = display))

def writeConstraint(f, object_name, maxX= '+inf', maxY= '+inf', maxZ= '+inf', 
                    minX= '-inf', minY= '-inf', minZ= '-inf'):
  f.write('''*.{name}.mobility.constraintAreaMaxX = {maxX} m
*.{name}.mobility.constraintAreaMaxY = {maxY} m
*.{name}.mobility.constraintAreaMaxZ = {maxZ} m
*.{name}.mobility.constraintAreaMinX = {minX} m
*.{name}.mobility.constraintAreaMinY = {minY} m
*.{name}.mobility.constraintAreaMinZ = {minZ} m
'''.format(name = object_name, maxX = maxX, maxY = maxY, maxZ = maxZ, 
          minX = minX, minY = minY, minZ = minZ))

# seeds deve ser uma lista de inteiros
def writeSeeds(f, seed_set = "${repetition}", num_rngs = 1, seeds = []):
  f.write("seed-set = {}\nnum-rngs = {}\n".format(seed_set, num_rngs))
  if num_rngs > 1 and len(seeds) >= num_rngs - 1:
    for i in range(1, num_rngs):
      f.write("seed-{}-mt = {}\n".format(i, seeds[i-1]))

def writeSchedulingOptions(f, sched: list):
  f.write('**.schedulingDisciplineUl = ${sched=')
  temp = ''
  for s in sched:
    temp += ' "' + s + '",'
  f.write(temp[:-1] + '}\n**.schedulingDisciplineDl = ${sched}\n')

if __name__ == "__main__":
  main()
  print("Done")