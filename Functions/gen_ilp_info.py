import geometry as geo
import sinr_comput as sc
from random import random, seed
from helper_xml import get_map_ues_time, get_coord_ues_time
from Solutions.ILP_fixed_in_time import ccop_mv_MILP

def main():
  #Teste linear_to_db
  #print(sc.linear_to_db(1))
  #print(sc.linear_to_db(1/2))
  #print(sc.linear_to_db(20))
  #print(sc.linear_to_db(100))

  #Teste jakes fadding
  #fading1 = sc.jakes_fadding(6, 0, 363**-9, 0.7, 1)
  #print(fading1)
  #fading2 = sc.jakes_fadding(6, 0, 363**-9, 2, 1)
  #print(fading2)
  #fading3 = sc.jakes_fadding(6, 0, 363**-9, 0.1, 1)
  #print(fading3)

  #Teste urban_macro pathloss
  #urban1 = sc.compute_urban_macro(distance = 1000, los = False, carrier_frequency= 0.7)
  #print(urban1)
  #urban2 = sc.compute_urban_macro(distance = 5000, los = False, carrier_frequency= 0.7)
  #print(urban2)
  #urban3 = sc.compute_urban_macro(distance = 1000, los = True, carrier_frequency= 0.7)
  #print(urban3)
  #urban4 = sc.compute_urban_macro(distance = 4999, los = False, carrier_frequency= 0.7)
  #print(urban4)

  #Teste log shadowing urban_macro
  #shad1 = sc.compute_shadowing(distance= 1000, speed= 0, los= False, scenario= "URBAN_MACROCELL", seed= 1)
  #print(shad1)
  #shad2 = sc.compute_shadowing(distance= 1000, speed= 0, los= True, scenario= "URBAN_MACROCELL", seed= 2)
  #print(shad2)
  #shad3 = sc.compute_shadowing(distance= 1000, speed= 0, los= False, scenario= "URBAN_MACROCELL", seed= 3)
  #print(shad3)
  #shad4 = sc.compute_shadowing(distance= 1000, speed= 0, los= False, scenario= "URBAN_MACROCELL", seed= 4)
  #print(shad4)

  show = 2

  #Initiating scenario
  scen = geo.MapChess(8000, 8000, 800, chosen_seed= 123) #100 setores

  if(show == 0):
    #Placing UEs: Full
    scen.placeUEs(type= "Full", n_ues_macro= 60) #72 macros? -> 4320 ues
    scen.plotUes()

  #Placing UEs
  scen.placeUEs(type= "Random", n_macros= 5, n_ues_macro= 60)
  scen.plotUes()

  #Generating sinr map
  print("-------------Generating sinr map")
  sinr_map = scen.getSinrMap()

  #Showing sinr in file
  count = 0
  count2 = 0
  with open("sinr.txt", 'w') as f:
    for enb in sinr_map:
      count = 0
      f.write("{}:".format(count2))
      for snr in enb:
        f.write("\t{}- {}\n".format(count, snr))
        count += 1
      count2 += 1

  if (show == 2):

    #Generating default parameters
    max_user_antenna_m = [60 for i in range(scen.n_regions)]
    antennas_map_m = [1 for i in range(scen.n_regions)]
    min_snr_m = [10 for i in range(scen.n_regions)]

    #Generating ues time map
    print("-------------Generating ues map")
    users_t_m = get_map_ues_time(scen= scen, xml_filename= 'ilp_fixed_users-sched=MAXCI-#0.sna')

    #Calculating Solution
    print("-------------Calculating Solution (this may take a while)")
    ccop_mv_MILP(Max_Space= scen.n_regions, Max_Time= 10, users_t_m= users_t_m, MAX_USER_PER_ANTENNA_m= max_user_antenna_m, antenasmap_m= antennas_map_m, snr_map_mn= sinr_map, MIN_SNR_m= min_snr_m)

  elif (show == 1):
    #Plotting ues configuration over time
    ues_coords = get_coord_ues_time(scen= scen, xml_filename= 'ilp_fixed_users-sched=MAXCI-#0.sna')
    for t_ues in ues_coords:
      scen.plotUes(external= True, ues_positions= t_ues)
  #print(map_ues_time)


if __name__ == "__main__":
  main()
  print("Done")