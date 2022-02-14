from typing import Dict, List

import helper as hp
import helper_ned as hned
import helper_xml as hxml
import random
import geometry as geo
import numpy as np

def ilp_fixed_users(filename: str, seed: int, size_y:int =8000, size_x:int =8000, size_sector:int =800, n_macros: int = 2):
  """This function generates a .ini file to watch users mobility behaviour.
  
  The simulation configured with the resulting file has the purpose of generate the mobility data of the users in time.

  It doesn't have any application running on the UEs or server.

  Args:
    filename: string representing the name of the resulting file
    seed: integer used as seed in the distribuition of UEs and the simulation
	  size_y: y dimension size of considered region in meters
    size_x: x dimension size of considered region in meters
    size_sector: sides size of square sectors in meters
    n_macros: number of macrocells considered to distribute the UEs on the map
  """

  scen = geo.MapChess(size_y, size_x, size_sector, carrier_frequency= 0.7, chosen_seed= seed)
  scen.placeUEs(type= "Random", n_macros= n_macros)#Full = 4320 UEs

  ues_coords = scen.getUEsPositionList()
  ues_mov = scen.getUEsMovementList()
  #scen.plotUes()
  num_ues = len(ues_coords)

  with open(filename, 'wt') as f:
    hp.writeCommentConfigILP(f, "ilp_fixed_users", filename, seed, size_y, size_x, size_sector, extra = 'Using {} macros with {} ues each.'.format(n_macros, 60))
    hp.defaultGeneral(f, is5g= True)
    hp.makeNewConfig(f, name= 'Config ilp_fixed_users')
    hp.writeNetwork(f, network= '_5G.networks.SimpleNet')
    hp.writeTime(f, time= 10, repeat= 1)
    hp.writeSeeds(f, num_rngs= 2, seeds= [seed])
    hp.nl(f)
    hp.writeOutput(f, "${resultdir}/${configname}/${repetition}")
    hp.writeSeparation(f, "Snapshots")
    hp.writeSnapshotsConfig(f, filename= "../../../Functions/${configname}-${iterationvarsf}-${repetition}.sna", snapshot= True)
    hp.writeSeparation(f, "Transmission Power")
    hp.writeTransmissionPower(f, is5G= True)
    hp.writeSeparation(f, "Channel Control")
    hp.writeCarrierAggregation5G(f,carriers_frequencies = [scen.carrier_frequency])
    hp.writeSeparation(f, "Channel Model")
    hp.writeChannelModel5G(f, tolerateMaxDistViolation= True, extCell_interference= False)
    hp.writeSeparation(f, "Resource Blocks")
    hp.writeResourceBlocks(f, 6, is5G= True)
    hp.writeSeparation(f, "UEs")
    hp.writeNumUEs(f, num_ues)
    hp.writeComment(f, text= "Conecting UEs to eNodeB")
    hp.writeConnectUE(f, UEs= [num_ues], ENBs= [1])
    hp.writeComment(f, text= "Scheduler")
    hp.writeSchedulingOptions(f, sched= ['MAXCI'])
    hp.writeSeparation(f, "Scenario")
    hp.writeComment(f, text= "UEs")
    hp.writeScenarioPerso(f, num_and_scen=[(num_ues, 'URBAN_MACROCELL')], for5g= True)
    hp.writeSeparation(f, "Mobility")
    hp.writeComment(f, text= "UEs")
    hp.nl(f)
    hp.writeMobilityType(f, type= "VariableSpeedMobility", object_name= "ue[*]")
    hp.writeVarSpeedMobDefault(f, speed_mean= 3000, std_dev= 1000, object_name= "ue[*]", update_interval= 1)
    hp.writeArrayIniMobility(f, object_array_name= 'ue', coordinates= ues_coords)
    hp.writeArrayMovMobility(f, object_array_name= 'ue', movements= ues_mov, fixed_speed= False)
    hp.writeConstraint(f, object_name= 'ue[*]', maxX=size_x, minX=0, maxY=size_y, minY= 0)

