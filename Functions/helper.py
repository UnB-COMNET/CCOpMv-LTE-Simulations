from coordinates import Coordinate
from geometry import MapHexagonal, Macrocell, Movement
import typing as ty
import numpy as np

separation = "###############"

def nl(f):
  """Writes a newline in the file."""
  f.write('\n')

def writeSeparation(f, name):
  """Writes a comment separation in the file."""
  f.write('\n' + separation + ' ' + name + ' ' + separation + '\n')
  
def makeNewConfig(f,name, extends = False, extend_name = ''):
  """
  Writes the start of a new config in a .ini file.
  
  Keyword arguments:

  1. *extends*: if True new config will extend another already existing config
  2. *extend_name*: name of the config that will be extended if *extends* if True
  """
  f.write('\n[Config {}]\n'.format(name))
  if extends:
    f.write('extends = {}\n'.format(extend_name))

def writeVectorExtra(f, module, statistic = '*', value: bool = True):
  """Writes the vector recording configuration of the specified statistics in a .ini file."""
  f.write("{}.{}.vector-recording = {}\n".format(module, statistic, 'true' if value else 'false'))

def writeOutput(f, path: str, vector_rec: bool = False):
  """Writes the output configuration in a .ini file."""
  f.write(("output-scalar-file = {path}.sca\n"
           "output-vector-file = {path}.vec\n"
           "**.vector-recording = {vector}\n"
           "eventlog-file = {path}.elog\n").format(path = path, vector= 'true' if vector_rec else 'false'))

def writeTime(f, time: ty.Union[int, ty.List[int]], repeat: int, iter_name = ''):
  """Writes the time configuration in a .ini file, including the number of repetitions."""
  if type(time) is list:
    f.write("sim-time-limit = {}\nrepeat = {}\n".format(getOptionsString(time, name= iter_name, unit= 's'), repeat))
  else:
    f.write("sim-time-limit = {}s\nrepeat = {}\n".format(time, repeat))

def writeNetwork(f, network: str):
  """Writes the network name in a .ini file."""
  f.write("network = {}\n".format(network))

def writeConnectUE(f, UEs: ty.List[int] = [1], ENBs: ty.List[int] = [1], object_name: str= "ue"):
  """Writes the connections between objects and their nodes in a .ini file."""
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
  """Writes the connections between the UEs of Macrocells and their nodes in a .ini file."""
  last = len(macrocells)
  for i in range(len(macrocells)):
    ues = [len(macrocells[i].ues)] + [len(x.ues) for x in macrocells[i].smallcells]
    enbs = [i+1]
    for s in macrocells[i].smallcells:
      enbs += [last + len(s.antennas)]
      last += len(s.antennas)
    writeConnectUE(f, ues, enbs, "ue"+str(i))

def writeConnectOptions(f, list_connections: ty.List[ty.Union[ty.List[int], int]], object_name: str= "ue", parallel_var: str = ""):
  """Writes the connections between a array of UEs and serving cells,  that can use iteration variables or not."""
  count = 0
  for i in list_connections:
    if type(i) is list:
      enb_str = getOptionsString(values= i, parallel= parallel_var)
    else:
      enb_str = i
    
    f.write('''**.{name}[{number}].macCellId = {enb}
**.{name}[{number}].masterId = {enb}\n'''.format(number = count, enb = enb_str, name = object_name))
    count += 1
    pass

def writeComment(f, text):
  """Writes 'text' as a comment in a .ini file."""
  f.write("\n# {}\n".format(text))

def writeMobilityType(f, type: str, object_name = "ue[*]"):
  """Writes the mobility type configuration in a .ini file."""
  f.write('*.{}.mobilityType = "{}"\n'.format(object_name, type))

def writeArrayMovMobility(f, object_array_name, movements: ty.List[ty.Union[Movement, ty.List[Movement]]], fixed_speed: bool = True,
                          iter_name: str = '', paral_name: str= '', unit_speed: str = 'mps', unit_heading: str = 'deg'):
  """Writes the moving mobility configuration of an array of objects a .ini file."""
  count = 0
  for mov in movements:
    if type(mov) is list:
      direction = [m.direction for m in mov]
      speed = [m.speed for m in mov]
    else:
      direction = mov.direction
      speed = mov.speed

    if not fixed_speed:
      writeMovMobility(f, speed =None, initial_heading=direction, object_name= object_array_name+'['+str(count)+']',
                       iter_name= iter_name, paral_name= paral_name, unit_speed= unit_speed, unit_heading= unit_heading)
    else:
      writeMovMobility(f, speed =speed, initial_heading=direction, object_name= object_array_name+'['+str(count)+']',
                       iter_name= iter_name, paral_name= paral_name, unit_speed= unit_speed, unit_heading= unit_heading)
    count += 1

