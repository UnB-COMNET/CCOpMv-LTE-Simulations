from math import ceil
import geometry as geo
import sinr_comput as sc
from random import random, seed
from helper_xml import get_map_ues_time, get_coord_ues_time
from Solutions.ILP_fixed_in_time import ccop_mv_MILP
import _5G_Scenarios.ILP_fixed as ilpf
import subprocess
import os

def main():
  #Main parameters
  chosen_seed = 123
  d_height = 8000
  d_width = 8000
  d_region = 800
  n_macros = 2
  ini_path = r"../Network_CCOpMv/_5G/simulations/ilp_fixed_users.ini"
  xml_filename= 'ilp_fixed_users-sched=MAXCI--0.sna'

  run_all = False

  if run_all:
    #Genereting .ini file
    ilpf.ilp_fixed_users(ini_path, chosen_seed, d_height= d_height, d_width= d_width, d_region= d_region, n_macros= n_macros)

    open(xml_filename, 'w').close()

    input("Waiting.")

    oppmake = r"opp_makemake -f --deep -O out -KINET4_PROJ=../../inet4 -KSIMU5G_1_1_0_PROJ=../../Simu5G-1.1.0 -DINET_IMPORT -I. -I$\(INET4_PROJ\)/src -I$\(SIMU5G_1_1_0_PROJ\)/src -L$\(INET4_PROJ\)/src -L$\(SIMU5G_1_1_0_PROJ\)/src -lINET$\(D\) -lsimu5g$\(D\)"
    #Running Omnet++
    subprocess.call(r'''cd ../Network_CCOpMv
opp_makemake -f --deep -O out -KINET4_PROJ=../../inet4 -KSIMU5G_1_1_0_PROJ=../../Simu5G-1.1.0 -DINET_IMPORT -I. -I$\(INET4_PROJ\)/src -I$\(SIMU5G_1_1_0_PROJ\)/src -L$\(INET4_PROJ\)/src -L$\(SIMU5G_1_1_0_PROJ\)/src -lINET$\(D\) -lsimu5g$\(D\)
make
./Network_CCOpMv '''.format(oppmake) + ini_path + r' -u Cmdenv -c ilp_fixed_users -n .:../../inet4/src:../../inet4/examples:../../inet4/tutorials:../../inet4/showcases:../../Simu5G-1.1.0/simulations:../../Simu5G-1.1.0/src', shell= True)


  #Determines what the program will show to the user
  show = 2

  #Initiating scenario
  scen = geo.MapChess(d_height, d_width, d_region, chosen_seed= chosen_seed) #100 setores

  if(show == 0):
    #Placing UEs: Full
    scen.placeUEs(type= "Full", n_ues_macro= 60) #72 macros? -> 4320 ues
    scen.plotUes()

  #Placing UEs
  scen.placeUEs(type= "Random", n_macros= n_macros, n_ues_macro= 60)
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
    users_t_m = get_map_ues_time(scen= scen, xml_filename= xml_filename)

    #Calculating Solution
    print("-------------Calculating Solution (this may take a while)")
    #ccop_mv_MILP(Max_Space= scen.n_regions, Max_Time= 10, users_t_m= users_t_m, MAX_USER_PER_ANTENNA_m= max_user_antenna_m, antenasmap_m= antennas_map_m, snr_map_mn= sinr_map, MIN_SNR_m= min_snr_m)

  elif (show == 1):
    #Plotting ues configuration over time
    ues_coords = get_coord_ues_time(scen= scen, xml_filename= xml_filename)
    for t_ues in ues_coords:
      scen.plotUes(external= True, ues_positions= t_ues)
  #print(map_ues_time)

Max_Space=4
Max_Time=6
users_t_m = [[ceil(random()*20) for m in range(0,Max_Space)] for t in range(0,Max_Time)]
antenasmap_m = [1,1,1,1]
MAX_USER_PER_ANTENNA_m=[60,40,60,40]
snr_map_mn=[[50 if n == m else -0.1 for n in range(0,Max_Space)] for m in range(0,Max_Space)]
MIN_SNR_m=[20,30,10,25]


ccop_mv_MILP(Max_Space,
    Max_Time, 
    users_t_m, 
    MAX_USER_PER_ANTENNA_m, 
    antenasmap_m, 
    snr_map_mn, 
    MIN_SNR_m)
if __name__ == "__main__":
  main()
  print("Done")