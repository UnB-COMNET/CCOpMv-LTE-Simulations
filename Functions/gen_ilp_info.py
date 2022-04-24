from typing import List
import geometry as geo
from sinr_comput import db_to_linear
from helper_xml import get_map_ues_time, get_ues_time
from Solutions.ILP_fixed_in_time import ccop_mv_MILP as solver_fixed
from Solutions.ILP_varying_in_time import ccop_mv_MILP as solver_varying
from Solutions.ILP_single import ccop_mv_MILP as solver_single
import _5G_Scenarios.ILP_configs as ilpc
import subprocess
from time import time, localtime, mktime
from datetime import datetime
from multiprocessing import Process, cpu_count
from pathlib import Path
import sys
import io
from errors import check_mode

def main():
    ini_path = r"../Network_CCOpMv/_5G/simulations/ilp_move_users.ini"
    chosen_seed = 123
    size_y = 4000
    size_x = 4000
    size_sector = 400
    n_macros = 1
    xml_filename = ilpc.gen_movement_filename("ilp_move_users", chosen_seed, snapshot= True)
    min_sinr = 5 #5, 10, 15s
    min_sinrs = [5, 10, 15]
    varying = True
    mode = "single"
    min_dis = 2000 #Enlace de rádio na prática
    first_antenna_region = 1
    min_time = 2
    num_slices = 10
    micro_power = 40#dBm
    result_dir = f"Solutions/chosen_seed_{chosen_seed}/micro_power_{micro_power}"

    gen_ilp_info(chosen_seed= chosen_seed, size_x= size_x, size_y= size_y, size_sector= size_sector, n_macros= n_macros, mode= mode, 
                 xml_filename = xml_filename, min_sinr= min_sinr, result_dir= result_dir, min_dis= min_dis, first_antenna_region= first_antenna_region,
                 min_time= min_time, micro_power= micro_power, num_slices= num_slices)
    #run_all_solvers(ini_path= ini_path, chosen_seed= chosen_seed, size_x= size_x, size_y= size_y, size_sector= size_sector, n_macros= n_macros,
    #                xml_filename= xml_filename, min_sinrs= min_sinrs, result_dir= result_dir, min_dis= min_dis, first_antenna_region= first_antenna_region)

def gen_ilp_info(chosen_seed: int, size_x: int, size_y: int, size_sector: int, n_macros: int, xml_filename: str,
                 min_sinr: int, result_dir: str, mode: str, min_dis: int, first_antenna_region: int, min_time: int,
                 micro_power: int = 30, num_slices: int= 10):
  
    #mode = "varying" if varying else "fixed"

    file_name = gen_file_name(mode= mode, min_sinr= min_sinr)
    print("Running Solver - Min Snr: {} - {} (Seed: {})".format(min_sinr, mode.capitalize(), chosen_seed))

    #Output config
    out_file = open(gen_log_file_name(result_dir, file_name), 'wb', 0)
    sys.stdout = io.TextIOWrapper(out_file, write_through=True)

    start_time = time()

    #Determines what the program will show to the user
    get_solution = True
    show_sinr = False
    show_ues = False
    is_micro = True

    #Initiating scenario
    scen = geo.MapChess(size_y, size_x, size_sector, carrier_frequency= 0.7, chosen_seed= chosen_seed, scenario= "URBAN_MICROCELL" if is_micro else "URBAN_MACROCELL",
                        enb_tx_power= micro_power if is_micro else 46, h_enbs= 18, gain_ue= -1, enb_noise_figure= 9)

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
        print(("-------------Calculating Solution (this may take a while)\n"
              f"+++++++++++++++++++Min Sinr: {min_sinr} dB ({mode})\n"
              f"+++++++++++++++++++With backhaul constraint. Start: {datetime.fromtimestamp(mktime(localtime(start_time)))}\n"))
        
        check_mode(mode= mode)

        if mode == "varying":
            solver_varying(Max_Space= scen.n_sectors, Max_Time= num_slices, users_t_m= users_t_m, MAX_USER_PER_ANTENNA_m= max_user_antenna_m, antenasmap_m= antennas_map_m,
                           snr_map_mn= sinr_map, MIN_SNR_m= min_snr_m, distance_mn= distance_mn, MIN_DIS= min_dis, result_dir = result_dir, MIN_TIME= min_time, FIRST_ANTENNA= first_antenna_region)
        elif mode == "fixed":
            solver_fixed(Max_Space= scen.n_sectors, Max_Time= num_slices, users_t_m= users_t_m, MAX_USER_PER_ANTENNA_m= max_user_antenna_m, antenasmap_m= antennas_map_m,
                         snr_map_mn= sinr_map, MIN_SNR_m= min_snr_m, distance_mn= distance_mn, MIN_DIS= min_dis, result_dir = result_dir, FIRST_ANTENNA= first_antenna_region)
        elif mode == "single":
            solver_single(Max_Space= scen.n_sectors, Max_Time= num_slices, users_t_m= users_t_m, MAX_USER_PER_ANTENNA_m= max_user_antenna_m, antenasmap_m= antennas_map_m, valid_time= num_slices,
                          snr_map_mn= sinr_map, MIN_SNR_m= min_snr_m, distance_mn= distance_mn, MIN_DIS= min_dis, result_dir= result_dir, FIRST_ANTENNA= first_antenna_region)

    elif show_ues:
        #Plotting ues configuration over time
        ues_coords = get_ues_time(ues_list= scen.getUEsList(), xml_filename= xml_filename)
        for t_ues in ues_coords:
            scen.plotUes(external= True, ues_positions= [u.position for u in t_ues])

    print(f"--- Done after {(time() - start_time)/(60*60)} hours. ---")
    sys.stdout = sys.__stdout__