def writeMovMobility(f, speed: ty.Union[float, ty.List[float]] = None, initial_heading: ty.Union[float, ty.List[float]] = 0, object_name = "ue[*]",
                     iter_name: str = '', paral_name: str= '', unit_speed: str = 'mps', unit_heading: str = 'deg'):
  """Writes the moving mobility configuration of an object in a .ini file."""
  if speed is not None:
    if type(speed) is list:
      f.write('*.{}.mobility.speed = {}\n'.format(object_name, getOptionsString(speed, "Spd_"+iter_name if iter_name != '' else '', unit_speed, paral_name)))
    else:
      f.write('*.{}.mobility.speed = {}{}\n'.format(object_name, speed, unit_speed))
  
  if type(initial_heading) is list:
    f.write('*.{}.mobility.initialMovementHeading = {}\n'.format(object_name, getOptionsString(initial_heading, "Ini_head_"+iter_name if iter_name != '' else '', unit_heading, paral_name)))
  else:
    f.write('*.{}.mobility.initialMovementHeading = {}{}\n'.format(object_name, initial_heading, unit_heading))

def writeMassMobDefault(f, object_name = "ue[*]", update_interval: float = 1.0, angle_delta: float = 0, axis_angle: float = 0):
  """Writes the default configuration of the MassMobility mobility type in a .ini file."""
  f.write('*.{}.mobility.changeInterval = {}s\n'.format(object_name, update_interval))
  f.write('*.{}.mobility.angleDelta = {}deg\n'.format(object_name, angle_delta))
  f.write('*.{}.mobility.rotationAxisAngle = {}deg\n'.format(object_name, axis_angle))

def writeVarSpeedMobDefault(f, speed_mean: float, std_dev: float, update_interval: float = 1.0, object_name = "ue[*]"):
  """Writes the default configuration of the VariableSpeedMobility mobility type in a .ini file."""
  f.write('*.{}.mobility.changeInterval = {}s\n'.format(object_name, update_interval))
  f.write('*.{}.mobility.meanSpeed = {}mps\n'.format(object_name, speed_mean))
  f.write('*.{}.mobility.standardDeviation = {}\n'.format(object_name, std_dev))

def writeIniMobility(f, object_name, iniX: float, iniY: float, iniZ: ty.Union[str, float] = 0, display = False):
  """Writes the initial location of an object in a .ini file."""
  f.write(("*.{name}.mobility.initialX = {iniX}m\n"
           "*.{name}.mobility.initialY = {iniY}m\n"
           "*.{name}.mobility.initialZ = {iniZ}m\n"
           "*.{name}.mobility.initFromDisplayString = {display}\n"
          ).format(name= object_name, iniX = iniX, iniY = iniY, iniZ = iniZ, display = 'true' if display else 'false'))

def getOptionsString(values: ty.List[ty.Union[float, int, str]], name: str = '', unit: str = '', parallel: str = "") -> str:
  """Writes a named or not iteration variable in a .ini file."""
  val_str = '${'+ (name+'= ' if name != "" else "")
  for f in values:
    val_str += str(f) + unit + ', '
  val_str = val_str[:-2]

  if parallel != '':
    val_str += ' ! {}'.format(parallel)
  val_str +=  "}"

  return val_str

def writeOptionsIniMobility(f, object_name, iniX: ty.List[float], iniY: ty.List[float], iniZ: ty.List[ty.Union[str, float]] = None, display: bool = False,
                            iter_name: str = '', paral_name: str= '', unit: str = 'm'):
  """Writes the initial location of an object using named iteration variables in a .ini file."""
  f.write(("*.{name}.mobility.initialX = {iniX}\n"
           "*.{name}.mobility.initialY = {iniY}\n"
           "*.{name}.mobility.initialZ = {iniZ}\n"
           "*.{name}.mobility.initFromDisplayString = {display}\n"
          )
  .format(name= object_name, iniX = getOptionsString(iniX, 'iniX_'+iter_name if iter_name != '' else '', unit, paral_name), iniY = getOptionsString(iniY, 'iniY_'+iter_name if iter_name != '' else '', unit, paral_name), 
          iniZ = getOptionsString(iniZ, 'iniZ_'+iter_name if iter_name != '' else '', unit, paral_name) if iniZ is not None else "0"+unit, display = 'true' if display else 'false'))

