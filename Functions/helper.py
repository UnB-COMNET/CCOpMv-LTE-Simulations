from geometry import MapHexagonal, Macrocell
import typing as ty
import numpy as np
import geometry as geo

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

def writeConnectUE(f, UEs: ty.List[int] = [1], ENBs: ty.List[int] = [1], object_name: str= "ue"):
  count = 0
  if len(UEs) > len(ENBs):
    print("ERROR: missing element in ENBs")
  else:
    numUEs = np.sum(UEs)
    for i in range(len(UEs)):
      for l in range(UEs[i]):
        if count < numUEs:
          f.write('''**.{name}[{number}].macCellId = {enb}
**.{name}[{number}].masterId = {enb}\n'''.format(number = count, enb = ENBs[i], name = object_name))
          count += 1
        else:
          break

#TODo: change function name to indicate macrocell need
def writeConnectMultiUE(f, macrocells: ty.List[Macrocell]):
  last = len(macrocells)
  for i in range(len(macrocells)):
    ues = [len(macrocells[i].ues)] + [len(x.ues) for x in macrocells[i].smallcells]
    enbs = [i+1]
    for s in macrocells[i].smallcells:
      enbs += [last + len(s.antennas)]
      last += len(s.antennas)
    writeConnectUE(f, ues, enbs, "ue"+str(i))

def writeComment(f, text):
  f.write("\n# {}\n".format(text))

def writeMobilityType(f, type: str, object_name = "ue[*]"):
  f.write('*.{}.mobilityType = "{}"\n'.format(object_name, type))

def writeMovMobility(f, type: str, speed, initial_heading, object_name = "ue[*]"):
  writeMobilityType(f, type, object_name)
  f.write('*.{}.mobility.speed = {}mps\n'.format(object_name, speed))
  f.write('*.{}.mobility.initialMovementHeading = {}deg\n'.format(object_name, initial_heading))

def writeIniMobility(f, object_name, iniX: float, iniY: float, iniZ: ty.Union[str, float] = 0, display = False):
  f.write('''*.{name}.mobility.initialX = {iniX}m
*.{name}.mobility.initialY = {iniY}m
*.{name}.mobility.initialZ = {iniZ}m
*.{name}.mobility.initFromDisplayString = {display}
'''.format(name= object_name, iniX = iniX, iniY = iniY, iniZ = iniZ, display = 'true' if display else 'false'))

def getOptionsString(ini: ty.List[float], name: str) -> str:
  ini_str = '${'+name+'='
  for f in np.unique(ini):
    ini_str += ' ' + str(f) + 'm,'
  ini_str = ini_str[:-1] + "}"

  return ini_str

def writeOptionsIniMobility(f, object_name, iniX: ty.List[float], iniY: ty.List[float], iniZ: ty.List[ty.Union[str, float]] = None, display = False):

  f.write('''*.{name}.mobility.initialX = {iniX}
*.{name}.mobility.initialY = {iniY}
*.{name}.mobility.initialZ = {iniZ}
*.{name}.mobility.initFromDisplayString = {display}
'''.format(name= object_name, iniX = getOptionsString(iniX, 'iniX'), iniY = getOptionsString(iniY, 'iniY'), 
          iniZ = getOptionsString(iniZ, 'iniZ') if iniZ is not None else "0m", display = 'true' if display else 'false'))

def writeArrayIniMobility(f, object_array_name, coordenates: ty.List[ty.List[int]]):
  count = 0
  for x, y in zip(coordenates[0], coordenates[1]):
    writeIniMobility(f, object_array_name+'['+str(count)+']', x, y)
    count += 1

def writeMultiIniMobility(f, object_name, coordenates: ty.List[ty.List[int]]):
  num_coords = len(coordenates)
  count = 0
  if num_coords < 2:
    print("ERROR: necessary list with x coordinate list and y coordinate list")
  elif num_coords == 2:
    for x, y in zip(coordenates[0], coordenates[1]):
      writeIniMobility(f, object_name+str(count), x, y)
      count += 1
  else:
    for x, y in zip(coordenates[0], coordenates[1], coordenates[2]):
      writeIniMobility(f, object_name+str(count), x, y, y)
      count += 1

