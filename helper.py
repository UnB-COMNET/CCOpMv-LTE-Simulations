from geometry import MapHexagonal
import typing as ty
import numpy as np

separation = "###############"

def nl(f):
  f.write('\n')

def writeSeparation(f, name):
  f.write('\n' + separation + ' ' + name + ' ' + separation + '\n')
  
def makeNewConfig(f,name, extends = False, extend_name = ''):
  f.write('\n[{}]\n'.format(name))
  if extends:
    f.write('extends = {}\n'.format(extend_name))

def writeOutput(f, path: str, vector_rec: bool = False):
  f.write('''output-scalar-file = {}.sca
output-vector-file = {}.vec
**.vector-recording = {}\n'''.format(path, path, 'true' if vector_rec else 'false'))

def writeTime(f, time: int, repeat: int):
  f.write("sim-time-limit = {}s\nrepeat = {}\n".format(time, repeat))

def writeNetwork(f, network: str):
  f.write("network = {}\n".format(network))

def writeConnectUE(f, numUEs: int, ENBs : ty.List[int] = [1]):
  count = 0
  for i in range(len(ENBs)):
    for l in range(ENBs[i]):
      if count < numUEs:
        f.write('''**.ue[{number}].macCellId = {enb}
**.ue[{number}].masterId = {enb}\n'''.format(number = count, enb = i+1))
        count += 1
      else:
        break

  dif = numUEs - count
  if dif != 0:
    for i in range(numUEs-dif, numUEs):
      f.write('''**.ue[{number}].macCellId = {enb}
**.ue[{number}].masterId = {enb}\n'''.format(number = i, enb = len(ENBs)))

def writeComment(f, text):
  f.write("\n# {}\n".format(text))

def writeUesMobilityType(f, type: str):
  f.write('*.ue[*].mobilityType = "{}"\n'.format(type))

def writeIniMobility(f, object_name, iniX: float, iniY: float, iniZ: ty.Union[str, float] = 0, display = False):
  f.write('''*.{name}.mobility.initialX = {iniX}m
*.{name}.mobility.initialY = {iniY}m
*.{name}.mobility.initialZ = {iniZ}m
*.{name}.mobility.initFromDisplayString = {display}
'''.format(name= object_name, iniX = iniX, iniY = iniY, iniZ = iniZ, display = 'true' if display else 'false'))

def writeUeMobilityPerso(f, map: MapHexagonal, display: bool = False):
  number = map.n_ues
  iniZ=np.zeros(map.n_ues)
  [iniX, iniY] = map.macrocells[0].getUEsPositionList()
  [iniX_smallcell, iniY_smallcell] = map.macrocells[0].smallcells[0].getUEsPositionList()
  iniX = iniX + iniX_smallcell
  iniY = iniY + iniY_smallcell
  pass
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

def writeConstraint(f, object_name, maxX: ty.Union[str, float] = 'inf', maxY: ty.Union[str, float] = 'inf',
                    maxZ: ty.Union[str, float] = 'inf', minX: ty.Union[str, float] = '-inf',
                    minY: ty.Union[str, float] = '-inf', minZ: ty.Union[str, float] = '-inf'):

  f.write('''*.{name}.mobility.constraintAreaMaxX = {maxX} m
*.{name}.mobility.constraintAreaMaxY = {maxY} m
*.{name}.mobility.constraintAreaMaxZ = {maxZ} m
*.{name}.mobility.constraintAreaMinX = {minX} m
*.{name}.mobility.constraintAreaMinY = {minY} m
*.{name}.mobility.constraintAreaMinZ = {minZ} m
'''.format(name = object_name, maxX = maxX, maxY = maxY, maxZ = maxZ, 
          minX = minX, minY = minY, minZ = minZ))

