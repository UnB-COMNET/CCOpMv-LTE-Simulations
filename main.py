import helper as hp

def main():

  filename = 'teste.ini'

  with open(filename, 'wt') as f:
    # General
    f.write("[General]\n")
    defaultGeneral(f)

def defaultGeneral(f):
  # Statistics
  f.write('\n' + hp.separation + " Statistics " + hp.separation + '\n')
  f.write('''output-scalar-file = ${resultdir}/${configname}/${repetition}.sca
output-scalar-file = ${resultdir}/${configname}/${repetition}.vec\n''')
  f.write("seed-set = ${repetition}\n**.vector-recording = false\n")
  #Transmission power
  writeSeparation("Transmission Power", f)
  f.write("**.ueTxPower = 24\n**eNodeBTxPower = 46\n")
  #Resource blocks
  writeSeparation("Resource Blocks", f)
  f.write('''**.numRbDl = 6\n**.numRbUl = 6
**.binder.numBands = 6 # this value should be kept equal to the number of RBs''')

def writeSeparation(name, f):
  f.write('\n' + hp.separation + ' ' + name + ' ' + hp.separation + '\n')

if __name__ == "__main__":
  main()
  print("Done")