def writeArrayIniMobility(f, object_array_name, coordinates: ty.List[ty.Union[Coordinate, ty.List[Coordinate]]], count_init: int = 0,
                          iter_name: str= '', paral_name: str= ''):
  """Writes the initial location of a array of objects, that can use iteration variables or not."""
  for coord in coordinates:
    if type(coord) is list:
      writeOptionsIniMobility(f, object_array_name+'['+str(count_init)+']', [c.x for c in coord], [c.y for c in coord], [c.z for c in coord],
                              iter_name= iter_name, paral_name= paral_name)
    else:
      writeIniMobility(f, object_array_name+'['+str(count_init)+']', coord.x, coord.y, coord.z)
    
    count_init += 1

def writeMultiIniMobility(f, object_name, coordinates: ty.List[Coordinate]):
  """Writes the initial location of multiple groups of an object in a .ini file.

  The function considers the existence of multiple groups of that object with a number in the end of each group name.

  Ex: UE0, UE1, ...
  """
  count = 0
  for coord in coordinates:
    writeIniMobility(f, object_name+str(count), coord.x, coord.y, coord.z)
    count += 1

#TODo: Trocar nome para indicar que só funciona com o Hexagonal
def writeUeMobilityPerso(f, scen: MapHexagonal, display: bool = False, multi: bool = False):
  """Writes the initial location of all UEs from a MapHexagonal scenario."""
  count = 0
  for m in scen.macrocells:
    if not multi: count = ''
    iniZ=np.zeros(scen.n_ues)
    ini = m.getUEsPositionList()
    ini_smallcell = m.smallcells[0].getUEsPositionList()

    ini = ini + ini_smallcell
    for i in range(len(ini)):
      f.write(("*.ue{num}[{number}].mobility.initialX = {iniX}m\n"
               "*.ue{num}[{number}].mobility.initialY = {iniY}m\n"
               "*.ue{num}[{number}].mobility.initialZ = {iniZ}m\n"
              ).format(number = i, num = count, iniX = ini[i].x, iniY = ini[i].y, iniZ = iniZ[i]))

    f.write("*.ue{num}[*].mobility.initFromDisplayString = {display}\n".format(display = 'true' if display else 'false', num = count,))
    if not multi: break
    else: count += 1

def writeConstraint(f, object_name, maxX: ty.Union[str, float] = 'inf', maxY: ty.Union[str, float] = 'inf',
                    maxZ: ty.Union[str, float] = 'inf', minX: ty.Union[str, float] = '-inf',
                    minY: ty.Union[str, float] = '-inf', minZ: ty.Union[str, float] = '-inf'):
  """Writes the mobility contraints of an object in a .ini file."""
  f.write(("*.{name}.mobility.constraintAreaMaxX = {maxX} m\n"
           "*.{name}.mobility.constraintAreaMaxY = {maxY} m\n"
           "*.{name}.mobility.constraintAreaMaxZ = {maxZ} m\n"
           "*.{name}.mobility.constraintAreaMinX = {minX} m\n"
           "*.{name}.mobility.constraintAreaMinY = {minY} m\n"
           "*.{name}.mobility.constraintAreaMinZ = {minZ} m\n"
          ).format(name = object_name, maxX = maxX, maxY = maxY, maxZ = maxZ, 
                   minX = minX, minY = minY, minZ = minZ))


def writeSeeds(f, seed_set: ty.Union[str, int] = "${repetition}", num_rngs: int = 1, seeds: ty.List[int] = []):
  """Writes the configuration of the seed set, number of rngs and seeds used in a .ini file."""
  f.write("seed-set = {}\nnum-rngs = {}\n".format(seed_set, num_rngs))
  if num_rngs > 1 and len(seeds) >= num_rngs - 1:
    for i in range(1, num_rngs):
      f.write("seed-{}-mt = {}\n".format(i, seeds[i-1]))

def writeSchedulingOptions(f, sched: ty.List[str]):
  """Writes the network name in a .ini file."""
  f.write('**.schedulingDisciplineUl = ${sched=')
  temp = ''
  for s in sched:
    temp += ' "' + s + '",'
  f.write(temp[:-1] + '}\n**.schedulingDisciplineDl = ${sched}\n')