# seeds deve ser uma lista de inteiros
def writeSeeds(f, seed_set: ty.Union[str, int] = "${repetition}", num_rngs: int = 1, seeds: ty.List[int] = []):
  f.write("seed-set = {}\nnum-rngs = {}\n".format(seed_set, num_rngs))
  if num_rngs > 1 and len(seeds) >= num_rngs - 1:
    for i in range(1, num_rngs):
      f.write("seed-{}-mt = {}\n".format(i, seeds[i-1]))

def writeSchedulingOptions(f, sched: ty.List[str]):
  f.write('**.schedulingDisciplineUl = ${sched=')
  temp = ''
  for s in sched:
    temp += ' "' + s + '",'
  f.write(temp[:-1] + '}\n**.schedulingDisciplineDl = ${sched}\n')

def writeNumApps(f, numUEs: int, directions: int):
  f.write('''*.ue[*].numApps = {directions}
*.server.numApps = {directions} * {numUEs}\n'''.format(directions = directions, numUEs = numUEs))

def writeAppVoipUL(f, numUEs: int, n_app: int = 0):
  f.write('''*.ue[*].app[{n}].typename="VoIPSender"
*.ue[*].app[{n}].PacketSize = default
*.ue[*].app[{n}].destAddress = "server"
*.ue[*].app[{n}].destPort = 4000 + ancestorIndex(1) #Pega o valor id de ue
*.ue[*].app[{n}].localPort = 4088
*.ue[*].app[{n}].startTime = 0.01s\n'''.format(n = n_app))
  f.write('''*.server.app[{n}..{f}].typename="VoIPReceiver"
*.server.app[{n}..{f}].localPort = 4000 + ancestorIndex(0)\n'''.format(n = n_app * numUEs, f = numUEs*(n_app+1) - 1))

def writeAppVoipDL(f, numUEs: int, n_app: int = 0):
  f.write('''*.server.app[{n}..{f}].typename="VoIPSender"
*.server.app[{n}..{f}].PacketSize = default
*.server.app[{n}..{f}].destAddress = "ue[" + string(ancestorIndex(0) - {numUEs}) + "]"
*.server.app[{n}..{f}].destPort = 3000
*.server.app[{n}..{f}].localPort = 3088 + ancestorIndex(0)
*.server.app[{n}..{f}].startTime = 0.01s\n'''.format(numUEs = numUEs, n = n_app * numUEs, f = numUEs*(n_app+1) - 1))
  f.write('''*.ue[*].app[{n}].typename="VoIPReceiver"
*.ue[*].app[{n}].localPort = 3000\n'''.format(n = n_app))

def writeNumUEs(f, numUEs: int):
  f.write("**.numUe = {}\n".format(numUEs))

def writePropagation(f, model: str):
  f.write('**.propagationModel = "{}"\n'.format(model))

def writeTransmissionPower(f, ue_power: int = 24, enb_power: int = 46, micro_power: int = 30):
  f.write("**.ueTxPower = {}\n**.eNodeBTxPower = {}\n**.microTxPower = {}\n".format(ue_power, enb_power, micro_power))

def writeNodeIsMicro(f, node_name, micro: bool = True):
  f.write('**.{}.cellInfo.microCell = {}\n'.format(node_name, "true" if micro else "false"))

def writeScenario(f, object_name, scenario: str = 'URBAN_MACROCELL'):
  f.write('**.{}.lteNic.channelModel.scenario = "{}"\n'.format(object_name, scenario))

def writeScenarioUEsPerso(f, numUEs: int, num_and_scen: ty.List[ty.List[int]] = [[1,1]]):
  count = 0
  for i in range(len(num_and_scen)):
    for l in range(num_and_scen[i][0]):
      if count < numUEs:
        f.write('**.ue[{}].lteNic.channelModel.scenario = "{}"\n'.format(count, num_and_scen[i][1]))
        count += 1
      else:
        break

  dif = numUEs - count
  if dif != 0:
    for i in range(numUEs-dif, numUEs):
      f.write('**.ue[{}].lteNic.channelModel.scenario = "{}"\n'.format(i, num_and_scen[-1][1]))