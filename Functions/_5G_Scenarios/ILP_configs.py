from typing import List
import helper as hp
import helper_ned as hned
import helper_xml as hxml
import geometry as geo
import numpy as np
from errors import check_mode
import general_functions as genf

def ilp_move_users(filename: str, seed: int, size_y:int =8000, size_x:int =8000, size_sector:int =800, n_macros: int = 2, config_name: str= 'ilp_move_users',
                   num_slices: int= 10):
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
    config_name: name of the configuration used in the .ini file
    num_slices: number of slices in the simulation
  """

  #Dict with the parameters used (must be the first operation in the function)
  dict_args = locals()

  scen = geo.MapChess(size_y, size_x, size_sector, carrier_frequency= 0.7, chosen_seed= seed)
  scen.placeUEs(type= "Random", n_macros= n_macros)#Full = 4320 UEs

  ues_coords = scen.getUEsPositionList()
  ues_mov = scen.getUEsMovementList()
  #scen.plotUes()
  num_ues = len(ues_coords)

  with open(filename, 'wt') as f:
    hp.writeCommentConfigILP(f, "ilp_move_users", dict_args, extra = 'Using {} macros with {} ues each.'.format(n_macros, 60))
    hp.defaultGeneral(f, is5g= True)
    hp.makeNewConfig(f, name= config_name)
    hp.writeNetwork(f, network= '_5G.networks.SimpleNet')
    hp.writeTime(f, time= num_slices, repeat= 1)
    hp.writeSeeds(f, num_rngs= 2, seeds= [seed])
    hp.nl(f)
    hp.writeOutput(f, "${resultdir}/${configname}/${repetition}")
    hp.writeSeparation(f, "Snapshots")
    hp.writeSnapshotsConfig(f, filename= "../../../Functions/" + genf.gen_movement_filename(config_name, seed, snapshot= True), snapshot= True, delay= 1)
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

def ilp_hando_fixed_ini(filename, seed, size_y:int =8000, size_x:int =8000, size_sector:int =800, n_macros: int = 2, antennas_regions: List[int] = [], min_sinr: float = 10, repetitions: int = 5,
                  num_bands: List[int] = [100], multi_carriers: bool = True, time:int = 10, is_micro: bool = True, p_size: int = 40, app: str= "voip",  target_f:int = 20,
                  extra_config_name: str = '', result_dir: str = '.', network_name: str = '', cmdenv_config: bool = False, xml_filename: str= 'ilp_fixed_users-sched=MAXCI--0.sna'):
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
    p_size: size of package used on the VoIP or Video Streaming application (in bytes)
    app: type of application (voip or video)
    target_f: target throughput considered to compute sendInterval, used by the Video Streaming application
    extra_config_name: string to be added at the end of the configuration name
    result_dir: directory with the solver results in .txt files (used if antennas_regions == [])
    network_name: if diferent than '' is used as the network of the configuration
    cmdenv_config: tells if cmdenv should be configured to not display the performance and redirect its output
    xml_filename: name of the snapshot file containing the movement caracteristics of the users
  """

  #Dict with the parameters used (must be the first operation in the function)
  dict_args = locals()

  scen = geo.MapChess(size_y, size_x, size_sector, carrier_frequency= 0.7, chosen_seed= seed, scenario= "URBAN_MICROCELL" if is_micro else "URBAN_MACROCELL",
                      enb_tx_power= 30 if is_micro else 46, h_enbs= 18, gain_ue= -1, enb_noise_figure= 9)

  scen.placeUEs(type= "Random", n_macros= n_macros, n_ues_macro= 60)#Full = 4320 UEs

  if antennas_regions == []:
    ues_map = hxml.get_map_ues_time(scen= scen, xml_filename = xml_filename)

    max_time = len(ues_map)
    _, antennas_regions, _ = parse_results(genf.gen_solver_result_filename(result_dir, 'fixed', min_sinr)+".txt", max_time)

  scen.placeAntennas(list_regions= antennas_regions)

  ues_coords = scen.getUEsPositionList()
  ues_mov = scen.getUEsMovementList()
  enbs_coords = scen.getAntennasPositionList()

  num_ues = len(ues_coords)
  num_enbs = len(enbs_coords)

  config_name = 'ilp_fixed_hando_{}'.format(min_sinr) + ('_carriers' if multi_carriers else '') + ('_' + extra_config_name if extra_config_name != '' else '')

  s_interval= 1000/((target_f*10**6)/(8*p_size)) # ms

  network_full_name = network_full_name = '_5G.networks.' + ('ILPFixedNet' if network_name == '' else network_name)


  with open(filename, 'wt') as f:
    hp.writeCommentConfigILP(f, "ilp_fixed_ini", dict_args= dict_args, extra = 'Using {} macros with {} ues each.'.format(n_macros, 60))
    hp.defaultGeneral(f, is5g= True)
    hp.makeNewConfig(f, name= config_name)
    hp.writeNetwork(f, network= network_full_name)
    hp.writeTime(f, time= time, repeat= repetitions)
    hp.writeSeeds(f, num_rngs= 2, seeds= [seed])
    hp.writeSeparation(f, "Outputs")
    hp.writeVectorExtra(f, module= "**.eNB*.cellularNic.channelModel[*]", statistic= "idRcvdSinr:vector", value= True)
    hp.writeVectorExtra(f, module= "**.eNB*.cellularNic.channelModel[*]", statistic= "rcvdSinr:vector", value= True)
    hp.writeVectorExtra(f, module= "**.app[*]", statistic= "throughput:vector", value= True)
    hp.writeVectorExtra(f, module= "**.app[*]", statistic= "endToEndDelay:vector", value= True)
    hp.writeOutput(f, "${resultdir}/" + config_name + "/"+str(min_sinr)+"-${repetition}-${RBs}")
    if cmdenv_config:
      hp.writeSeparation(f, "Cmdenv")
      hp.writeCmdenvConfig(f, min_sinr= min_sinr, performance_display = False, redirect_output= True)
    hp.writeSeparation(f, "Snapshots")
    hp.writeSnapshotsConfig(f, filename= "../../../Functions/"+ config_name + "-${iterationvarsf}-"+str(min_sinr)+"-${repetition}.sna", snapshot= False)
    hp.writeSeparation(f, "Transmission Power")
    hp.writeTransmissionPower(f, is5G= True)
    hp.writeSeparation(f, "Channel Control")
    if multi_carriers:
      hp.writeCarrierAggregation5G(f, num_carriers= len(antennas_regions), carriers_frequencies= [scen.carrier_frequency - 0.02*np.max(num_bands)*i/100 for i in range(len(antennas_regions))], eNBs_carriers= True)
    else:
      hp.writeCarrierAggregation5G(f, carriers_frequencies= [scen.carrier_frequency])
    hp.writeSeparation(f, "Channel Model")
    hp.writeChannelModel5G(f, model_name= "MoreInfoChannelModel", tolerateMaxDistViolation= True, extCell_interference= False, building_height= scen.h_building, nodeb_height= scen.h_enbs,
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
      hp.writeNumApps(f, numUEs= num_ues, directions= 2, multi= False)
      hp.writeComment(f, text= "Video Streaming UL")
      hp.writeAppVideoUL(f, numUEs= num_ues, p_size= p_size, n_app= 0, mtu= False, s_interval= s_interval)
      hp.writeComment(f, text= "Video Streaming DL")
      hp.writeAppVideoDL(f, numUEs= num_ues, p_size= p_size, n_app= 1, mtu= True, s_interval= s_interval)

    hp.writeSeparation(f, "Handover")
    hp.writeComment(f, text= "Enable handover")
    hp.writeEnableHandover(f, object_name= "eNB*", enable= True, is5G= True)
    hp.writeEnableHandover(f, object_name= "ue[*]", enable= True, is5G= True)
    hp.writeComment(f, text= "X2 configuration")
    hp.writeX2Configuration(f, object_name= "eNB*", quantity= num_enbs) #Connections between enbs
    hp.writeComment(f, text= "Connections")
    hp.writeX2Connections(f, object_names = ["eNB"], quantities= [num_enbs], initial_values= [0])

  return config_name, num_enbs

def ilp_sliced_ini(filename, seed, size_y:int =8000, size_x:int =8000, size_sector:int =800, n_macros: int = 2, min_sinr: float = 10, repetitions: int = 5,
                  num_bands: List[int] = [100], multi_carriers: bool = True, slice_time:int = 1, is_micro: bool = True, p_size: int = 40, app: str= "voip", target_f:int = 10,
                  extra_config_name: str = '', result_dir: str = '.', mode: str = '', network_name: str = '', net_dir: str= '_5G/networks',
                  cmdenv_config: bool = False, micro_power: int = 30, xml_filename: str= 'ilp_fixed_users-sched=MAXCI--0.sna'):
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
    slice_time: total time of each slice of the simulation in seconds
    is_micro: if True, the eNBs will be Low Power Nodes and the simulation will use the UrbanMicrocell scenario
    p_size: size of package used on the VoIP or Video Streaming application (in bytes)
    app: type of application (voip or video)
    target_f: target throughput considered to compute sendInterval, used by the Video Streaming application
    extra_config_name: string to be added at the end of the configuration name
    result_dir: directory with the solver results in .txt files
    mode: if varying use ILP_varying_in_time results else if single use ILP_single else if fixed use ILP_fixed_in_time results
    network_name: if diferent than '' is used as the network of the configuration
    net_dir: directory containing the network
    cmdenv_config: tells if cmdenv should be configured to not display the performance and redirect its output
    micro_power: defines the transmission power used when is_micro is True
    xml_filename: name of the snapshot file containing the movement caracteristics of the users
  """
  #Dict with the parameters used (must be the first operation in the function)
  dict_args = locals()

  scen = geo.MapChess(size_y, size_x, size_sector, carrier_frequency= 0.7, chosen_seed= seed, scenario= "URBAN_MICROCELL" if is_micro else "URBAN_MACROCELL",
                      enb_tx_power= micro_power if is_micro else 46, h_enbs= 18, gain_ue= -1, enb_noise_figure= 9)
  scen.placeUEs(type= "Random", n_macros= n_macros, n_ues_macro= 60)#Full = 4320 UEs

  ues_in_time = hxml.get_ues_time(scen.getUEsList(), xml_filename, slice_time)

  iter_slice_name = "Slice"
  num_slices = len(ues_in_time)

  check_mode(mode= mode)

  optimized, antennas_regions, num_enbs_time = parse_results(genf.gen_solver_result_filename(result_dir, mode, min_sinr), num_slices)

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

  connections = get_ues_connections(optimized, ues_coords, antennas_regions, size_sector, size_x, size_y)

  config_name = genf.gen_sliced_config_pattern(min_sinr, mode, multi_carriers, extra_config_name)

  s_interval= 1000/((target_f*10**6)/(8*p_size)) # ms

  network_full_name = hned.dir_to_package(net_dir) + (f'ILP{mode.capitalize()}Net' if network_name == '' else network_name)

  with open(filename, 'wt') as f:
    hp.writeCommentConfigILP(f, 'ilp_sliced_ini', dict_args= dict_args, extra = 'Using {} macros with {} ues each. Slicing 10s in 10 different simulations. Using microcells.'.format(n_macros, 60))
    hp.defaultGeneral(f, is5g= True)
    hp.makeNewConfig(f, name= config_name)
    hp.writeNetwork(f, network= network_full_name)
    hp.writeTime(f, time= slice_time, repeat= repetitions)
    hp.writeSeeds(f, num_rngs= 2, seeds= [seed])
    hp.writeSeparation(f, "Outputs")
    hp.writeVectorExtra(f, module= "**.eNB*.cellularNic.channelModel[*]", statistic= "idRcvdSinr:vector", value= True)
    hp.writeVectorExtra(f, module= "**.eNB*.cellularNic.channelModel[*]", statistic= "rcvdSinr:vector", value= True)
    hp.writeVectorExtra(f, module= "**.app[*]", statistic= "throughput:vector", value= True)
    hp.writeVectorExtra(f, module= "**.app[*]", statistic= "endToEndDelay:vector", value= True)
    hp.writeOutput(f, "${resultdir}/"+ config_name +"/"+str(min_sinr)+"-${RBs}-${repetition}-${Slice}")
    if cmdenv_config:
      hp.writeSeparation(f, "Cmdenv")
      hp.writeCmdenvConfig(f, config_name= config_name, min_sinr= min_sinr, performance_display = False, redirect_output= True)
    hp.writeSeparation(f, "Snapshots")
    hp.writeSnapshotsConfig(f, filename= "../../../Functions/" + config_name + "-RBs_${RBs}-Slice_${Slice}-"+str(min_sinr)+"-${repetition}.sna", snapshot= False)
    hp.writeSeparation(f, "Transmission Power")
    hp.writeTransmissionPower(f, micro_power= micro_power, is5G= True)
    hp.writeSeparation(f, "Channel Control")
    if multi_carriers:
      hp.writeCarrierAggregation5G(f, num_carriers= len(antennas_regions), carriers_frequencies= [scen.carrier_frequency - 0.02*np.max(num_bands)*i/100 for i in range(len(antennas_regions))], eNBs_carriers= True)
    else:
      hp.writeCarrierAggregation5G(f, carriers_frequencies= [scen.carrier_frequency])
    hp.writeSeparation(f, "Channel Model")
    hp.writeChannelModel5G(f, model_name= "MoreInfoChannelModel", tolerateMaxDistViolation= True, extCell_interference= False, building_height= scen.h_building, nodeb_height= scen.h_enbs,
                           ue_height= scen.h_ues, street_wide= scen.w_street, antennGainEnB= scen.gain_enb, antennaGainUe= scen.gain_ue, bs_noise_figure= scen.enb_noise_figure, ue_noise_figure= scen.ue_noise_figure,
                           cable_loss= scen.cable_loss, thermalNoise= scen.thermal_noise, fixed_los= scen.los)
    hp.writeSlices(f, num_slices= num_slices, iter_name= iter_slice_name)
    hp.writeNumEnbs(f, options= num_enbs_time, iter_name= 'NumEnbs', parallel_name= iter_slice_name)
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
      hp.writeNumApps(f, numUEs= num_ues, directions= 2, multi= False)
      hp.writeComment(f, text= "Video Streaming UL")
      hp.writeAppVideoUL(f, numUEs= num_ues, p_size= p_size, n_app= 0, mtu= False, s_interval= s_interval)
      hp.writeComment(f, text= "Video Streaming DL")
      hp.writeAppVideoDL(f, numUEs= num_ues, p_size= p_size, n_app= 1, mtu= True, s_interval= s_interval)

  return config_name, num_enbs

def ilp_sliced_ini_per_slice(filename, seed, size_y:int =8000, size_x:int =8000, size_sector:int =800, n_macros: int = 2, min_sinr: float = 10, repetitions: int = 5,
                             num_bands: List[int] = [100], multi_carriers: bool = True, slice_time:int = 1, is_micro: bool = True, p_size: int = 40, app: str= "voip", target_f:int = 10,
                             extra_config_name: str = '', result_dir: str = '.', mode: str = '', network_name: str = '', net_dir: str= '_5G/networks',
                             cmdenv_config: bool = False, micro_power: int = 30, xml_filename: str= 'ilp_fixed_users-sched=MAXCI--0.sna'):
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
    slice_time: total time of each slice of the simulation in seconds
    is_micro: if True, the eNBs will be Low Power Nodes and the simulation will use the UrbanMicrocell scenario
    p_size: size of package used on the VoIP or Video Streaming application (in bytes)
    app: type of application (voip or video)
    target_f: target throughput considered to compute sendInterval, used by the Video Streaming application
    extra_config_name: string to be added at the end of the configuration name
    result_dir: directory with the solver results in .txt files
    mode: if varying use ILP_varying_in_time results else if single use ILP_single else if fixed use ILP_fixed_in_time results
    network_name: if diferent than '' is used as the network of the configuration
    net_dir: directory containing the network
    cmdenv_config: tells if cmdenv should be configured to not display the performance and redirect its output
    micro_power: defines the transmission power used when is_micro is True
    xml_filename: name of the snapshot file containing the movement caracteristics of the users
  """
  #Dict with the parameters used (must be the first operation in the function)
  dict_args = locals()

  scen = geo.MapChess(size_y, size_x, size_sector, carrier_frequency= 0.7, chosen_seed= seed, scenario= "URBAN_MICROCELL" if is_micro else "URBAN_MACROCELL",
                      enb_tx_power= micro_power if is_micro else 46, h_enbs= 18, gain_ue= -1, enb_noise_figure= 9)
  scen.placeUEs(type= "Random", n_macros= n_macros, n_ues_macro= 60)#Full = 4320 UEs

  ues_in_time = hxml.get_ues_time(scen.getUEsList(), xml_filename, slice_time)

  iter_slice_name = "Slice"
  num_slices = len(ues_in_time)

  check_mode(mode= mode)

  list_scen = []
  for i in range(num_slices):
    tmp_scen = geo.MapChess(size_y, size_x, size_sector, carrier_frequency= 0.7, chosen_seed= seed, scenario= "URBAN_MICROCELL" if is_micro else "URBAN_MACROCELL",
                      enb_tx_power= micro_power if is_micro else 46, h_enbs= 18, gain_ue= -1, enb_noise_figure= 9)
    tmp_scen.placeUEs(type= "Random", n_macros= n_macros, n_ues_macro= 60)#Full = 4320 UEs
    list_scen.append(tmp_scen)

  optimized_byslice, antennas_regions_byslice, num_enbs_time = parse_results_per_slice(genf.gen_solver_result_filename(result_dir, mode, min_sinr), num_slices)

  if optimized_byslice == None and antennas_regions_byslice == None and num_enbs_time == None:
    #There was a not feasible solution
    return None, None
  
  for i in range(len(antennas_regions_byslice)):
    list_scen[i].placeAntennas(list_regions= antennas_regions_byslice[i])
    
  ues_coords = []
  ues_mov = []
  for slice in ues_in_time:
    ues_coords.append([ue.position for ue in slice])
    ues_mov.append([ue.movement for ue in slice])
  ues_coords = np.swapaxes(ues_coords, 0, 1).tolist()
  ues_mov = np.swapaxes(ues_mov, 0, 1).tolist()

  enbs_coords_list = num_slices*[None]

  num_ues = len(scen.getUEsList())

  num_enbs_list = num_slices*[None]
  connections_list = num_slices*[None]
  for slice in range(num_slices):
    enbs_coords_list[slice] = list_scen[slice].getAntennasPositionList()
    num_enbs_list[slice] = len(enbs_coords_list[slice])
    connections_list[slice] = get_ues_connections_per_slice(optimized_byslice[slice], ues_coords, antennas_regions_byslice[slice], size_sector, size_x, size_y, slice)
  
  '''print("Analisando o resultado...")
  ue_test = 3
  slice_test = 9
  y = ues_coords[ue_test][slice_test]
  print(type(y), y.x, y.y)    # UE 59 no slice 9
  print("UE[{}], no slice {},  esta na regiao {}".format(ue_test, 9, geo.coord2Region(y, size_sector, size_x, size_y)))
  print(optimized_byslice[slice_test])
  print(antennas_regions_byslice[slice_test])
  print("Ue deve ser conectado ao ENB de indice ", connections_list[slice_test][ue_test])'''

  config_pattern = genf.gen_sliced_config_pattern(min_sinr, mode, multi_carriers, extra_config_name)
  config_name_list = []
  s_interval= 1000/((target_f*10**6)/(8*p_size)) # ms

  network_full_name = hned.dir_to_package(net_dir) + (f'ILP{mode.capitalize()}Net' if network_name == '' else network_name)

  with open(filename, 'wt') as f:
    hp.writeCommentConfigILP(f, 'ilp_sliced_ini2', dict_args= dict_args, extra = 'Using {} macros with {} ues each. Slicing 10s in 10 different simulations. Using microcells.'.format(n_macros, 60))
    hp.generalConfig(f)
    hp.writeSeeds(f, num_rngs= 2, seeds= [seed])
    hp.writeSeparation(f, "Transmission Power")
    hp.writeTransmissionPower(f, micro_power= micro_power, is5G= True)
    hp.writeSeparation(f, "Channel Control")
    if multi_carriers:
      hp.writeCarrierAggregation5G(f, num_carriers= len(antennas_regions_byslice), carriers_frequencies= [scen.carrier_frequency - 0.02*np.max(num_bands)*i/100 for i in range(len(antennas_regions_byslice))], eNBs_carriers= True)
    else:
      hp.writeCarrierAggregation5G(f, carriers_frequencies= [scen.carrier_frequency])
    hp.writeSeparation(f, "Channel Model")
    hp.writeChannelModel5G(f, model_name= "MoreInfoChannelModel", tolerateMaxDistViolation= True, extCell_interference= False, building_height= scen.h_building, nodeb_height= scen.h_enbs,
                           ue_height= scen.h_ues, street_wide= scen.w_street, antennGainEnB= scen.gain_enb, antennaGainUe= scen.gain_ue, bs_noise_figure= scen.enb_noise_figure, ue_noise_figure= scen.ue_noise_figure,
                           cable_loss= scen.cable_loss, thermalNoise= scen.thermal_noise, fixed_los= scen.los)
    hp.writeSeparation(f, "Resource Blocks")
    hp.writeResourceBlocksOptions(f, "RBs", num_bands, is5G= True)
    hp.writeSeparation(f, "UEs")
    hp.writeNumUEs(f, num_ues)
    #hp.writeConnectOptions(f, list_connections= connections, parallel_var= iter_slice_name)
    hp.writeComment(f, text= "Scheduler")
    hp.writeSchedulingOptions(f, sched= ['MAXCI'])
    hp.writeSeparation(f, "Scenario")
    hp.writeComment(f, text= "UEs")
    hp.writeScenarioPerso(f, num_and_scen=[(num_ues, scen.scenario)], for5g= True)
    hp.writeComment(f, text= "UEs")
    hp.nl(f)
    hp.writeMobilityType(f, type= "LinearMobility", object_name= "ue[*]")
    #hp.writeVarSpeedMobDefault(f, speed_mean= 3000, std_dev= 1000, object_name= "ue[*]", update_interval= 1)
    
    hp.writeConstraint(f, object_name= 'ue[*]', maxX=size_x, minX=0, maxY=size_y, minY= 0)
    hp.writeSeparation(f, "Apps")
    if app.upper() == "VOIP":
      hp.writeNumApps(f, numUEs= num_ues, directions= 2, multi= False)
      hp.writeComment(f, text= "VoIP UL")
      hp.writeAppVoipUL(f, num_ues, n_app= 0, p_size= p_size)
      hp.writeComment(f, text= "VoIP DL")
      hp.writeAppVoipDL(f, num_ues, n_app= 1, p_size= p_size)
    elif app.upper() == "VIDEO":
      hp.writeNumApps(f, numUEs= num_ues, directions= 2, multi= False)
      hp.writeComment(f, text= "Video Streaming UL")
      hp.writeAppVideoUL(f, numUEs= num_ues, p_size= p_size, n_app= 0, mtu= False, s_interval= s_interval)
      hp.writeComment(f, text= "Video Streaming DL")
      hp.writeAppVideoDL(f, numUEs= num_ues, p_size= p_size, n_app= 1, mtu= True, s_interval= s_interval)
    
    for slice in range(num_slices):
      config_name = config_pattern  + '_slice{}'.format(slice)
      config_name_list.append(config_name)
      hp.makeNewConfig(f, config_name)
      hp.writeTime(f, time= slice_time, repeat= repetitions)
      hp.writeSeparation(f, "Outputs")
      hp.writeVectorExtra(f, module= "**.eNB*.cellularNic.channelModel[*]", statistic= "idRcvdSinr:vector", value= True)
      hp.writeVectorExtra(f, module= "**.eNB*.cellularNic.channelModel[*]", statistic= "rcvdSinr:vector", value= True)
      hp.writeVectorExtra(f, module= "**.app[*]", statistic= "throughput:vector", value= True)
      hp.writeVectorExtra(f, module= "**.app[*]", statistic= "endToEndDelay:vector", value= True)
      hp.writeOutput(f, "${resultdir}/" + config_pattern + "/"+str(min_sinr)+"-${RBs}-${repetition}-${Slice}")
      if cmdenv_config:
        hp.writeSeparation(f, "Cmdenv")
        hp.writeCmdenvConfig(f, config_name= config_pattern, min_sinr= min_sinr, performance_display = False, redirect_output= True)
      hp.writeSeparation(f, "Snapshots")
      hp.writeSnapshotsConfig(f, filename= "../../../Functions/" + config_pattern + "-RBs_${RBs}-Slice_${Slice}-"+str(min_sinr)+"-${repetition}.sna", snapshot= False)
      hp.writeSlice(f, slice= slice, iter_name= iter_slice_name)
      hp.writeNumEnbs(f, options= [num_enbs_time[slice]], iter_name= 'NumEnbs', parallel_name= iter_slice_name)
      network_full_name = hned.dir_to_package(net_dir) + (f'ILP{mode.capitalize()}Net' if network_name == '' else network_name) + f'Slice{slice}'
      hp.writeNetwork(f, network= network_full_name)
      hp.writeComment(f, text= "Conecting UEs to eNodeB")
      hp.writeConnectOptions(f, list_connections= connections_list[slice], parallel_var= iter_slice_name)
      if is_micro:
        hp.writeSeparation(f, "eNBs")
        hp.writeMultiMicro(f, num_enbs_list[slice], node_name = "eNB")

      hp.writeComment(f, text= "eNodeBs")
      hp.writeMultiScenarios(f, object_name= 'eNB', num= num_enbs_list[slice], scenario= scen.scenario, for5g= True)

      hp.writeSeparation(f, "Mobility")
      hp.writeComment(f, text= "eNodeB")
      hp.writeMultiIniMobility(f,object_name= 'eNB', coordinates= enbs_coords_list[slice])
      hp.writeConstraint(f, object_name= 'eNB*', maxX=size_x, minX=0, maxY=size_y, minY= 0)

      hp.writeSeparation(f,'Mobility each slice')
      list_coord_ue = []
      list_mov_ue = []
      for ue in range(len(ues_coords)):
        list_coord_ue.append(ues_coords[ue][slice])
        list_mov_ue.append(ues_mov[ue][slice])
      
      hp.writeArrayIniMobility(f, object_array_name= 'ue', coordinates = list_coord_ue, paral_name= '')
      hp.writeArrayMovMobility(f, object_array_name= 'ue', movements= list_mov_ue, fixed_speed= True, paral_name= '')   
   

  return config_name_list, num_enbs_time


def ilp_ned(network:str = "ILPFixedNet", size_y:int =8000, size_x:int =8000, image:str =None, n_enbs: int = 2, net_dir: str= '_5G/networks', project_dir: str= '../Network_CCOpMv'):
  """This function generates a .ned file to create a network with multiple UEs and eNBs.
  
  The network created include the default and necessary submodules to ensure a correct Simu5G simulation.

  Args:
    network: string representing the new network name
	  size_y: y dimension size of considered region in meters
    size_x: x dimension size of considered region in meters
    size_sector: sides size of square sectors in meters
    image: string representing the image path to be used as a background
    n_enbs: the number of eNBs composing the network
    net_dir: directory containing the network
    project_dir: directory of the omnet++ project
  """

  filename = f"{project_dir}/{net_dir}/{network}.ned"

  with open(filename, 'wt') as f:
    hned.writeBaseImports(f, is5g= True, snapshot= True, net_dir= net_dir)
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

def parse_results(filename: str, max_time: int):
  """This function parses the UEs and eNBs necessary information from the solver (ccop_mv_MILP) resulted solution.

  Args:
    filename: string representing the name of the txt file with the solution
    max_time: Max_Time parameter used in the solver

  Return:
    Three structures. The first one is a list of dict (results[t]{n: m}) where t is the simulation time, n is the sector of a UE at that time and m is the sector of its serving cell.
    The second one is a list with the sectors where the eNBs were located (List[int]).
    The third is a list with the number of eNBs deployed in each slice
  """

  results = []
  enbs = []
  enbs_time = []
  for i in range(max_time):
    results.append({})
    enbs_time.append([])

  with open(filename, "r") as f:
    for line in f:
      if not line.startswith('---'): 
        data = [int(x) for x in line.split()]   # data: [t, m, n]
        results[data[0]][data[2]] = data[1]
        enbs_time[data[0]].append(data[1])
        enbs.append(data[1])
        enbs = np.unique(enbs).tolist()

  #Get the number of eNBs at each slice
  for t in range(max_time):
    enbs_time[t] = np.unique(enbs_time[t]).size

  return results, enbs, enbs_time

def parse_results_per_slice(filename: str, max_time: int):
  """This function parses the UEs and eNBs necessary information from the solver (ccop_mv_MILP) resulted solution.

  Args:
    filename: string representing the name of the txt file with the solution
    max_time: Max_Time parameter used in the solver

  Return:
    Three structures. The first one is a list of dict (results[t]{n: m}) where t is the simulation time, n is the sector of a UE at that time and m is the sector of its serving cell.
    The second one is a list of lists (list[t][n]) where t is the time of the simulation and n is the number of the eNB with the sector where each eNB is located at that time (List[List[int]]).
    The third is a list with the number of eNBs deployed in each slice
  """

  results = []
  enbs = []
  enbs_time = []
  enbs_byslice = []
  for i in range(max_time):
    results.append({})
    enbs_time.append([])
    enbs_byslice.append([])
  try:
    with open(filename, "r") as f:
      for line in f:
        if not line.startswith('---'): 
          data = [int(x) for x in line.split()]   # data: [t, m, n]
          results[data[0]][data[2]] = data[1]
          enbs_time[data[0]].append(data[1])
          enbs.append(data[1])
          enbs = np.unique(enbs).tolist()
  except FileNotFoundError:
    print("File {} not found.".format(filename))
    return None, None, None

  #Get the number of eNBs at each slice
  
  for t in range(max_time):
    enbs_byslice[t] = np.unique(enbs_time[t]).tolist()
    enbs_time[t] = np.unique(enbs_time[t]).size
  
  results_list = 10*[None]
  for i in range(len(results)):
    results_list[i] = results[i]

  return results_list, enbs_byslice, enbs_time

def get_ues_connections(result, ues_coords, antennas_regions: List[int], size_sector, size_x, size_y):
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

def get_ues_connections_per_slice(result, ues_coords, antennas_regions: List[int], size_sector, size_x, size_y, slice_):
  """This function interpretates the result parsed from the solver in to the elements connections.

  Args:
    result: Dict containing the parsed solution from the solver for a specific time (slice_)
    ues_coords: 2D Matrix (n X t) with the coordinates of each UE (n) at each time of simulation (t).
    antennas_regions: List[int] containing the sectors where eNBs are located
    size_sector: sides size of square sectors in meters
    size_x: x dimension size of considered region in meters
    size_y: y dimension size of considered region in meters
    slice_: specific time considered

  Return:
    A Array of size n with the serving cell number for each UE (n).
  """
  connections = []
  
  for ue in ues_coords:
    region = geo.coord2Region(ue[slice_], size_sector, size_x, size_y)
    #Assume-se que a regiao do UE é servida por alguma das antenas
    connections.append(antennas_regions.index(result[region])+1)

  return connections