def writeNumApps(f, numUEs: int, directions: int, num_multi: int = 1, multi: bool = False):
  """Writes the number of apps that the UEs and the server must have in a .ini file."""
  if multi:
    f.write("*.ue*[*].numApps = {}\n".format(directions))
    f.write("*.server.numApps = {} * {} * {}\n".format(directions, numUEs, num_multi))
  else:
    f.write("*.ue[*].numApps = {}\n".format(directions))
    f.write("*.server.numApps = {} * {} * {}\n".format(directions, numUEs, 1))

def writeAppVoipUL(f, numUEs: int, n_app: int = 0, object_name: str = "ue[*]", port: int = 4000, p_size= 40):
  """Writes the VoIP UL aplication configuration involving objects and a server in a .ini file."""
  f.write(('*.{name}.app[{n}].typename="VoIPSender"\n'
           '*.{name}.app[{n}].PacketSize = {p_size}\n'
           '*.{name}.app[{n}].destAddress = "server"\n'
           '*.{name}.app[{n}].destPort = {port} + ancestorIndex(1) #Pega o valor id de ue\n'
           '*.{name}.app[{n}].localPort = 4888\n'
           '*.{name}.app[{n}].startTime = 0.01s\n').format(name = object_name, n = n_app, port = port, p_size= p_size))
  f.write(('*.server.app[{n}..{f}].typename="VoIPReceiver"\n'
           '*.server.app[{n}..{f}].localPort = {port} + ancestorIndex(0) - {n}\n').format(n = n_app * numUEs, f = numUEs*(n_app+1) - 1, port = port))

def writeMultiAppVoipUL(f, numUEs: int, num_multi: int, number_app: int = 0, num_apps: int = 2, p_size= 40):
  """Writes the VoIP UL application configuration involving multiple UE lists and a server in a .ini file."""
  for m in range(num_multi):
    f.write(('*.{name}.app[{n}].typename="VoIPSender"\n'
             '*.{name}.app[{n}].PacketSize = {p_size}\n'
             '*.{name}.app[{n}].destAddress = "server"\n'
             '*.{name}.app[{n}].destPort = {port} + ancestorIndex(1) #Pega o valor id de ue\n'
             '*.{name}.app[{n}].localPort = 4888\n'
             '*.{name}.app[{n}].startTime = 0.01s\n'
             ).format(name = "ue"+str(m)+"[*]", n = number_app, port = 4000 + m*numUEs, p_size= p_size))
    f.write(('*.server.app[{n}..{f}].typename="VoIPReceiver"\n'
             '*.server.app[{n}..{f}].localPort = {port} + ancestorIndex(0) - {n}\n'
            ).format(n = (number_app + m*num_apps) * numUEs, f = numUEs*(number_app + m*num_apps + 1) - 1, port = 4000 + m*numUEs))

def writeAppVoipDL(f, numUEs: int, n_app: int = 0, p_size= 40):
  """Writes the VoIP DL aplication configuration involving an UE list and a server in a .ini file."""
  f.write(('*.server.app[{n}..{f}].typename="VoIPSender"\n'
           '*.server.app[{n}..{f}].PacketSize = {p_size}\n'
           '*.server.app[{n}..{f}].destAddress = "ue[" + string(ancestorIndex(0) - {n}) + "]"\n'
           '*.server.app[{n}..{f}].destPort = 3000\n'
           '*.server.app[{n}..{f}].localPort = 3088 + ancestorIndex(0)\n'
           '*.server.app[{n}..{f}].startTime = 0.01s\n'
          ).format(n = n_app * numUEs, f = numUEs*(n_app+1) - 1, p_size= p_size))
  f.write(('*.ue[*].app[{n}].typename="VoIPReceiver"\n'
           '*.ue[*].app[{n}].localPort = 3000\n').format(n = n_app))

def writeMultiAppVoipDL(f, numUEs: int, num_multi: int, number_app: int = 0, num_apps: int = 2, p_size= 40):
  """Writes the VoIP DL application configuration involving multiple UE lists and a server in a .ini file."""
  for m in range(num_multi):
    f.write(('*.server.app[{n}..{f}].typename="VoIPSender"\n'
             '*.server.app[{n}..{f}].PacketSize = {p_size}\n'
             '*.server.app[{n}..{f}].destAddress = "ue{m}[" + string(ancestorIndex(0) - {n}) + "]"\n'
             '*.server.app[{n}..{f}].destPort = 3000\n'
             '*.server.app[{n}..{f}].localPort = 3088 + ancestorIndex(0)\n'
             '*.server.app[{n}..{f}].startTime = 0.01s\n'
            ).format(m = m, n = (number_app + m*num_apps) * numUEs, f = numUEs*(number_app + m*num_apps + 1) - 1, port = 3000 + m*numUEs, p_size= p_size))
    f.write(('*.{name}.app[{n}].typename="VoIPReceiver"\n'
             '*.{name}.app[{n}].localPort = 3000\n').format(name = "ue"+str(m)+"[*]", n = number_app))

