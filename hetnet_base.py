import helper as hp
import random
import geometry as geo

def hetnet_base(filename, directions, center_x, center_y, num_ues, sites, micro_per_small, small_per_site, seed):

  center = geo.Coordinate(center_x,center_y)
  random.seed(seed)
  scen = startScenario(num_ues, center, micro_per_small)
  num_macros = len(scen.macrocells)
  antennasPositions = getMicroAntennasPositions(scen.macrocells)

  with open(filename, 'wt') as f:
    # General

    hp.writeCommentConfig(f, "hetnet_base", filename, directions, center_x, center_y,
                          num_ues, sites, micro_per_small, small_per_site, seed)

    hp.defaultGeneral(f)
    hp.makeNewConfig(f, name= 'Config eNB3_Base')
    hp.writeNetwork(f, network= 'networks.UrbanMacro7_4')
    hp.writeTime(f, time= 10, repeat= 10)
    hp.writeSeeds(f, num_rngs= 2, seeds= [123])
    hp.nl(f)
    hp.writeOutput(f, "${resultdir}/${configname}/${sched}-${repetition}")
    hp.writeSeparation(f, "Micro Cell")
    hp.writeMultiMicro(f, number= num_macros*micro_per_small*small_per_site)
    hp.writeSeparation(f, "Transmission Power")
    hp.writeTransmissionPower(f)
    hp.writeSeparation(f, "UEs")
    hp.writeNumUEs(f, scen.n_ues)
    hp.writeComment(f, text= "Conecting UEs to eNodeB")
    hp.writeConnectMultiUE(f, scen.macrocells)
    hp.writeComment(f, text= "Scheduler")
    hp.writeSchedulingOptions(f, sched= ['MAXCI', 'DRR', 'PF'])
    hp.writeSeparation(f, "Scenario")
    hp.writeComment(f, text= "eNodeB")
    hp.writeMultiScenarios(f, object_name= 'eNB', num= num_macros, scenario= 'URBAN_MACROCELL')
    hp.writeComment(f, text= "Microcell")
    hp.writeMultiScenarios(f, object_name= 'microCell', num = num_macros, scenario= 'URBAN_MICROCELL')
    hp.writeComment(f, text= "UEs")
    hp.writeMultiScenariosPerso(f, macrocells= scen.macrocells)
    hp.writeSeparation(f, "Mobility")
    hp.writeComment(f, text= "eNodeB")
    hp.writeMultiIniMobility(f,object_name= 'eNB', coordenates= scen.getMacrocellsPositionList())
    hp.writeConstraint(f, object_name= 'eNB*')
    hp.writeComment(f, text= "UEs")
    hp.nl(f)
    hp.writeMobilityType(f, type= "StationaryMobility", object_name= "ue*[*]")
    hp.writeUeMobilityPerso(f, scen= scen, multi= True)
    hp.writeConstraint(f, object_name= 'ue*[*]')
    hp.writeComment(f, text= "Microcell")
    hp.writeMultiIniMobility(f,object_name= 'microCell', coordenates= antennasPositions)
    hp.writeConstraint(f, object_name= 'microCell*')
    hp.writeSeparation(f, "Apps")
    hp.writeNumApps(f, numUEs= scen.n_ues, directions= directions, num_macros= num_macros, multi= True)
    hp.writeComment(f, text= "VoIP UL")
    hp.writeMultiAppVoipUL(f, numUEs= scen.n_ues, num_macros= num_macros, number_app= 0)
    hp.writeComment(f, text= "VoIP DL")
    hp.writeMultiAppVoipDL(f, numUEs= scen.n_ues, num_macros= num_macros, number_app= 1, num_apps = 2)
    hp.writeSeparation(f, "Channel Control")
    hp.writePropagation(f, model= "LogNormalShadow")
    hp.writeSeparation(f, "Handover")
    hp.writeComment(f, text= "Enable handover")
    hp.writeEnableHandover(f, object_name= "microCell*", enable= True)
    hp.writeEnableHandoverMultiUE(f, macrocells= scen.macrocells, only_micro= True)
    hp.writeComment(f, text= "X2 configuration")
    hp.writeX2Configuration(f, object_name= "microCell*", quantity= micro_per_small) #Connections in groups of 4
    #hp.writeX2Connections(f, object_names= ["eNB", "microCell"], quantities= [7, 28])
    for i in range(num_macros):
      hp.writeComment(f, text= "Hotspot{}".format(i))
      hp.writeX2Connections(f, object_names = ["microCell"], quantities= [micro_per_small], initial_values= [i*micro_per_small])


  #geo.plotMap(scen, False, 7)