#TODo: Trocar nome para indicar que só funciona com o Hexagonal
def writeUeMobilityPerso(f, scen: MapHexagonal, display: bool = False, multi: bool = False):
  count = 0
  for m in scen.macrocells:
    if not multi: count = ''
    iniZ=np.zeros(scen.n_ues)
    [iniX, iniY] = m.getUEsPositionList()
    [iniX_smallcell, iniY_smallcell] = m.smallcells[0].getUEsPositionList()
    if iniX is None:
      iniX = []
      iniY = []
    if iniX_smallcell is None:
      iniX_smallcell = []
      iniY_smallcell = []
    iniX = iniX + iniX_smallcell
    iniY = iniY + iniY_smallcell
    for i in range(len(iniX)):
      f.write('''*.ue{num}[{number}].mobility.initialX = {iniX}m
*.ue{num}[{number}].mobility.initialY = {iniY}m
*.ue{num}[{number}].mobility.initialZ = {iniZ}m
'''.format(number = i, num = count, iniX = iniX[i], iniY = iniY[i], iniZ = iniZ[i]))

    f.write("*.ue{num}[*].mobility.initFromDisplayString = {display}\n".format(display = 'true' if display else 'false', num = count,))
    if not multi: break
    else: count += 1

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

'''def writeMultiConstraint(f, object_name, maxX = [], maxY = [],
                    maxZ = [], minX = [],
                    minY = [], minZ = []):
  count = 0
  for xa, ya, za, xb, yb, zb in zip(maxX, maxY, maxZ, minX, minY, minZ):
    writeConstraint(f, object_name+str(count), xa, ya, za, xb, yb, zb)
    count += 1 
'''
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

def writeNumApps(f, numUEs: int, directions: int, num_macros: int = 1, multi: bool = False):
  if multi:
    f.write("*.ue*[*].numApps = {}\n".format(directions))
  else:
    f.write("*.ue[*].numApps = {}\n".format(directions))
  f.write("*.server.numApps = {} * {} * {}\n".format(directions, numUEs, num_macros))

def writeAppVoipUL(f, numUEs: int, n_app: int = 0, object_name: str = "ue[*]", port: int = 4000):
  f.write('''*.{name}.app[{n}].typename="VoIPSender"
*.{name}.app[{n}].PacketSize = default
*.{name}.app[{n}].destAddress = "server"
*.{name}.app[{n}].destPort = {port} + ancestorIndex(1) #Pega o valor id de ue
*.{name}.app[{n}].localPort = 4888
*.{name}.app[{n}].startTime = 0.01s\n'''.format(name = object_name, n = n_app, port = port))
  f.write('''*.server.app[{n}..{f}].typename="VoIPReceiver"
*.server.app[{n}..{f}].localPort = {port} + ancestorIndex(0) - {n}\n'''.format(n = n_app * numUEs, f = numUEs*(n_app+1) - 1, port = port))

def writeMultiAppVoipUL(f, numUEs: int, num_macros: int, number_app: int = 0, num_apps: int = 2):
  for m in range(num_macros):
    f.write('''*.{name}.app[{n}].typename="VoIPSender"
*.{name}.app[{n}].PacketSize = default
*.{name}.app[{n}].destAddress = "server"
*.{name}.app[{n}].destPort = {port} + ancestorIndex(1) #Pega o valor id de ue
*.{name}.app[{n}].localPort = 4888
*.{name}.app[{n}].startTime = 0.01s\n'''.format(name = "ue"+str(m)+"[*]", n = number_app, port = 4000 + m*numUEs))
    f.write('''*.server.app[{n}..{f}].typename="VoIPReceiver"
*.server.app[{n}..{f}].localPort = {port} + ancestorIndex(0) - {n}
'''.format(n = (number_app + m*num_apps) * numUEs, f = numUEs*(number_app + m*num_apps + 1) - 1, port = 4000 + m*numUEs))

def writeAppVoipDL(f, numUEs: int, n_app: int = 0):
  f.write('''*.server.app[{n}..{f}].typename="VoIPSender"
*.server.app[{n}..{f}].PacketSize = default
*.server.app[{n}..{f}].destAddress = "ue[" + string(ancestorIndex(0) - {numUEs}) + "]"
*.server.app[{n}..{f}].destPort = 3000
*.server.app[{n}..{f}].localPort = 3088 + ancestorIndex(0)
*.server.app[{n}..{f}].startTime = 0.01s\n'''.format(numUEs = numUEs, n = n_app * numUEs, f = numUEs*(n_app+1) - 1))
  f.write('''*.ue[*].app[{n}].typename="VoIPReceiver"
*.ue[*].app[{n}].localPort = 3000\n'''.format(n = n_app))