def writeAppVideoUL(f, numUEs: int, p_size:int = 1000, n_app: int = 0, mtu: bool = True, s_interval: int = 1):
  """Writes the Video Streaming DL aplication configuration involving an UE list and a server in a .ini file."""
  f.write(('**.server.app[{n}..{f}].typename = "UdpVideoStreamClient"\n'
           '**.server.app[{n}..{f}].serverAddress = "ue[" + string(ancestorIndex(0) - {n}) + "]"\n'
           '**.server.app[{n}..{f}].localPort = 9000 + ancestorIndex(0)\n'
           '**.server.app[{n}..{f}].serverPort = 4088\n'
           '**.server.app[{n}..{f}].startTime = 0.001s\n'
          ).format(n = n_app * numUEs, f = numUEs*(n_app+1) - 1))
  f.write(('**.ue[*].app[{n}].typename = "UdpVideoStreamServer"\n'
           '**.ue[*].app[{n}].videoSize = 10MiB\n'
           '**.ue[*].app[{n}].localPort = 4088\n'
           '**.ue[*].app[{n}].sendInterval = {s_interval}ms\n'
           '**.ue[*].app[{n}].packetLen = {p_size}B\n'
          ).format(p_size= p_size, n = n_app, s_interval= s_interval))
  if mtu:
    f.write('**.mtu = 1428B\n')

def writeAppVideoDL(f, numUEs: int, p_size:int = 1000, n_app: int = 0, mtu: bool= True, s_interval: int = 1):
  """Writes the Video Streaming DL aplication configuration involving an UE list and a server in a .ini file."""
  f.write(('**.ue[*].app[{n}].typename = "UdpVideoStreamClient"\n'
           '**.ue[*].app[{n}].serverAddress = "server"\n'
           '**.ue[*].app[{n}].localPort = 9000\n'
           '**.ue[*].app[{n}].serverPort = 3088 + ancestorIndex(1) + {g}\n'
           '**.ue[*].app[{n}].startTime = 0.001s\n'
          ).format(n = n_app, g= numUEs*n_app))
  f.write(('**.server.app[{n}..{f}].typename = "UdpVideoStreamServer"\n'
           '**.server.app[{n}..{f}].videoSize = 10MiB\n'
           '**.server.app[{n}..{f}].localPort = 3088 + ancestorIndex(0)\n'
           '**.server.app[{n}..{f}].sendInterval = {s_interval}ms\n'
           '**.server.app[{n}..{f}].packetLen = {p_size}B\n'
          ).format(p_size= p_size, n = n_app * numUEs, f = numUEs*(n_app+1) - 1, s_interval= s_interval))
  if mtu:
    f.write('**.mtu = 1428B\n')
  

def writeNumUEs(f, numUEs: int):
  """Writes the number os UEs in a .ini file."""
  f.write("**.numUe = {}\n".format(numUEs))

def writePropagation(f, model: str):
  """Writes the propagation model from INET in a .ini file.
  
  Obs: **Not being used in SimuLTE or Simu5G**
  """
  f.write('**.propagationModel = "{}"\n'.format(model))

def writeTransmissionPower(f, ue_power: int = 24, enb_power: int = 46, micro_power: int = 30, txDirection: str="\"OMNI\"", is5G= False):
  """Writes the transmission configuration in a .ini file.
  
  The tranmission configuration includes the UEs, eNodeB and Microcells transmission power and direction.

  Keyword arguments:

  1. *is5G*: if true uses Simu5G else SimuLTE (default False)
  """
  f.write("**.ueTxPower = {}\n**.eNodeBTxPower = {}\n**.microTxPower = {}\n".format(ue_power, enb_power, micro_power))
  if is5G:
    f.write("**.cellularNic.phy.txDirection = {}\n".format(txDirection))
  else:
    f.write("**.lteNic.phy.txDirection = {}\n".format(txDirection))

def writeCarrierAggregation5G(f, num_carriers:int = 1, carriers_frequencies: ty.List[float] = [2], eNBs_carriers: bool = False):
  """Writes the carrier aggregation submodule configuration from Simu5G in a .ini file."""
  f.write('**.numComponentCarriers = {}\n'.format(num_carriers))
  for i in range(num_carriers):
    f.write('*.carrierAggregation.componentCarrier[{}].carrierFrequency = {}GHz\n'.format(i, carriers_frequencies[i]))
  if eNBs_carriers:
    for i in range(num_carriers):
      f.write("*.eNB{}.cellularNic.channelModel[*].componentCarrierIndex = {}\n".format(i, i))