def ilp_fixed_ini(filename, seed, size_y:int =8000, size_x:int =8000, size_sector:int =800, n_macros: int = 2, antennas_regions: List[int] = [], min_sinr: float = 10, repetitions: int = 5,
                  num_bands: List[int] = [100], multi_carriers: bool = True, time:float = 10, is_micro: bool = True, p_size: int = 40, app: str= "voip", extra_config_name = ''):
  """This function generates a .ini file to create a simulation with multiple UEs and eNBs with handover enabled.
  
  The simulation configured with the resulting file has the purpose of generate data about the behaviour of all elements involved in the simulation throughout a single simulation.

  The ues and server are communicating using VoIP UL and DL applications.

  Args:
    filename: string representing the name of the resulting file
    seed: integer used as seed in the distribuition of ues and the simulation
	  size_y: y dimension size of considered region in meters
    size_x: x dimension size of considered region in meters
    size_sector: sides size of square sectors in meters
    n_macros: number of macrocells considered to distribute the ues on the map
    antennas_regions: list of the sectors where eNBs should be deployed
    min_sinr: number of the minimum sinr value used to generate the eNBs locations (ccop_mv_MILP)
    repetitions: number of repetitions to be executed in the simulation
    num_bands: list of the possible number of resource blocks to be used in the simulation
    multi_carriers: if True, the eNBs will suport more than one type of carrier
    time: total time of the simulation in seconds
    is_micro: if True, the eNBs will be Low Power Nodes and the simulation will use the UrbanMicrocell scenario
<<<<<<< HEAD
    extra_config_name: string to be added at the end of the configuration name
=======
    p_size: size of package used on the VoIP or Video Streaming application (in bytes)
    app: type of application (voip or video)
>>>>>>> MacroToMicro
  """

  scen = geo.MapChess(size_y, size_x, size_sector, carrier_frequency= 0.7, chosen_seed= seed, scenario= "URBAN_MICROCELL" if is_micro else "URBAN_MACROCELL",
                      enb_tx_power= 30 if is_micro else 46, h_enbs= 18, gain_ue= -1, enb_noise_figure= 9)

  scen.placeUEs(type= "Random", n_macros= n_macros, n_ues_macro= 60)#Full = 4320 UEs
  scen.placeAntennas(list_regions= antennas_regions)

  ues_coords = scen.getUEsPositionList()
  ues_mov = scen.getUEsMovementList()
  enbs_coords = scen.getAntennasPositionList()

  num_ues = len(ues_coords)
  num_enbs = len(enbs_coords)

  config_name = 'Config ilp_fixed_{}'.format(min_sinr) + ('_carriers' if multi_carriers else '') + ('_' + extra_config_name if extra_config_name != '' else '')

  with open(filename, 'wt') as f:
    hp.writeCommentConfigILP(f, "ilp_fixed", filename, seed, size_y, size_x, size_sector, extra = 'Using {} macros with {} ues each.'.format(n_macros, 60))
    hp.defaultGeneral(f, is5g= True)
    hp.makeNewConfig(f, name= config_name)
    hp.writeNetwork(f, network= '_5G.networks.ILPFixedNet')
    hp.writeTime(f, time= time, repeat= repetitions)
    hp.writeSeeds(f, num_rngs= 2, seeds= [seed])
    hp.nl(f)
    hp.writeVectorExtra(f, module= "**.eNB*.cellularNic.channelModel[*]", statistic= "*", value= True)
    hp.writeOutput(f, "${resultdir}/${configname}/"+str(min_sinr)+"-${repetition}-${RBs}")
    hp.writeSeparation(f, "Snapshots")
    hp.writeSnapshotsConfig(f, filename= "../../../Functions/${configname}-${iterationvarsf}-"+str(min_sinr)+"-${repetition}.sna", snapshot= False)
    hp.writeSeparation(f, "Transmission Power")
    hp.writeTransmissionPower(f, is5G= True)
    hp.writeSeparation(f, "Channel Control")
    if multi_carriers:
      hp.writeCarrierAggregation5G(f, num_carriers= len(antennas_regions), carriers_frequencies= [scen.carrier_frequency - 0.02*np.max(num_bands)*i/100 for i in range(len(antennas_regions))], eNBs_carriers= True)
    else:
      hp.writeCarrierAggregation5G(f, carriers_frequencies= [scen.carrier_frequency])
    hp.writeSeparation(f, "Channel Model")
    hp.writeChannelModel5G(f, model_name= "MoreInfoChannelModel" ,tolerateMaxDistViolation= True, extCell_interference= False, building_height= scen.h_building, nodeb_height= scen.h_enbs,
                           ue_height= scen.h_ues, street_wide= scen.w_street, antennGainEnB= scen.gain_enb, antennaGainUe= scen.gain_ue, bs_noise_figure= scen.enb_noise_figure, ue_noise_figure= scen.ue_noise_figure,
                           cable_loss= scen.cable_loss, thermalNoise= scen.thermal_noise, fixed_los= scen.los)
    hp.writeSeparation(f, "Resource Blocks")
    hp.writeResourceBlocksOptions(f, "RBs", num_bands, is5G= True)
    if is_micro:
      hp.writeSeparation(f, "eNBs")
      hp.writeMultiMicro(f, num_enbs, node_name = "eNB")
    hp.writeSeparation(f, "UEs")
    hp.writeNumUEs(f, num_ues)
    hp.writeComment(f, text= "Conecting UEs to eNodeB")
    hp.writeConnectUE(f, UEs= [num_ues], ENBs= [1])
    hp.writeComment(f, text= "Scheduler")
    hp.writeSchedulingOptions(f, sched= ['MAXCI'])
    hp.writeSeparation(f, "Scenario")
    hp.writeComment(f, text= "eNodeBs")
    hp.writeMultiScenarios(f, object_name= 'eNB', num= num_enbs, scenario= scen.scenario, for5g= True)
    hp.writeComment(f, text= "UEs")
    hp.writeScenarioPerso(f, num_and_scen=[(num_ues, scen.scenario)], for5g= True)
    hp.writeSeparation(f, "Mobility")
    hp.writeComment(f, text= "eNodeB")
    hp.writeMultiIniMobility(f,object_name= 'eNB', coordinates= enbs_coords)
    hp.writeConstraint(f, object_name= 'eNB*', maxX=size_x, minX=0, maxY=size_y, minY= 0)
    hp.writeComment(f, text= "UEs")
    hp.nl(f)
    hp.writeMobilityType(f, type= "VariableSpeedMobility", object_name= "ue[*]")
    hp.writeVarSpeedMobDefault(f, speed_mean= 3000*10/time, std_dev= 1000*10/time, object_name= "ue[*]", update_interval= 1*time/10)
    hp.writeArrayIniMobility(f, object_array_name= 'ue', coordinates= ues_coords)
    hp.writeArrayMovMobility(f, object_array_name= 'ue', movements= ues_mov, fixed_speed= False)
    hp.writeConstraint(f, object_name= 'ue[*]', maxX=size_x, minX=0, maxY=size_y, minY= 0)
    hp.writeSeparation(f, "Apps")
    if app.upper() == "VOIP":
      hp.writeNumApps(f, numUEs= num_ues, directions= 2, multi= False)
      hp.writeComment(f, text= "VoIP UL")
      hp.writeAppVoipUL(f, num_ues, n_app= 0, p_size= p_size)
      hp.writeComment(f, text= "VoIP DL")
      hp.writeAppVoipDL(f, num_ues, n_app= 1, p_size= p_size)
    elif app.upper() == "VIDEO":
      hp.writeNumApps(f, numUEs= num_ues, directions= 1, multi= False)
      hp.writeComment(f, text= "Video Streaming DL")
      hp.writeAppVideoDL(f, p_size= p_size)
      

    hp.writeSeparation(f, "Handover")
    hp.writeComment(f, text= "Enable handover")
    hp.writeEnableHandover(f, object_name= "eNB*", enable= True, is5G= True)
    hp.writeEnableHandover(f, object_name= "ue[*]", enable= True, is5G= True)
    hp.writeComment(f, text= "X2 configuration")
    hp.writeX2Configuration(f, object_name= "eNB*", quantity= num_enbs) #Connections between enbs
    hp.writeComment(f, text= "Connections")
    hp.writeX2Connections(f, object_names = ["eNB"], quantities= [num_enbs], initial_values= [0])