def writeMultiAppVoipDL(f, numUEs: int, num_macros: int, number_app: int = 0, num_apps: int = 2):
  for m in range(num_macros):
    f.write('''*.server.app[{n}..{f}].typename="VoIPSender"
*.server.app[{n}..{f}].PacketSize = default
*.server.app[{n}..{f}].destAddress = "ue{m}[" + string(ancestorIndex(0) - {n}) + "]"
*.server.app[{n}..{f}].destPort = 3000
*.server.app[{n}..{f}].localPort = 3088 + ancestorIndex(0)
*.server.app[{n}..{f}].startTime = 0.01s
'''.format(m = m, n = (number_app + m*num_apps) * numUEs, f = numUEs*(number_app + m*num_apps + 1) - 1, port = 3000 + m*numUEs))
    f.write('''*.{name}.app[{n}].typename="VoIPReceiver"
*.{name}.app[{n}].localPort = 3000\n'''.format(name = "ue"+str(m)+"[*]", n = number_app))

def writeNumUEs(f, numUEs: int):
  f.write("**.numUe = {}\n".format(numUEs))

def writePropagation(f, model: str):
  f.write('**.propagationModel = "{}"\n'.format(model))

def writeTransmissionPower(f, ue_power: int = 24, enb_power: int = 46, micro_power: int = 30, txDirection: str="\"OMNI\""):
  f.write("**.ueTxPower = {}\n**.eNodeBTxPower = {}\n**.microTxPower = {}\n*.eNB.cellularNic.phy.txDirection = {}".format(ue_power, enb_power, micro_power,txDirection))

def writeChannelControl(f, alpha: int = 2, carrierFrequency: str = "2.4GHz", numChannels: int = 1):
  f.write('''*.channelControl.alpha = {}
*.channelControl.carrierFrequency = {}
*.channelControl.numChannels = {}
'''.format(alpha,carrierFrequency,numChannels))

