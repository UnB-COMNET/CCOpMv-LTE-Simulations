import helper as hp
import random
import geometry as geo

def ilp_fixed_info(filename, seed, d_height:int =8000, d_width:int =8000, d_region:int =800):
  random.seed(seed)
  scen = start_scenario_chess(d_height, d_width, d_region)

  ues_x_y = scen.getUEsPositionList()
  regions_x_y = scen.getRegionsCentersList()
  num_ues = scen.n_regions

  with open(filename, 'wt') as f:
    hp.writeCommentConfigILP(f, "ilp_fixed_info", filename, seed, d_height, d_width, d_region)

    hp.defaultGeneral(f, is5g= True)
    hp.makeNewConfig(f, name= 'Config ilp_fixed_info')
    hp.writeNetwork(f, network= '_5G.networks.SimpleNet')
    hp.writeTime(f, time= 10, repeat= 1)
    hp.writeSeeds(f, num_rngs= 2, seeds= [seed])
    hp.nl(f)
    hp.writeOutput(f, "${resultdir}/${configname}/${iniX}-${iniY}")
    hp.writeSeparation(f, "Transmission Power")
    hp.writeTransmissionPower(f)
    hp.writeSeparation(f, "Channel Control")
    hp.writeCarrierAggregation(f,carrierFrequency = "0.7GHz")
    hp.writeSeparation(f, "Channel Model")
    hp.writeChannelModel(f)
    hp.writeSeparation(f, "Resource Blocks")
    hp.writeResourceBlocks(f, 6, is5G= True)
    hp.writeSeparation(f, "UEs")
    hp.writeNumUEs(f, num_ues)
    hp.writeComment(f, text= "Conecting UEs to eNodeB")
    hp.writeConnectUE(f, UEs= [num_ues], ENBs= [1])
    hp.writeComment(f, text= "Scheduler")
    hp.writeSchedulingOptions(f, sched= ['MAXCI'])
    hp.writeSeparation(f, "Scenario")
    hp.writeComment(f, text= "eNodeB")
    hp.writeScenario(f, "eNB", for5g= True)
    hp.writeComment(f, text= "UEs")
    hp.writeScenarioPerso(f, num_and_scen=[(num_ues, 'URBAN_MACROCELL')], for5g= True)
    hp.writeSeparation(f, "Mobility")
    hp.writeComment(f, text= "eNodeB")
    hp.writeOptionsIniMobility(f, 'eNB', regions_x_y[0], regions_x_y[1])
    hp.writeConstraint(f, object_name= 'eNB*', maxX=d_width, minX=0, maxY=d_height, minY= 0)
    hp.writeComment(f, text= "UEs")
    hp.nl(f)
    hp.writeMobilityType(f, type= "StationaryMobility", object_name= "ue[*]")
    hp.writeArrayIniMobility(f, object_array_name= 'ue', coordenates= ues_x_y)
    hp.writeConstraint(f, object_name= 'ue[*]', maxX=d_width, minX=0, maxY=d_height, minY= 0)
    hp.writeSeparation(f, "Apps")
    hp.writeNumApps(f, numUEs= num_ues, directions= 2)
    #TODo: Change app?
    hp.writeComment(f, text= "VoIP UL")
    hp.writeAppVoipUL(f, num_ues, n_app= 0)
    hp.writeComment(f, text= "VoIP DL")
    hp.writeAppVoipDL(f, num_ues, n_app= 1)


def start_scenario_chess(d_height:int =1000, d_width:int =1000, d_region:int =100):

  scen = geo.MapChess(d_height, d_width, d_region)
  scen.placeTestUEs()

  return scen