def ilp_fixed_sliced_ini(filename, seed, size_y:int =8000, size_x:int =8000, size_sector:int =800, n_macros: int = 2, min_sinr: float = 10, repetitions: int = 5,
                  num_bands: List[int] = [100], multi_carriers: bool = True, time:float = 1, is_micro: bool = True, p_size: int = 40, app: str= "voip", extra_config_name = ''):
  """This function generates a .ini file to create a simulation with multiple UEs and eNBs using slices of time.
  
  The simulation configured with the resulting file has the purpose of generate data about the behaviour of all elements involved thoughout multiple slices (simulations),
  each one being the continuation of the previous one, resulting in a single event.
  
  The simulation doesn't use the handover process, making the changes of serving cells in the setup of each slice.

  The ues and server are communicating using VoIP UL and DL applications.

  Args:
    filename: string representing the name of the resulting file
    seed: integer used as seed in the distribuition of ues and the simulation
	  size_y: y dimension size of considered region in meters
    size_x: x dimension size of considered region in meters
    size_sector: sides size of square sectors in meters
    n_macros: number of macrocells considered to distribute the ues on the map
    min_sinr: number of the minimum sinr value used to generate the eNBs locations (ccop_mv_MILP)
    repetitions: number of repetitions to be executed in the simulation
    num_bands: list of the possible number of resource blocks to be used in the simulation
    multi_carriers: if True, the eNBs will suport more than one type of carrier
    time: total time of the simulation in seconds
    is_micro: if True, the eNBs will be Low Power Nodes and the simulation will use the UrbanMicrocell scenario
<<<<<<< HEAD
    extra_config_name: string to be added at the end of the configuration name
=======
    p_size: size of package used on the VoIP or Video Streaming application (in bytes)
    app: type of application (voip or video)
>>>>>>> MacroToMicro
  """

  scen = geo.MapChess(size_y, size_x, size_sector, carrier_frequency= 0.7, chosen_seed= seed, scenario= "URBAN_MICROCELL" if is_micro else "URBAN_MACROCELL",
                      enb_tx_power= 30 if is_micro else 46, h_enbs= 18, gain_ue= -1, enb_noise_figure= 9)
  scen.placeUEs(type= "Random", n_macros= n_macros, n_ues_macro= 60)#Full = 4320 UEs

  xml_filename= 'ilp_fixed_users-sched=MAXCI--0.sna'
  ues_in_time = hxml.get_ues_time(scen.getUEsList(), xml_filename, time)

  iter_slice_name = "Slice"
  num_slices = len(ues_in_time)

  optimized, antennas_regions = parse_results("result_"+ str(min_sinr)+".txt", num_slices)

  scen.placeAntennas(list_regions= antennas_regions)

  ues_coords = []
  ues_mov = []
  for slice in ues_in_time:
    ues_coords.append([ue.position for ue in slice])
    ues_mov.append([ue.movement for ue in slice])
  ues_coords = np.swapaxes(ues_coords, 0, 1).tolist()
  ues_mov = np.swapaxes(ues_mov, 0, 1).tolist()

  enbs_coords = scen.getAntennasPositionList()

  num_ues = len(scen.getUEsList())
  num_enbs = len(enbs_coords)

  connections = getUesConnections(optimized, ues_coords, antennas_regions, size_sector, size_x, size_y)

  config_name = 'Config ilp_fixed_sliced_{}'.format(min_sinr) + ('_carriers' if multi_carriers else '') + ('_' + extra_config_name if extra_config_name != '' else '')

  with open(filename, 'wt') as f:
    hp.writeCommentConfigILP(f, "ilp_fixed", filename, seed, size_y, size_x, size_sector, extra = 'Using {} macros with {} ues each. Slicing 10s in 10 different simulations. Using microcells.'.format(n_macros, 60))
    hp.defaultGeneral(f, is5g= True)
    hp.makeNewConfig(f, name= config_name)
    hp.writeNetwork(f, network= '_5G.networks.ILPFixedNet')
    hp.writeTime(f, time= time, repeat= repetitions)
    hp.writeSeeds(f, num_rngs= 2, seeds= [seed])
    hp.nl(f)
    hp.writeVectorExtra(f, module= "**.eNB*.cellularNic.channelModel[*]", statistic= "*", value= True)
    hp.writeOutput(f, "${resultdir}/${configname}/"+str(min_sinr)+"-${RBs}-${repetition}-${Slice}")
    hp.writeSeparation(f, "Snapshots")
    hp.writeSnapshotsConfig(f, filename= "../../../Functions/${configname}-RBs_${RBs}-Slice_${Slice}-"+str(min_sinr)+"-${repetition}.sna", snapshot= False)
    hp.writeSeparation(f, "Transmission Power")
    hp.writeTransmissionPower(f, is5G= True)
    hp.writeSeparation(f, "Channel Control")
    if multi_carriers:
      hp.writeCarrierAggregation5G(f, num_carriers= len(antennas_regions), carriers_frequencies= [scen.carrier_frequency - 0.02*np.max(num_bands)*i/100 for i in range(len(antennas_regions))], eNBs_carriers= True)
    else:
      hp.writeCarrierAggregation5G(f, carriers_frequencies= [scen.carrier_frequency])
    hp.writeSeparation(f, "Channel Model")
    hp.writeChannelModel5G(f, model_name= "MoreInfoChannelModel" ,tolerateMaxDistViolation= True, extCell_interference= False, building_height= scen.h_building, nodeb_height= scen.h_enbs,
                           ue_height= scen.h_ues, street_wide= scen.w_street, antennGainEnB= scen.gain_enb, antennaGainUe= scen.gain_ue, bs_noise_figure= scen.enb_noise_figure, ue_noise_figure= scen.ue_noise_figure,
                           cable_loss= scen.cable_loss, thermalNoise= scen.thermal_noise, fixed_los= scen.los)
    hp.writeSlices(f, num_slices= num_slices, iter_name= iter_slice_name)
    hp.writeSeparation(f, "Resource Blocks")
    hp.writeResourceBlocksOptions(f, "RBs", num_bands, is5G= True)
    if is_micro:
      hp.writeSeparation(f, "eNBs")
      hp.writeMultiMicro(f, num_enbs, node_name = "eNB")
    hp.writeSeparation(f, "UEs")
    hp.writeNumUEs(f, num_ues)
    hp.writeComment(f, text= "Conecting UEs to eNodeB")
    #hp.writeConnectUE(f, UEs= [num_ues], ENBs= [1])
    hp.writeConnectOptions(f, list_connections= connections, parallel_var= iter_slice_name)
    hp.writeComment(f, text= "Scheduler")
    hp.writeSchedulingOptions(f, sched= ['MAXCI'])
    hp.writeSeparation(f, "Scenario")
    hp.writeComment(f, text= "eNodeBs")
    hp.writeMultiScenarios(f, object_name= 'eNB', num= num_enbs, scenario= scen.scenario, for5g= True)
    hp.writeComment(f, text= "UEs")
    hp.writeScenarioPerso(f, num_and_scen=[(num_ues, scen.scenario)], for5g= True)
    hp.writeSeparation(f, "Mobility")
    hp.writeComment(f, text= "eNodeB")
    hp.writeMultiIniMobility(f,object_name= 'eNB', coordinates= enbs_coords)
    hp.writeConstraint(f, object_name= 'eNB*', maxX=size_x, minX=0, maxY=size_y, minY= 0)
    hp.writeComment(f, text= "UEs")
    hp.nl(f)
    hp.writeMobilityType(f, type= "LinearMobility", object_name= "ue[*]")
    #hp.writeVarSpeedMobDefault(f, speed_mean= 3000, std_dev= 1000, object_name= "ue[*]", update_interval= 1)
    hp.writeArrayIniMobility(f, object_array_name= 'ue', coordinates= ues_coords, paral_name= iter_slice_name)
    hp.writeArrayMovMobility(f, object_array_name= 'ue', movements= ues_mov, fixed_speed= True, paral_name= iter_slice_name)
    hp.writeConstraint(f, object_name= 'ue[*]', maxX=size_x, minX=0, maxY=size_y, minY= 0)
    hp.writeSeparation(f, "Apps")
    if app.upper() == "VOIP":
      hp.writeNumApps(f, numUEs= num_ues, directions= 2, multi= False)
      hp.writeComment(f, text= "VoIP UL")
      hp.writeAppVoipUL(f, num_ues, n_app= 0, p_size= p_size)
      hp.writeComment(f, text= "VoIP DL")
      hp.writeAppVoipDL(f, num_ues, n_app= 1, p_size= p_size)
    elif app.upper() == "VIDEO":
      hp.writeNumApps(f, numUEs= num_ues, directions= 1, multi= False)
      hp.writeComment(f, text= "Video Streaming DL")
      hp.writeAppVideoDL(f, p_size= p_size)