def hetnet_mov(filename, directions, center_x, center_y, num_ues, sites, micro_per_small, small_per_site, seed):

  center = geo.Coordinate(center_x,center_y)
  random.seed(seed)
  scen = startScenario(num_ues, center, micro_per_small)
  num_macros = len(scen.macrocells)
  antennasPositions = getMicroAntennasPositions(scen.macrocells)

  with open(filename, 'wt') as f:
    # General

    hp.writeCommentConfig(f, "hetnet_mov", filename, directions, center_x, center_y,
                          num_ues, sites, micro_per_small, small_per_site, seed)

    hp.defaultGeneral(f)
    hp.makeNewConfig(f, name= 'Config HetNet_Mov')
    hp.writeNetwork(f, network= 'networks.Hetnet_mov')
    hp.writeTime(f, time= 10, repeat= 10)
    hp.writeSeeds(f, num_rngs= 2, seeds= [123])
    hp.nl(f)
    hp.writeOutput(f, "${resultdir}/${configname}/${sched}-${repetition}")
    hp.writeSeparation(f, "Micro Cell")
    hp.writeMultiMicro(f, number= num_macros*micro_per_small*small_per_site)
    hp.writeSeparation(f, "Transmission Power")
    hp.writeTransmissionPower(f)
    hp.writeSeparation(f, "UEs")
    hp.writeNumUEs(f, scen.n_ues)
    hp.writeComment(f, text= "Conecting UEs to eNodeB")
    hp.writeConnectMultiUE(f, scen.macrocells)
    hp.writeComment(f, text= "Scheduler")
    hp.writeSchedulingOptions(f, sched= ['MAXCI', 'DRR', 'PF'])
    hp.writeSeparation(f, "Scenario")
    hp.writeComment(f, text= "eNodeB")
    hp.writeMultiScenarios(f, object_name= 'eNB', num= num_macros, scenario= 'URBAN_MACROCELL')
    hp.writeComment(f, text= "Microcell")
    hp.writeMultiScenarios(f, object_name= 'microCell', num = num_macros, scenario= 'URBAN_MICROCELL')
    hp.writeComment(f, text= "UEs")
    hp.writeMultiScenariosPerso(f, macrocells= scen.macrocells)
    hp.writeSeparation(f, "Mobility")
    hp.writeComment(f, text= "eNodeB")
    hp.writeMultiIniMobility(f,object_name= 'eNB', coordenates= scen.getMacrocellsPositionList())
    hp.writeConstraint(f, object_name= 'eNB*')
    hp.writeComment(f, text= "UEs")
    hp.nl(f)
    hp.writeMovMobility(f, type= "LinearMobility", speed= 100, initial_heading= 0, object_name= "ue*[*]")
    hp.writeUeMobilityPerso(f, scen= scen, multi= True)
    hp.writeConstraint(f, object_name= 'ue*[*]')
    hp.writeComment(f, text= "Microcell")
    hp.writeMultiIniMobility(f,object_name= 'microCell', coordenates= antennasPositions)
    hp.writeConstraint(f, object_name= 'microCell*')
    hp.writeSeparation(f, "Apps")
    hp.writeNumApps(f, numUEs= scen.n_ues, directions= directions, num_macros= num_macros, multi= True)
    hp.writeComment(f, text= "VoIP UL")
    hp.writeMultiAppVoipUL(f, numUEs= scen.n_ues, num_macros= num_macros, number_app= 0)
    hp.writeComment(f, text= "VoIP DL")
    hp.writeMultiAppVoipDL(f, numUEs= scen.n_ues, num_macros= num_macros, number_app= 1, num_apps = 2)
    hp.writeSeparation(f, "Channel Control")
    hp.writePropagation(f, model= "LogNormalShadow")
    hp.writeSeparation(f, "Handover")
    hp.writeComment(f, text= "Enable handover")
    hp.writeEnableHandover(f, object_name= "microCell*", enable= True)
    hp.writeEnableHandoverMultiUE(f, macrocells= scen.macrocells, only_micro= True)
    hp.writeComment(f, text= "X2 configuration")
    hp.writeX2Configuration(f, object_name= "eNB*", quantity= micro_per_small*small_per_site+num_macros)
    hp.writeX2Configuration(f, object_name= "microCell*", quantity= micro_per_small+1) 
    #hp.writeX2Connections(f, object_names= ["eNB", "microCell"], quantities= [7, 28])
    for i in range(num_macros):
      hp.writeComment(f, text= "Hotspot{}".format(i))
      hp.writeX2Connections(f, object_names = ["microCell", "eNB"], quantities= [micro_per_small,1], initial_values= [i*micro_per_small,i])
    hp.writeComment(f, text= "Macros")
    hp.writeX2Connections(f, object_names = ["eNB"], quantities= [num_macros], initial_values= [0], initial_app= micro_per_small*small_per_site)

def startScenario(numUEs, center, micro_per_small):

  scen = geo.MapHexagonal(center)
  scen.n_ues = numUEs
  scen.n_antennas = micro_per_small

  for i in range(len(scen.macrocells)):
    # For each macrocell, it places the smallcells
    scen.placeSmallCell(scen.macrocells[i], scen.d_macromacro*0.425, scen.d_macrocluster)
    # For each smallcell in a given macrocell, it places the antennas
    for j in range(len(scen.macrocells[i].smallcells)):
            scen.placeAntennas(scen.macrocells[i].smallcells[j],scen.dropradius_sc_cluster,0,scen.n_antennas)           

  scen.placeUEs()

  return scen

def getMicroAntennasPositions(macrocells):
  positions = [[],[]]
  for m in macrocells:
    for s in m.smallcells:
      tmp = s.getAntennasPositionList()
      positions[0] += tmp[0]
      positions[1] += tmp[1]
  return positions