def writeChannelModel(f, building_height: float = 20, nodeb_height: float = 25,
ue_height: float = 1.5,street_wide: float = 20, fading_type: str = "\"JAKES\"",
extCell_interference: bool = True, antennGainEnB: int = 18, antennGainMicro: int = 5,
antennaGainUe: int = 0, bs_noise_figure: int = 5, cable_loss: int = 2,
componentCarrierIndex: int = 0, correlation_distance: int = 50, d2d_interference: bool = True,
delay_rms: str = "363e-9", downlink_interference: bool = False, dynamic_los: bool = False,
enable_extCell_los: bool = True, fading: bool = True, fading_paths: int = 6,
fixed_los: bool = False, harqReduction: float = 0.2, inside_building: bool = False,
lambdaMaxTh: float = 0.2, lambdaMinTh: float = 0.02, lambdaRatioTh: float = 20,
rsrqScale: float = 1.0, rsrqShift: float = 22, shadowing: bool = True, targetBler: float = 0.01,
thermalNoise: float = -104.5, tolerateMaxDistViolation: bool = False, ue_noise_figure: float = 7,
uplink_interference: bool = False, useRsrqFromLog: bool = False, useTorus: bool = False):
  f.write('''**.cellularNic.channelModel[*].building_height = {}
**.cellularNic.channelModel[*].nodeb_height = {}
**.cellularNic.channelModel[*].ue_height = {}
**.cellularNic.channelModel[*].street_wide = {}
**.cellularNic.channelModel[*].fading_type = {}
**.cellularNic.channelModel[*].extCell_interference = {}
**.cellularNic.channelModel[*].antennGainEnB = {}
**.cellularNic.channelModel[*].antennGainMicro = {}
**.cellularNic.channelModel[*].antennaGainUe = {}
**.cellularNic.channelModel[*].bs_noise_figure = {}
**.cellularNic.channelModel[*].cable_loss = {}
**.cellularNic.channelModel[*].componentCarrierIndex = {}
**.cellularNic.channelModel[*].correlation_distance = {}
**.cellularNic.channelModel[*].d2d_interference = {}
**.cellularNic.channelModel[*].delay_rms = {}
**.cellularNic.channelModel[*].downlink_interference = {} 
**.cellularNic.channelModel[*].dynamic_los = {}
**.cellularNic.channelModel[*].enable_extCell_los = {}
**.cellularNic.channelModel[*].fading = {}
**.cellularNic.channelModel[*].fading_paths = {}
**.cellularNic.channelModel[*].fixed_los = {}
**.cellularNic.channelModel[*].harqReduction = {}
**.cellularNic.channelModel[*].inside_building = {}
**.cellularNic.channelModel[*].lambdaMaxTh = {}
**.cellularNic.channelModel[*].lambdaMinTh = {}
**.cellularNic.channelModel[*].lambdaRatioTh = {}
**.cellularNic.channelModel[*].rsrqScale = {}
**.cellularNic.channelModel[*].rsrqShift = {}
**.cellularNic.channelModel[*].shadowing = {}
**.cellularNic.channelModel[*].targetBler = {}
**.cellularNic.channelModel[*].thermalNoise = {}
**.cellularNic.channelModel[*].tolerateMaxDistViolation = {}
**.cellularNic.channelModel[*].ue_noise_figure = {}
**.cellularNic.channelModel[*].uplink_interference = {}
**.cellularNic.channelModel[*].useRsrqFromLog = {}
**.cellularNic.channelModel[*].useTorus = false
'''.format(building_height, nodeb_height, ue_height, street_wide, fading_type,
"true" if extCell_interference else "false", antennGainEnB, antennGainMicro, antennaGainUe,
bs_noise_figure, cable_loss, componentCarrierIndex, correlation_distance, "true" if d2d_interference else "false",
delay_rms, "false" if not downlink_interference else "true", "false" if not dynamic_los else "true",
"true" if enable_extCell_los else "false", "true" if fading else "false", fading_paths,
"false" if not fixed_los else "true", harqReduction, "false" if not inside_building else "true",
lambdaMaxTh, lambdaMinTh, lambdaRatioTh, rsrqScale, rsrqShift, "true" if shadowing else "false",
targetBler, thermalNoise, "false" if not tolerateMaxDistViolation else "true", ue_noise_figure,
"false" if not uplink_interference else "true", "false" if not useRsrqFromLog else "true",
"false" if not useTorus else "true"))

def writeNodeIsMicro(f, node_name, micro: bool = True):
  f.write('**.{}.cellInfo.microCell = {}\n'.format(node_name, "true" if micro else "false"))

def writeMultiMicro(f, number, node_name = "microCell", micro: bool = True):
  for i in range(number):
    writeNodeIsMicro(f, node_name+str(i))

def writeScenario(f, object_name, scenario: str = 'URBAN_MACROCELL', for5g: bool = False):
  if for5g:
    f.write('**.{}.cellularNic.channelModel[*].scenario = "{}"\n'.format(object_name, scenario))
  else:
    f.write('**.{}.lteNic.channelModel.scenario = "{}"\n'.format(object_name, scenario))

def writeMultiScenarios(f, object_name, num, scenario: str = 'URBAN_MACROCELL', for5g: bool = False):
  for i in range(num):
    writeScenario(f, object_name+str(i), scenario, for5g)

def writeScenarioPerso(f, object_name: str = 'ue', num_and_scen: ty.List[ty.Tuple[int,str]] = [[1,1]], for5g: bool = False):
  count = 0
  for i in range(len(num_and_scen)):
    for l in range(num_and_scen[i][0]):
        if for5g:
          f.write('**.{}[{}].cellularNic.channelModel[*].scenario = "{}"\n'.format(object_name, count, num_and_scen[i][1]))
        else:
          f.write('**.{}[{}].lteNic.channelModel.scenario = "{}"\n'.format(object_name, count, num_and_scen[i][1]))
        count += 1

def writeMultiScenariosPerso(f, macrocells: ty.List[Macrocell], object_name: str = 'ue', for5g: bool = False):
  for i in range(len(macrocells)):
    num_ues_macro = len(macrocells[i].ues)
    num_ues_micro = np.sum([len(x.ues) for x in macrocells[i].smallcells])
    writeScenarioPerso(f, object_name+str(i), [(num_ues_macro, 'URBAN_MACROCELL'), (num_ues_micro, 'URBAN_MICROCELL')], for5g)