def ilp_fixed_ned(network:str = "ILPFixedNet", size_y:int =8000, size_x:int =8000, image:str =None, n_enbs: int = 2):
  """This function generates a .ned file to create a network with multiple UEs and eNBs.
  
  The network created include the default and necessary submodules to ensure a correct Simu5G simulation.

  Args:
    network: string representing the new network name
	  size_y: y dimension size of considered region in meters
    size_x: x dimension size of considered region in meters
    size_sector: sides size of square sectors in meters
    image: string representing the image path to be used as a background
    n_enbs: the number of eNBs composing the network
  """

  filename = "../Network_CCOpMv/_5G/networks/{}.ned".format(network)

  with open(filename, 'wt') as f:
    hned.writeBaseImports(f, is5g= True, snapshot= True)
    hned.writeNet(f, net_name= network)
    hned.writeParams(f, bg_x= size_x, bg_y = size_y, bg_image= image)
    hned.writeBaseSubmodules(f, is5g= True)
    hned.writeMultiNode(f, quantity= n_enbs)
    hned.writeSubmodule(f, name= "ue[numUe]", type= "Ue", size= "s")
    hned.writeSnapshotter(f, submodule_size= 's')
    hned.writeConnections(f, base= True)
    hned.writeMultiNodeConnections(f, object_name= "eNB" , quantity= n_enbs)
    hned.writeSeparation(f, "X2 Connections")
    hned.writeX2Connections(f, object_names=["eNB"], quantities= [n_enbs])
    hned.writeEndNet(f)

