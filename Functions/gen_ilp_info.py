import geometry as geo
from sinr_comput import db_to_linear
from helper_xml import get_map_ues_time, get_ues_time
from Solutions.ILP_fixed_in_time import ccop_mv_MILP as solver_fixed
from Solutions.ILP_varying_in_time import ccop_mv_MILP as solver_varying
import _5G_Scenarios.ILP_configs as ilpc
import subprocess
from time import time, localtime, mktime
from datetime import datetime

def main():
  start_time = time()
  #Main parameters
  chosen_seed = 123
  size_y = 4000
  size_x = 4000
  size_sector = 400
  n_macros = 1
  ini_path = r"../Network_CCOpMv/_5G/simulations/ilp_fixed_users.ini"
  xml_filename= 'ilp_fixed_users-sched=MAXCI--0.sna'
  min_sinr = 15 #5, 10, 15
  result_dir = "Solutions"
  varying = True
  min_dis = 2000 #Enlace de rádio na prática
  first_antenna_region = 1

  run_all = False

  if run_all:
    #Genereting .ini file
    ilpc.ilp_fixed_users(ini_path, chosen_seed, size_y= size_y, size_x= size_x, size_sector= size_sector, n_macros= n_macros)

    open(xml_filename, 'w').close()

    #oppmake = r"opp_makemake -f --deep -O out -KINET4_PROJ=../../inet4 -KSIMU5G_1_1_0_PROJ=../../Simu5G-1.1.0 -DINET_IMPORT -I. -I$\(INET4_PROJ\)/src -I$\(SIMU5G_1_1_0_PROJ\)/src -L$\(INET4_PROJ\)/src -L$\(SIMU5G_1_1_0_PROJ\)/src -lINET$\(D\) -lsimu5g$\(D\)"
    #Running Omnet++
    subprocess.call(r'''cd ../Network_CCOpMv
opp_makemake -f --deep -O out -KINET4_PROJ=../../inet4 -KSIMU5G_1_1_0_PROJ=../../Simu5G-1.1.0 -DINET_IMPORT -I. -I$\(INET4_PROJ\)/src -I$\(SIMU5G_1_1_0_PROJ\)/src -L$\(INET4_PROJ\)/src -L$\(SIMU5G_1_1_0_PROJ\)/src -lINET$\(D\) -lsimu5g$\(D\)
make
./Network_CCOpMv ''' + ini_path + r' -u Cmdenv -c ilp_fixed_users -n .:../../inet4/src:../../inet4/examples:../../inet4/tutorials:../../inet4/showcases:../../Simu5G-1.1.0/simulations:../../Simu5G-1.1.0/src', shell= True)


  #Determines what the program will show to the user
  get_solution = True
  show_sinr = False
  show_full = False
  show_ues = False
  is_micro = True

  #Initiating scenario
  scen = geo.MapChess(size_y, size_x, size_sector, carrier_frequency= 0.7, chosen_seed= chosen_seed, scenario= "URBAN_MICROCELL" if is_micro else "URBAN_MACROCELL",
                      enb_tx_power= 30 if is_micro else 46, h_enbs= 18, gain_ue= -1, enb_noise_figure= 9)

  if show_full:
    #Placing UEs: Full
    scen.placeUEs(types= "Full", n_ues_macro= 60) #72 macros? -> 4320 ues
    scen.plotUes()

  #Placing UEs
  scen.placeUEs(type= "Random", n_macros= n_macros, n_ues_macro= 60)
  #scen.plotUes()

  #Generating sinr map
  print("-------------Generating sinr map")
  sinr_map = scen.getSinrMap()

  if show_sinr:
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

  if get_solution:

    #Generating default parameters
    max_user_antenna_m = [60 for i in range(scen.n_sectors)]
    antennas_map_m = [1 for i in range(scen.n_sectors)]
    min_snr_m = [db_to_linear(min_sinr) for i in range(scen.n_sectors)]
    distance_mn = scen.getRegionsDistanceMatrix()

    #Generating ues time map
    print("-------------Generating ues map")
    users_t_m = get_map_ues_time(scen= scen, xml_filename= xml_filename)

    #Calculating Solution
    print("-------------Calculating Solution (this may take a while)")
    print(f"+++++++++++++++++++Min Sinr: {min_sinr} dB ({'varying' if varying else 'fixed'})")
    print(f"+++++++++++++++++++With backhaul constraint. Start: {datetime.fromtimestamp(mktime(localtime(start_time)))}")
    
    if varying:
      min_time= 2
      solver_varying(Max_Space= scen.n_sectors, Max_Time= 10, users_t_m= users_t_m, MAX_USER_PER_ANTENNA_m= max_user_antenna_m, antenasmap_m= antennas_map_m,
                  snr_map_mn= sinr_map, MIN_SNR_m= min_snr_m, distance_mn= distance_mn, MIN_DIS= min_dis, result_dir = result_dir, MIN_TIME= min_time, FIRST_ANTENNA= first_antenna_region)
    else:
      solver_fixed(Max_Space= scen.n_sectors, Max_Time= 10, users_t_m= users_t_m, MAX_USER_PER_ANTENNA_m= max_user_antenna_m, antenasmap_m= antennas_map_m,
                  snr_map_mn= sinr_map, MIN_SNR_m= min_snr_m, distance_mn= distance_mn, MIN_DIS= min_dis, result_dir = result_dir, FIRST_ANTENNA= first_antenna_region)

  elif show_ues:
    #Plotting ues configuration over time
    ues_coords = get_ues_time(ues_list= scen.getUEsList(), xml_filename= xml_filename)
    for t_ues in ues_coords:
      scen.plotUes(external= True, ues_positions= [u.position for u in t_ues])
  #print(map_ues_time)

  print(f"--- Done after {(time() - start_time)/(60*60)} hours. ---")

if __name__ == "__main__":
  main()
  print("Done")