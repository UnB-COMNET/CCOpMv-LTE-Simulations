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
from random import randint, seed, random
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import general_functions as genf
import ga
import gwo

def main():
    ini_path = r"../Network_CCOpMv/_5G/simulations/ilp_move_users.ini"
    chosen_seed = 123
    size_y = 4000
    size_x = 4000
    size_sector = 400
    n_macros = 1
    xml_filename = genf.gen_movement_filename("ilp_move_users", chosen_seed, snapshot= True)
    min_sinr = 5 #5, 10, 15s
    min_sinrs = [5, 10, 15]
    varying = True
    mode = "single"
    min_dis = 2000 #Enlace de rádio na prática
    first_antenna_region = None
    min_time = 2
    num_slices = 10
    micro_power = 40#dBm
    result_dir = f"Solutions/chosen_seed_{chosen_seed}/micro_power_{micro_power}"
    disaster_percentage = 0

    gen_ilp_info(chosen_seed= chosen_seed, size_x= size_x, size_y= size_y, size_sector= size_sector, n_macros= n_macros, mode= mode, 
                 xml_filename = xml_filename, min_sinr= min_sinr, result_dir= result_dir, min_dis= min_dis, first_antenna_region= first_antenna_region,
                 min_time= min_time, micro_power= micro_power, disaster_percentage= disaster_percentage)
    #run_all_solvers(ini_path= ini_path, chosen_seed= chosen_seed, size_x= size_x, size_y= size_y, size_sector= size_sector, n_macros= n_macros,
    #                xml_filename= xml_filename, min_sinrs= min_sinrs, result_dir= result_dir, min_dis= min_dis, first_antenna_region= first_antenna_region)