def parse_results(filename: str, slices_num: int):
  """This function parses the UEs and eNBs necessary information from the solver (ccop_mv_MILP) resulted solution.

  Args:
    filename: string representing the name of the txt file with the solution
    slices_num: number of slices used

  Return:
    Two structures. The first one is a list of dict (results[t]{n: m}) where t is the simulation time, n is the sector of a UE at that time and m is the sector of its serving cell.
    The second one is a list with the sectors where the eNBs were located (List[int]).
  """

  results = []
  enbs = []
  for i in range(slices_num):
    results.append({})

  with open(filename, "r") as f:
    for line in f:
      data = [int(x) for x in line.split()]
      results[data[0]][data[2]] = data[1]
      enbs.append(data[1])
      enbs = np.unique(enbs).tolist()

  return results, enbs

def getUesConnections(result, ues_coords, antennas_regions: List[int], size_sector, size_x, size_y):
  """This function interpretates the result parsed from the solver in to the elements connections.

  Args:
    result: List[Dict] containing the parsed solution from the solver
    ues_coords: 2D Matrix (n X t) with the coordinates of each UE (n) at each time of simulation (t).
    antennas_regions: List[int] containing the sectors where eNBs are located
    size_sector: sides size of square sectors in meters
    size_x: x dimension size of considered region in meters
    size_y: y dimension size of considered region in meters

  Return:
    A 2D Matrix (n X t) with the serving cell number for each UE (n) at each time (t).
  """

  connections = []
  for ue in ues_coords:
    connections.append([])
    for s in range(len(ue)):
      region = geo.coord2Region(ue[s], size_sector, size_x, size_y)
      #Assume-se que a regiao do UE é servida por alguma das antenas
      connections[-1].append(antennas_regions.index(result[s][region])+1)

  return connections

