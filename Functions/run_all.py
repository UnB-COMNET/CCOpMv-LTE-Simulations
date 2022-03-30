from concurrent.futures.process import EXTRA_QUEUED_CALLS
from typing import List
from gen_ilp_info import run_movement_simulation, gen_ilp_info
from multiprocessing import Process, cpu_count
from sys import stdout
from _5G_Scenarios.ILP_configs import ilp_sliced_ini, ilp_ned
from run_simulations import run_simulation
import subprocess
import sys
import io

def main():
    #General configs
    chosen_seed = 123
    size_x = 4000
    size_y = 4000
    size_sector = 400
    n_macros = 1
    min_sinrs = [5, 10, 15]
    mode = ''# varying or fixed else both
    result_dir = "Solutions/"

    #Solver configs
    ini_path = r"../Network_CCOpMv/_5G/simulations/ilp_fixed_users.ini"
    xml_filename = 'ilp_fixed_users-sched=MAXCI--0.sna'
    min_dis = 2000 #Enlace de rádio na prática (m)
    first_antenna_region = 1
    min_time = 2 #Tempo minimo que um antena deve existir ate ser movida

    #Simulation configs
    dir_path = '../Network_CCOpMv/_5G/simulations/'
    num_bands = [100]
    repetitions = 3
    slice_time = 1 #s
    #multi_carriers = False #Keep False
    #is_micro = True #Keep True
    p_size = 1428 #bytes (for voip = 40)
    app = "video" #video or voip
    extra_config_name= "video"
    target_f = 10 #Mbps
    cmdenv_config = True #Redirects cmdenv outputs to a file

    run_all(chosen_seed= chosen_seed, size_x= size_x, size_y= size_y, size_sector= size_sector, n_macros= n_macros,
            min_sinrs= min_sinrs, mode= mode, result_dir= result_dir, ini_path= ini_path, xml_filename= xml_filename,
            min_dis= min_dis, first_antenna_region= first_antenna_region, dir_path= dir_path, num_bands= num_bands,
            repetitions= repetitions, slice_time= slice_time, p_size= p_size, app= app, target_f= target_f,
            extra_config_name= extra_config_name, cmdenv_config= cmdenv_config, min_time= min_time)


def run_all(chosen_seed: int, size_x: int, size_y: int, size_sector: int, n_macros: int, min_sinrs: List[int],
            ini_path: str, xml_filename: str, min_dis: int, first_antenna_region: int, dir_path: str,
            num_bands: List[int], repetitions: int, p_size: int, app: str, target_f: float, mode: str= '',
            result_dir: str = './', slice_time: int = 1, multi_carriers: bool= False, is_micro: bool= True,
            extra_config_name: str = '', cmdenv_config: bool= True, min_time: int = 2):

    var = []
    processes = []

    if mode.lower() == 'varying':
        var = [True]
    elif mode.lower() == 'fixed':
        var = [False]
    else:
        var = [True, False]

    #Verifying if movement simulation is already done
    last_line = ''
    with open(xml_filename, 'r') as f:
        last_line = f.readlines()[-1]

    if last_line == '<!--Done-->\n':
        print(f'Movement profile already simulated. Results in {xml_filename}.')
    # If not done, do it    
    else:
        run_movement_simulation(ini_path= ini_path, chosen_seed= chosen_seed, size_x= size_x, size_y= size_y,
                                size_sector= size_sector, n_macros= n_macros, xml_filename= xml_filename)

    #Varying, fixed or both
    kwargs = {'chosen_seed' : chosen_seed, 'size_x': size_x, 'size_y': size_y, 'size_sector': size_sector, 'n_macros': n_macros, 'min_sinr': None,
              'varying': None, 'xml_filename': xml_filename, 'result_dir': result_dir, 'min_dis': min_dis, 'first_antenna_region': first_antenna_region,
              'dir_path': dir_path, 'num_bands': num_bands, 'repetitions': repetitions, 'slice_time': slice_time, 'p_size': p_size, 'app': app,
              'target_f': target_f, 'extra_config_name': extra_config_name, 'multi_carriers': multi_carriers, 'is_micro': is_micro, 'cmdenv_config': cmdenv_config,
              'min_time': min_time}


    print(f'Starting computations on {cpu_count()} cores.')
    for varying in var:
        kwargs['varying'] = varying

        for min_snr in min_sinrs:
    
            kwargs['min_sinr'] = min_snr

            processes.append(Process(target= process_func, kwargs= kwargs))
            processes[-1].start()
    
    for p in processes:
        p.join()

    for varying in var:
        get_csv(varying= varying, dir_path= dir_path, extra_config_name= extra_config_name)

def process_func(chosen_seed: int, size_x: int, size_y: int, size_sector: int, n_macros: int, min_sinr: int,
                varying: bool, xml_filename: str, min_dis: int, first_antenna_region: int, dir_path: str,
                num_bands: List[int], repetitions: int, p_size: int, app: str, target_f: float,
                result_dir: str = './', slice_time: int = 1, multi_carriers: bool= False, is_micro: bool= True,
                extra_config_name: str = '', cmdenv_config: bool = True, min_time: int = 2):

    mode = "varying" if varying else "fixed"
    file_name = f'ilp_{mode}_sliced_{str(min_sinr)}'

    #Running solver
    gen_ilp_info(chosen_seed= chosen_seed, size_x= size_x, size_y= size_y, size_sector= size_sector, n_macros= n_macros,
                 xml_filename= xml_filename, min_sinr= min_sinr, result_dir= result_dir, varying= varying, min_dis= min_dis,
                 first_antenna_region= first_antenna_region, min_time= min_time)

    #Generating config and network files
    print("Generating configuration files - Min Snr: {} - {}".format(min_sinr, mode.capitalize()))
    
    ini_path_sliced = dir_path + f'{file_name}.ini'
    network_name = f"ILP{mode.capitalize()}Net{str(min_sinr)}"

    config_name_sliced, enbs_sliced_num = ilp_sliced_ini(ini_path_sliced, chosen_seed, size_y= size_y, size_x= size_x, size_sector= size_sector, n_macros= n_macros, repetitions= repetitions,
                                                         min_sinr= min_sinr, num_bands= num_bands, multi_carriers= multi_carriers, is_micro= is_micro, p_size= p_size, app= app, extra_config_name= extra_config_name,
                                                         time= slice_time, target_f= target_f, result_dir= result_dir, varying = varying, network_name= network_name, cmdenv_config= cmdenv_config)

    ilp_ned(network = network_name, n_enbs= enbs_sliced_num, size_x= size_x, size_y= size_y)

    #Running the simulation
    run_simulation(ini_path= ini_path_sliced, config_name= config_name_sliced, cpu_num= cpu_count())

def get_csv(varying: bool, dir_path: str, extra_config_name: str = ''):

    mode = 'varying' if varying else 'fixed'
    result_dir = dir_path + 'results/'
    if extra_config_name != '':
        extra_config_name = '_' + extra_config_name 
    path = result_dir + f'ilp_{mode}_sliced_*' + extra_config_name
    path_csv = result_dir + f'ilp_{mode}_sliced' + extra_config_name

    print(f'Making .csv of {path_csv}.')

    subprocess.call(f'scavetool x -o {path_csv}.csv -f "module(**.cellularNic.channelModel[*]) OR module(**.app[*])" {path}/*-*.sca {path}/*-*.vec', shell= True)

if __name__ == "__main__": 
    main()
    print("Done")