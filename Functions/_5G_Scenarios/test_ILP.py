import numpy
from Functions.coordinates import Coordinate
from Functions.geometry import Centroid
import helper as hp
import random
import geometry as geo

def test_ILP(filename, seed, d_height:int =1000, d_width:int =1000, d_region:int =100):
  random.seed(seed)
  scen = start_scenario_chess(d_height, d_width, d_region)

  user_map = [25,13,2,19]
  regions_x_y = scen.getRegionsCentersList()
  num_ues = 25+13+2+19 #scen.n_regions

  with open(filename, 'wt') as f:
    hp.writeCommentConfigILP(f, "ilp_fixed_info", filename, seed, d_height, d_width, d_region)

    hp.defaultGeneral(f, is5g= True)
    hp.makeNewConfig(f, name= 'Config ilp_fixed_info')
    hp.writeNetwork(f, network= '_5G.networks.SimpleNet')
    hp.writeTime(f, time= 10, repeat= 1)
    hp.writeSeeds(f, num_rngs= 2, seeds= [seed])
    hp.nl(f)
    hp.writeOutput(f, "${resultdir}/${configname}/${iniX}-${iniY}-${repetition}")
    hp.writeSeparation(f, "Transmission Power")
    hp.writeTransmissionPower(f)
    hp.writeSeparation(f, "Resource Blocks")
    hp.writeResourceBlocks(f, 6, is5G= True)
    hp.writeSeparation(f, "Carrier Aggregation")
    hp.writeCarrierAggregation(f, "0.7GHz")    
    hp.writeSeparation(f, "Channel Model")
    hp.writeChannelModel(f)
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
    #hp.writeOptionsIniMobility(f, 'eNB', [coord.x for coord in regions_x_y], [coord.y for coord in regions_x_y], [scen.h_enbs])
    hp.writeOptionsIniMobility(f, 'eNB', [750], [250])
    hp.writeConstraint(f, object_name= 'eNB*', maxX=d_width, minX=0, maxY=d_height, minY= 0)
    hp.writeComment(f, text= "UEs")
    hp.nl(f)
    hp.writeMobilityType(f, type= "StationaryMobility", object_name= "ue[*]")
    
    count_users = 1
    for n in range(len(user_map)):
        if n == 0:
            centroid = Centroid(Coordinate(250,250))
        elif n == 1:
            centroid = Centroid(Coordinate(750,250))
        elif n == 2:
            centroid = Centroid(Coordinate(250,750))
        else:
            centroid = Centroid(Coordinate(750,750))

        centroid.placeUEs(user_map[n],50,1)
        ues_x_y = centroid.getUEsPositionList()
        print(count_users)
        hp.writeArrayIniMobility(f, object_array_name= 'ue', coordinates= ues_x_y,count_init = count_users - 1)
        count_users = count_users + user_map[n]

    hp.writeConstraint(f, object_name= 'ue[*]', maxX=d_width, minX=0, maxY=d_height, minY= 0)
    hp.writeSeparation(f, "Apps")
    hp.writeNumApps(f, numUEs= num_ues, directions= 2)
    #TODo: Change app?
    hp.writeComment(f, text= "VoIP UL")
    hp.writeAppVoipUL(f, num_ues, n_app= 0)
    hp.writeComment(f, text= "VoIP DL")
    hp.writeAppVoipDL(f, num_ues, n_app= 1)


def start_scenario_chess(d_height:int =1000, d_width:int =1000, d_region:int =100):

  scen = geo.MapChess(d_width, d_height, d_region)
  scen.placeTestUEs()
  scen.placeAntennas([0,1])

  return scen