def writeChannelModel5G(f, model_name: str = "LteRealisticChannelModel",  building_height: float = 20, nodeb_height: float = 25,
                        ue_height: float = 1.5,street_wide: float = 20, fading_type: str = "\"JAKES\"",
                        extCell_interference: bool = False, antennGainEnB: int = 18, antennGainMicro: int = 5,
                        antennaGainUe: int = 0, bs_noise_figure: int = 5, cable_loss: int = 2,
                        componentCarrierIndex: int = 0, correlation_distance: int = 50, d2d_interference: bool = True,
                        delay_rms: str = "363e-9", downlink_interference: bool = False, dynamic_los: bool = False,
                        enable_extCell_los: bool = True, fading: bool = True, fading_paths: int = 6,
                        fixed_los: bool = False, harqReduction: float = 0.2, inside_building: bool = False,
                        lambdaMaxTh: float = 0.2, lambdaMinTh: float = 0.02, lambdaRatioTh: float = 20,
                        rsrqScale: float = 1.0, rsrqShift: float = 22, shadowing: bool = True, targetBler: float = 0.01,
                        thermalNoise: float = -104.5, tolerateMaxDistViolation: bool = False, ue_noise_figure: float = 7,
                        uplink_interference: bool = False, useRsrqFromLog: bool = False, useTorus: bool = False):
  """Writes the channel model submodule configuration in a .ini file."""
  f.write(('**.cellularNic.LteChannelModelType = "{}"\n'
           '**.cellularNic.channelModel[*].building_height = {}\n'
           '**.cellularNic.channelModel[*].nodeb_height = {}\n'
           '**.cellularNic.channelModel[*].ue_height = {}\n'
           '**.cellularNic.channelModel[*].street_wide = {}\n'
           '**.cellularNic.channelModel[*].fading_type = {}\n'
           '**.cellularNic.channelModel[*].extCell_interference = {}\n'
           '**.cellularNic.channelModel[*].antennGainEnB = {}\n'
           '**.cellularNic.channelModel[*].antennGainMicro = {}\n'
           '**.cellularNic.channelModel[*].antennaGainUe = {}\n'
           '**.cellularNic.channelModel[*].bs_noise_figure = {}\n'
           '**.cellularNic.channelModel[*].cable_loss = {}\n'
           '**.cellularNic.channelModel[*].componentCarrierIndex = {}\n'
           '**.cellularNic.channelModel[*].correlation_distance = {}\n'
           '**.cellularNic.channelModel[*].d2d_interference = {}\n'
           '**.cellularNic.channelModel[*].delay_rms = {}\n'
           '**.cellularNic.channelModel[*].downlink_interference = {}\n'
           '**.cellularNic.channelModel[*].dynamic_los = {}\n'
           '**.cellularNic.channelModel[*].enable_extCell_los = {}\n'
           '**.cellularNic.channelModel[*].fading = {}\n'
           '**.cellularNic.channelModel[*].fading_paths = {}\n'
           '**.cellularNic.channelModel[*].fixed_los = {}\n'
           '**.cellularNic.channelModel[*].harqReduction = {}\n'
           '**.cellularNic.channelModel[*].inside_building = {}\n'
           '**.cellularNic.channelModel[*].lambdaMaxTh = {}\n'
           '**.cellularNic.channelModel[*].lambdaMinTh = {}\n'
           '**.cellularNic.channelModel[*].lambdaRatioTh = {}\n'
           '**.cellularNic.channelModel[*].rsrqScale = {}\n'
           '**.cellularNic.channelModel[*].rsrqShift = {}\n'
           '**.cellularNic.channelModel[*].shadowing = {}\n'
           '**.cellularNic.channelModel[*].targetBler = {}\n'
           '**.cellularNic.channelModel[*].thermalNoise = {}\n'
           '**.cellularNic.channelModel[*].tolerateMaxDistViolation = {}\n'
           '**.cellularNic.channelModel[*].ue_noise_figure = {}\n'
           '**.cellularNic.channelModel[*].uplink_interference = {}\n'
           '**.cellularNic.channelModel[*].useRsrqFromLog = {}\n'
           '**.cellularNic.channelModel[*].useTorus = {}\n'
          ).format(model_name, building_height, nodeb_height, ue_height, street_wide, fading_type,
                   "true" if extCell_interference else "false", antennGainEnB, antennGainMicro, antennaGainUe,
                   bs_noise_figure, cable_loss, componentCarrierIndex, correlation_distance, "true" if d2d_interference else "false",
                   delay_rms, "false" if not downlink_interference else "true", "false" if not dynamic_los else "true",
                   "true" if enable_extCell_los else "false", "true" if fading else "false", fading_paths,
                   "false" if not fixed_los else "true", harqReduction, "false" if not inside_building else "true",
                   lambdaMaxTh, lambdaMinTh, lambdaRatioTh, rsrqScale, rsrqShift, "true" if shadowing else "false",
                   targetBler, thermalNoise, "false" if not tolerateMaxDistViolation else "true", ue_noise_figure,
                   "false" if not uplink_interference else "true", "false" if not useRsrqFromLog else "true",
                   "false" if not useTorus else "true"))