def run_movement_simulation(ini_path: str, chosen_seed: int, size_x: int, size_y: int, size_sector: int, n_macros: int, config_name: str= 'ilp_move_users',
                            num_slices: int= 10, cpu_num: int= 1):
    #Genereting .ini file
    ilpc.ilp_move_users(ini_path, chosen_seed, size_y= size_y, size_x= size_x, size_sector= size_sector, n_macros= n_macros,
                        config_name= config_name, num_slices= num_slices)

    snapshot_filename = ilpc.gen_movement_filename(config_name= config_name, seed= chosen_seed, snapshot= True)

    open(snapshot_filename, 'w').close()
    print('\nmovimento para seed\n', chosen_seed)
    #Running Omnet++
    arg = ('cd ../Network_CCOpMv\n'
                          f'opp_runall -j{cpu_num} ./Network_CCOpMv -f ' + ini_path + r' -u Cmdenv -c ' + config_name + r' -n .:../../../OmNET2/inet4/src:../../../OmNET2/inet4/examples:../../../OmNET2/inet4/tutorials:../../../OmNET2/inet4/showcases:../../../OmNET2/Simu5G-1.1.0/simulations:../../../OmNET2/Simu5G-1.1.0/src')

    code = subprocess.check_output(arg, shell= True)
    #code.check_returncode()

    with open(snapshot_filename, 'a') as f:
        f.write('<!--Done-->\n')


def run_all_solvers(chosen_seed: int, xml_filename: str, size_x: int, size_y: int, size_sector: int, n_macros: int,
                    min_sinrs: List[int], result_dir: str, min_dis: int, first_antenna_region: int, mode: str = ''):

    var = []
    processes = []

    if mode.lower() == 'varying':
        var = [True]
    elif mode.lower() == 'fixed':
        var = [False]
    else:
        var = [True, False]

    #Varying, fixed or both
    kwargs = {'chosen_seed' : chosen_seed, 'size_x': size_x, 'size_y': size_y, 'size_sector': size_sector, 'n_macros': n_macros, 'min_sinr': None,
              'xml_filename': xml_filename, 'result_dir': result_dir, 'varying': None, 'min_dis': min_dis, 'first_antenna_region': first_antenna_region}


    print(f'Starting computations on {cpu_count()} cores.')
    for varying in var:
        kwargs['varying'] = varying

        for min_snr in min_sinrs:
    
            kwargs['min_sinr'] = min_snr

            processes.append(Process(target= gen_ilp_info, kwargs= kwargs))
            processes[-1].start()

        #gen_ilp_info(chosen_seed= chosen_seed, size_x= size_x, size_y= size_y, size_sector= size_sector, n_macros= n_macros, xml_filename= xml_filename,
        #                       min_sinr= min_sinr, result_dir= result_dir, varying= varying, min_dis= min_dis, first_antenna_region= first_antenna_region)
    
    for p in processes:
        p.join()

def gen_file_name(mode: str, min_sinr: int):
    return f'ilp_{mode}_sliced_{str(min_sinr)}'

#Result_dir must have a 'logs' subdir
def gen_log_file_name(result_dir: str, file_name: str):
    log_dir = f"{result_dir}/logs"
    Path(log_dir).mkdir(parents=False, exist_ok=True)
    return f"{log_dir}/{file_name}.log"

if __name__ == "__main__":
    main()
    print("Done")