def gen_ilp_info(scen: geo.MapChess, ues_per_slice: list, xml_filename: str,
                 min_sinr: int, result_dir: str, mode: str, min_dis: int, first_antenna_region: int, min_time: int,
                 disaster_percentage: int= 0):

    file_name = genf.gen_file_name(mode= mode, min_sinr= min_sinr)

    start_time = time()

    #Determines what the program will show to the user
    get_solution = True
    show_sinr = False
    show_ues = False
    show_antennas_map = False

    is_micro = True
    chosen_seed = scen.chosen_seed
    size_x = scen.size_x
    size_y = scen.size_y
    size_sector = scen.size_sector
    num_slices = scen.num_slices

    if show_sinr:

        # Generating sinr map
        print("-------------Generating sinr map")
        sinr_map = scen.getSinrMap()

        # Showing sinr in file
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

        # Generating sinr map
        print("-------------Generating sinr map")
        sinr_map = scen.getSinrMap()

        print("Running Solver - Min Snr: {} - {} (Seed: {})".format(min_sinr, mode.capitalize(), chosen_seed))

        # Generating default parameters
        seed(chosen_seed)
        max_user_antenna_m = [40 for i in range(scen.n_sectors)]
        antennas_map_m = [(0 if random() < disaster_percentage/100 else 1) for i in range(scen.n_sectors)]
        min_snr_m = [db_to_linear(min_sinr) for _ in range(scen.n_sectors)]
        distance_mn = scen.getRegionsDistanceMatrix()

        # Setting first antenna position
        done = False
        while not done:
            if first_antenna_region is not None and antennas_map_m[first_antenna_region] == 1:
                done = True
            else:
                first_antenna_region = genf.gen_first_antenna_region(chosen_seed=chosen_seed, n_sectors=scen.n_sectors)

        # Generating ues time map
        print("-------------Generating ues map")
        users_t_m = get_map_ues_time(scen= scen, xml_filename= xml_filename, ues_per_slice = ues_per_slice)
        
        # Output config
        out_file = open(genf.gen_log_file_name(result_dir, file_name), 'wb', 0)
        sys.stdout = io.TextIOWrapper(out_file, write_through=True)

        # Calculating Solution
        print(("-------------Calculating Solution (this may take a while)\n"
              f"+++++++++++++++++++Min Sinr: {min_sinr} dB ({mode})\n"
              f"+++++++++++++++++++With backhaul constraint. Start: {datetime.fromtimestamp(mktime(localtime(start_time)))}\n"))
        
        check_mode(mode= mode)

        # Printing parameters
        print('Parameters:')
        print('- chosen seed {}'.format(chosen_seed))
        print('- Map with {} sectors'.format(scen.n_sectors))
        print('- Map {} x {} m'.format(scen.size_x, scen.size_y))
        print('- Sector has a side of {} m'.format(scen.size_sector))
        print('- Max time: ', num_slices)
        print("- users_t_m: ", users_t_m)
        print('MAX_USER_PER_ANTENNAS_m: ', max_user_antenna_m)
        print("antennas_map_m: ", antennas_map_m)
        print("FIRST_ANTENNA: ", first_antenna_region)
        print("MIN_SNR_m: ", min_snr_m)
        print("-MIN_DIST: ", min_dis)
        print("- disaster percentage: ", disaster_percentage)

        if mode == "varying":
            solver_varying(Max_Space= scen.n_sectors, Max_Time= num_slices, users_t_m= users_t_m, MAX_USER_PER_ANTENNA_m= max_user_antenna_m, antenasmap_m= antennas_map_m,
                           snr_map_mn= sinr_map, MIN_SNR_m= min_snr_m, distance_mn= distance_mn, MIN_DIS= min_dis, result_dir = result_dir, MIN_TIME= min_time, FIRST_ANTENNA= first_antenna_region)
        elif mode == "fixed":
            solver_fixed(Max_Space= scen.n_sectors, Max_Time= num_slices, users_t_m= users_t_m, MAX_USER_PER_ANTENNA_m= max_user_antenna_m, antenasmap_m= antennas_map_m,
                         snr_map_mn= sinr_map, MIN_SNR_m= min_snr_m, distance_mn= distance_mn, MIN_DIS= min_dis, result_dir = result_dir, FIRST_ANTENNA= first_antenna_region)
        elif mode == "single":
            valid_time = 0
            print("- valid_time: ", valid_time)
            solver_single(Max_Space= scen.n_sectors, Max_Time= num_slices, users_t_m= users_t_m, MAX_USER_PER_ANTENNA_m= max_user_antenna_m, antenasmap_m= antennas_map_m, valid_time= valid_time,
                          snr_map_mn= sinr_map, MIN_SNR_m= min_snr_m, distance_mn= distance_mn, MIN_DIS= min_dis, result_dir= result_dir, FIRST_ANTENNA= first_antenna_region)

        elif mode == "ga":
            #TODO: Not working correctly with disaster > 0
            ga.ga_solver(num_regions=scen.n_sectors, num_slices=num_slices, users_t_m=users_t_m, max_users_per_antenna_m=max_user_antenna_m, snr_map_mn=sinr_map, min_sinr_w=db_to_linear(min_sinr),
                         distance_mn=distance_mn, min_dis=min_dis, result_dir=result_dir, first_antenna_region=first_antenna_region, fitness_func=ga.fitness_pygad)

        elif mode == "gwo":
            gwo.gwo_solver(scenario = scen, num_regions=scen.n_sectors, users_t_m=users_t_m, distance_mn=distance_mn, min_dis=min_dis, 
                        antenasmap_m= antennas_map_m, snr_map_mn=sinr_map, min_sinr_w=db_to_linear(min_sinr), first_antenna_region=first_antenna_region,
                        result_dir=result_dir, max_users_per_antenna_m=max_user_antenna_m, num_slices=num_slices)


    elif show_ues:
        # FIXME: 
        #Plotting ues configuration over time
        ues_coords = get_ues_time(ues_list= scen.getUEsList(), xml_filename= xml_filename)
        for t_ues in ues_coords:
            scen.plotUes(external= True, ues_positions= [u.position for u in t_ues])
    
    elif show_antennas_map:
        seed(chosen_seed)
        antennas_map_m = [(0 if random() < disaster_percentage/100 else 1) for i in range(scen.n_sectors)]

        nrows = int(size_y/size_sector)
        ncols = int(size_x/size_sector)

        res = np.array(antennas_map_m).reshape((nrows, ncols)).tolist()

        fig, ax = plt.subplots(figsize=(10, 10))

        ax.imshow(res, cmap='gray')

        plt.xticks(np.arange(-.5, ncols, 1))
        plt.yticks(np.arange(-.5, nrows, 1))
        plt.gca().set_xticklabels((np.arange(0, size_x+size_sector, size_sector)))
        plt.gca().set_yticklabels((np.arange(0, size_y+size_sector, size_sector)))
        plt.grid()
        plt.title(f'Antennas Map - {disaster_percentage}% Disaster')

        black_patch = mpatches.Patch(color='black', label='Unavailable')
        white_patch = mpatches.Patch(color='white', label='Available')
        plt.legend(handles= [black_patch, white_patch])

        plt.show()

        print("Plot")

    print(f"--- Done after {(time() - start_time)/(60*60)} hours. ---")
    sys.stdout = sys.__stdout__

def run_movement_simulation(ini_path: str, chosen_seed: int, size_x: int, size_y: int, size_sector: int, n_macros: int, ues_per_slice: list, n_ues: int, config_name: str= 'ilp_move_users',
                            num_slices: int= 10, simtime_move: int = 1000, slice_time: int = 1, cpu_num: int= 1):
    # Genereting .ini file
    scen = geo.MapChess(size_x = size_x, size_y = size_y, size_sector = size_sector, carrier_frequency= 0.7, chosen_seed= chosen_seed,
                        num_slices = num_slices, simtime_move= simtime_move, slice_time= slice_time)
    
    ilpc.ilp_move_users(scen, ini_path, n_macros= n_macros, n_ues_macro = n_ues, ues_per_slice = ues_per_slice, config_name= config_name)
    
    snapshot_filename = genf.gen_movement_filename(config_name= config_name, seed= chosen_seed, snapshot= True)

    open(snapshot_filename, 'w').close()
    
    frame_path = genf.get_frameworks_path()
    
    # Running Omnet++
    arg = ('cd ../Network_CCOpMv\n'
                          f'opp_runall -j{cpu_num} ./Network_CCOpMv -f ' + ini_path + r' -u Cmdenv -c ' + config_name + rf' -n .:{frame_path}/inet4/src:{frame_path}/inet4/examples:{frame_path}/inet4/tutorials:{frame_path}/inet4/showcases:{frame_path}/Simu5G-1.1.0/simulations:{frame_path}/Simu5G-1.1.0/src')

    code = subprocess.check_output(arg, shell= True)
    # code.check_returncode()

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


if __name__ == "__main__":
    main()
    print("Done")