def writeSlices(f, num_slices: int, iter_name: str = 'Slice'):
  """Writes the configuration that defines the number of slices used when using MoreInfoChannelModel."""
  f.write('**.cellularNic.channelModel[*].num_slice = {}\n'.format(getOptionsString(values= range(num_slices), name= iter_name)))

def writeNumEnbs(f, options: ty.List[int], iter_name: str = 'Slice', parallel_name: str = ''):
  """Writes the configuration that informs the number of eNBs used when in each slice using MoreInfoChannelModel."""
  f.write('**.cellularNic.channelModel[*].num_enbs = {}\n'.format(getOptionsString(values= options, name= iter_name, parallel= parallel_name)))  

def writeNodeIsMicro(f, node_name, micro: bool = True):
  """Writes the configuration that defines a node as a microcell in a .ini file."""
  f.write('**.{}.cellInfo.microCell = {}\n'.format(node_name, "true" if micro else "false"))

def writeMultiMicro(f, number, node_name = "microCell"):
  """Writes a configuration defining multiple nodes as microcells in a .ini file."""
  for i in range(number):
    writeNodeIsMicro(f, node_name+str(i))

def writeScenario(f, object_name, scenario: str = 'URBAN_MACROCELL', for5g: bool = False):
  """Writes the propagation scenario used by an object in a .ini file.
  
  Keyword arguments:

  1. *is5g*: if true uses Simu5G else SimuLTE (default False)
  """
  if for5g:
    f.write('**.{}.cellularNic.channelModel[*].scenario = "{}"\n'.format(object_name, scenario))
  else:
    f.write('**.{}.lteNic.channelModel.scenario = "{}"\n'.format(object_name, scenario))

def writeMultiScenarios(f, object_name, num, scenario: str = 'URBAN_MACROCELL', for5g: bool = False):
  """Writes the propagation scenario used by multiple objects in a .ini file.

  Keyword arguments:

  1. *is5g*: if true uses Simu5G else SimuLTE (default False)
  """
  for i in range(num):
    writeScenario(f, object_name+str(i), scenario, for5g)

def writeScenarioPerso(f, object_name: str = 'ue', num_and_scen: ty.List[ty.Tuple[int,str]] = [[1,1]], for5g: bool = False):
  """Writes the propagation scenario for specific elements of a object array in a .ini file.
  
  Keyword arguments:

  1. *is5g*: if true uses Simu5G else SimuLTE (default False)
  """
  count = 0
  for i in range(len(num_and_scen)):
    for l in range(num_and_scen[i][0]):
        if for5g:
          f.write('**.{}[{}].cellularNic.channelModel[*].scenario = "{}"\n'.format(object_name, count, num_and_scen[i][1]))
        else:
          f.write('**.{}[{}].lteNic.channelModel.scenario = "{}"\n'.format(object_name, count, num_and_scen[i][1]))
        count += 1

def writeMultiScenariosPerso(f, macrocells: ty.List[Macrocell], object_name: str = 'ue', for5g: bool = False):
  """Writes the propagation scenario used by multiple array objects in a .ini file.
  
  Keyword arguments:

  1. *is5g*: if true uses Simu5G else SimuLTE (default False)
  """
  for i in range(len(macrocells)):
    num_ues_macro = len(macrocells[i].ues)
    num_ues_micro = np.sum([len(x.ues) for x in macrocells[i].smallcells])
    writeScenarioPerso(f, object_name+str(i), [(num_ues_macro, 'URBAN_MACROCELL'), (num_ues_micro, 'URBAN_MICROCELL')], for5g)

