import typing as ty

separation = "###############"

def nl(f):
  f.write('\n')

def writeSeparation(f, name):
  f.write('\n' + separation + ' ' + name + ' ' + separation + '\n')
  
def makeNewConfig(f,name, extends = False, extend_name = ''):
  f.write('\n[{}]\n'.format(name))
  if extends:
    f.write('extends = {}\n'.format(extend_name))

def writeOutput(f, path, vector_rec=False):
  f.write('''output-scalar-file = {}.sca
output-vector-file = {}.vec
**.vector-recording = {}\n'''.format(path, path, 'true' if vector_rec else 'false'))

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

def writeIniMobility(f, object_name, iniX, iniY, iniZ: ty.Union[str, int] = 0, display = False):
  f.write('''*.{name}.mobility.initialX = {iniX}m
*.{name}.mobility.initialY = {iniY}m
*.{name}.mobility.initialZ = {iniZ}m
*.{name}.mobility.initFromDisplayString = {display}
'''.format(name= object_name, iniX = iniX, iniY = iniY, iniZ = iniZ, display = 'true' if display else 'false'))

def writeUeMobilityPerso(f, number, iniX: list, iniY: list, iniZ: list, display = False):
  for i in range(len(iniX)):
    for l in range(int(number/len(iniX))):
      f.write('''*.ue[{number}].mobility.initialX = {iniX}m
*.ue[{number}].mobility.initialY = {iniY}m
*.ue[{number}].mobility.initialZ = {iniZ}m
'''.format(number = int(i*number/len(iniX)) + l, iniX = iniX[i], iniY = iniY[i], iniZ = iniZ[i]))

  dif = number - len(iniX)*int(number/len(iniX))
  if dif != 0:
    for i in range(number-dif, number):
      f.write('''*.ue[{number}].mobility.initialX = {iniX}m
*.ue[{number}].mobility.initialY = {iniY}m\n'''.format(number = i, iniX = iniX[-1], iniY = iniY[-1]))

  f.write("*.ue[*].mobility.initFromDisplayString = {display}\n".format(display = 'true' if display else 'false'))

def writeConstraint(f, object_name, maxX = 'inf', maxY= 'inf', maxZ= 'inf', 
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

def writeNumApps(f, numUEs, directions):
  f.write('''*.ue[*].numApps = {directions}
*.server.numApps = {directions} * {numUEs}\n'''.format(directions = directions, numUEs = numUEs))

def writeAppVoipUL(f, numUEs, n_app = 0):
  f.write('''*.ue[*].app[{n}].typename="VoIPSender"
*.ue[*].app[{n}].PacketSize = default
*.ue[*].app[{n}].destAddress = "server"
*.ue[*].app[{n}].destPort = 4000 + ancestorIndex(1) #Pega o valor id de ue
*.ue[*].app[{n}].localPort = 4088
*.ue[*].app[{n}].startTime = 0.01s\n'''.format(n = n_app))
  f.write('''*.server.app[{n}..{f}].typename="VoIPReceiver"
*.server.app[{n}..{f}].localPort = 4000 + ancestorIndex(0)\n'''.format(n = n_app * numUEs, f = numUEs*(n_app+1) - 1))

def writeAppVoipDL(f, numUEs, n_app = 0):
  f.write('''*.server.app[{n}..{f}].typename="VoIPSender"
*.server.app[{n}..{f}].PacketSize = default
*.server.app[{n}..{f}].destAddress = "ue[" + string(ancestorIndex(0) - {numUEs}) + "]"
*.server.app[{n}..{f}].destPort = 3000
*.server.app[{n}..{f}].localPort = 3088 + ancestorIndex(0)
*.server.app[{n}..{f}].startTime = 0.01s\n'''.format(numUEs = numUEs, n = n_app * numUEs, f = numUEs*(n_app+1) - 1))
  f.write('''*.ue[*].app[{n}].typename="VoIPReceiver"
*.ue[*].app[{n}].localPort = 4000 + ancestorIndex(0)\n'''.format(n = n_app))

def writeNumUEs(f, numUEs):
  f.write("**.numUe = {}\n".format(numUEs))

def writePropagation(f, model):
  f.write('**.propagationModel = "{}"\n'.format(model))