def writeEnableHandover(f, object_name, enable = True):# Enable handover
  f.write('*.{}.lteNic.phy.enableHandover = {}\n'.format(object_name, "true" if enable else "false"))

def writeEnableHandoverMultiUE(f, macrocells: ty.List[Macrocell], only_micro = True):
  for i in range(len(macrocells)):
    if only_micro:
      ues_macro = len(macrocells[i].ues)
      ues_micro = np.sum([len(x.ues) for x in macrocells[i].smallcells])
      writeEnableHandover(f, "ue{}[{}..{}]".format(i, ues_macro, ues_macro+ues_micro-1))
    else:
      writeEnableHandover(f, "ue{}[*]".format(i))

def writeX2Configuration(f, object_name, quantity):
  f.write('*.{}.numX2Apps = {}    # one x2App per peering eNodeB\n'.format(object_name, quantity-1))
  f.write('*.{}.x2App[*].server.localPort = 5000 + ancestorIndex(1)\n'.format(object_name))

#Connecting only between same object_name
def writeX2Connections(f, object_names : ty.List[str], quantities : ty.List[int], initial_values : ty.List[int] = None, initial_app: int = 0):
  if initial_values is None:
    initial_values = np.zeros(len(quantities), dtype= int)

  if len(object_names) > len(quantities):
    print("ERROR: Missing quantities for all objects.")
    return -1

  ports = [None for i in range(len(object_names))]

  for i in range(len(object_names)):

    for number in range(initial_values[i], initial_values[i]+quantities[i]):
      app = initial_app

      for j in range(len(object_names)):
        if ports[j] is None:
          ports[j] = np.full(quantities[j], initial_app, dtype= int)

        for count in range(initial_values[j], initial_values[j]+quantities[j]):
          if count == number and i == j:
            continue
          else:
            f.write('*.{name}{number}.x2App[{app}].client.connectAddress = "{name2}{count}%x2ppp{port}"\n'
                    .format(name=object_names[i], number=number, app=app, name2=object_names[j],
                            count = count, port = ports[j][count-initial_values[j]]))
            app += 1
            ports[j][count-initial_values[j]] += 1

def writeCommentConfig(f, function_name, filename, directions, num_ues, center_x, center_y, sites, micro_per_small, small_per_site, seed):
  f.write('''#Function: {}
#Parameters: 
#  filename = '{}'
#  directions = {}
#  num_ues = {}
#  center_x = {}
#  center_y = {}
#  sites = {}
#  micro_per_small = {}
#  small_per_site = {}
#  seed = {}\n'''.format(function_name, filename, directions, num_ues, center_x,
                        center_y, sites, micro_per_small, small_per_site, seed))

def writeCommentConfigILP(f, function_name, filename, seed, d_height, d_width, d_region):
  f.write('''#Function: {}
#Parameters: 
#  filename = '{}'
#  seed = {}
#  Map height distance = {}
#  Map width distance = {}
#  Region side distance = {}\n'''.format(function_name, filename, seed, d_height, d_width, d_region))

def writeScenarioManager(f, xml, doc= True):
  if doc:
    f.write('*.scenarioManager.script = xmldoc("{}")\n'.format(xml))
  else:
    f.write('*.scenarioManager.script = xml("{}")\n'.format(xml))

def writeResourceBlocks(f, num: int, is5G: bool= False):
  if is5G:
    f.write("**.numBands = {}\n".format(num))
  else:
    f.write('''**.numRbDl = {}\n**.numRbUl = {}
**.binder.numBands = {} # this value should be kept equal to the number of RBs\n'''.format(num))

def defaultGeneral(f, is5g: bool = False):
  # General
  f.write("[General]\n")
  #Time
  f.write("sim-time-limit = 10s\n")
  # Statistics
  f.write('\n' + separation + " Statistics " + separation + '\n')
  writeOutput(f, "${resultdir}/${configname}/${repetition}")
  f.write("seed-set = ${repetition}\n")
  #Resource blocks
  if not is5g:
    writeSeparation(f, "Resource Blocks")
    f.write('''**.numRbDl = 6\n**.numRbUl = 6
**.binder.numBands = 6 # this value should be kept equal to the number of RBs\n''')