def writeEnableHandover(f, object_name, enable = True, is5G = False):
  """Writes the configuration that enables the handover procedure involving a object in a .ini file.
  
  Keyword arguments:

  1. *is5g*: if true uses Simu5G else SimuLTE (default False)
  """
  if is5G:
    f.write('*.{}.cellularNic.phy.enableHandover = {}\n'.format(object_name, "true" if enable else "false"))
  else:
    f.write('*.{}.lteNic.phy.enableHandover = {}\n'.format(object_name, "true" if enable else "false"))

def writeEnableHandoverMultiUE(f, macrocells: ty.List[Macrocell], only_micro = True):
  """Writes the configuration that enables the handover procedure for the UEs of a Macrocell in a .ini file.
  
  Keyword arguments:

  1. *only_micro*: if true considers only the UEs connected to the Microcells (default True)
  """
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
  """Writes the X2 connections in a .ini file."""
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
  """Writes a comment with the main parameters of the MapHexagonal scenario used in a .ini file."""
  f.write((f"#Function: {function_name}\n"
           "#Parameters: \n"
           "#  filename = '{}'\n"
           "#  directions = {}\n"
           "#  num_ues = {}\n"
           "#  center_x = {}\n"
           "#  center_y = {}\n"
           "#  sites = {}\n"
           "#  micro_per_small = {}\n"
           "#  small_per_site = {}\n"
           "#  seed = {}\n").format(function_name, filename, directions, num_ues, center_x,
                                    center_y, sites, micro_per_small, small_per_site, seed))

def writeCommentConfigILP(f, function_name: str, dict_args: dict, extra: str = None):
  """Writes a comment with the main parameters of the ILP scenario used in a .ini file."""

  f.write((f"#Function: {function_name}\n"
            "#Parameters:\n"))
  for arg in dict_args:
    f.write(f"#   {arg}: {dict_args[arg]}\n")
  if extra is not None:
    f.write('#Extra = {}\n'.format(extra))

def writeScenarioManager(f, xml, doc= True):
  """Writes the configuration of the scenario manager submodule in a .ini file."""
  if doc:
    f.write('*.scenarioManager.script = xmldoc("{}")\n'.format(xml))
  else:
    f.write('*.scenarioManager.script = xml("{}")\n'.format(xml))

def writeResourceBlocks(f, num: int, is5G: bool= False):
  """Writes the number of resource blocks used in a .ini file."""
  if is5G:
    f.write("**.numBands = {}\n".format(num))
  else:
    f.write(('**.numRbDl = {}\n**.numRbUl = {}\n'
             '**.binder.numBands = {} # this value should be kept equal to the number of RBs\n').format(num))

def writeResourceBlocksOptions(f, name: str, nums: ty.List[int], is5G: bool= False):
  """Writes the number of resource blocks used in a .ini file."""
  if is5G:
    f.write("**.numBands = {}\n".format(getOptionsString(nums, name, '')))
  else:
    f.write(('**.numRbDl = {}\n**.numRbUl = ${{{}}}\n'
             '**.binder.numBands = ${{{}}} # this value should be kept equal to the number of RBs\n').format(getOptionsString(nums, name, ''), name, name))    

def writeSnapshotsConfig(f, filename: str = "${resultdir}/${configname}-${iterationvarsf}-${repetition}.sna",
  snapshot: bool = True, delay: float = 1.0):
  """Writes the snapshotter configuration in a .ini file."""
  f.write('snapshot-file = {}\n'.format(filename))
  f.write('**.snapshotter.snapshot = {}\n'.format("true" if snapshot else "false"))
  f.write('**.snapshotter.delay = {}\n'.format(delay))

def writeCmdenvConfig(f, min_sinr: int, output_file_name: str = None, performance_display = False, redirect_output= False):
  """Writes the cmdenv configuration in a .ini file."""
  if output_file_name is None:
    output_file_name = "${resultdir}/${configname}-cmdout/"+ str(min_sinr) +"-${RBs}-${repetition}-${Slice}.out"

  f.write(('cmdenv-performance-display = {p_display}\n'
           'cmdenv-redirect-output = {r_output}\n'
           'cmdenv-output-file = {file_name}\n'
           ).format(p_display = 'true' if performance_display else 'false', r_output= 'true' if redirect_output else 'false', file_name= output_file_name))

def defaultGeneral(f, is5g: bool = False):
  """Writes a default General configuration in a .ini file."""
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
    f.write(('**.numRbDl = 6\n**.numRbUl = 6\n'
             '**.binder.numBands = 6 # this value should be kept equal to the number of RBs\n'))