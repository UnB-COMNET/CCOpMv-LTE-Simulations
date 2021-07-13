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
    nl(f)
    writeSeparation(f, "UEs")
    writeComment(f, text= "Conecting UEs to eNodeB")
    writeConnectUE(f, numENB= 1)

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

# seeds deve ser uma lista de inteiros
def writeSeeds(f, seed_set = "${repetition}", num_rngs = 1, seeds = []):
  f.write("seed-set = {}\nnum-rngs = {}\n".format(seed_set, num_rngs))
  if num_rngs > 1 and len(seeds) >= num_rngs - 1:
    for i in range(1, num_rngs):
      f.write("seed-{}-mt = {}\n".format(i, seeds[i-1]))


if __name__ == "__main__":
  main()
  print("Done")