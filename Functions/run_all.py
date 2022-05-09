# Version 08/05/2022

from math import ceil
from typing import List
from gen_ilp_info import run_movement_simulation, gen_ilp_info, gen_file_name
from multiprocessing import cpu_count, Process
from _5G_Scenarios.ILP_configs import ilp_sliced_ini, ilp_sliced_ini_per_slice, ilp_ned, gen_solver_result_filename, gen_movement_filename, gen_sliced_config_pattern
from run_simulations import run_make, run_simulation_all_slices, run_simulation_per_slice
from joblib import Parallel, delayed, parallel_backend
from pathlib import Path
import subprocess
import sys
from errors import check_mode
#import psutil
#import time

SUCCESS = 'SUCCESS'

def main():
    #General configs
    chosen_seeds = [352,512,791,854]#
    size_x = 4000
    size_y = 4000
    size_sector = 400
    n_macros = 1
    min_sinrs = [5,10,15]
    modes = ['varying','single'] # varying, fixed or single
    result_dir = "Solutions"
    micro_power = 30 #dBm
    project_dir = '../Network_CCOpMv'
    sim_dir = '_5G/simulations'
    extra_dir = ['disaster_percentage','micro_power']
    num_slices = 10
    per_slice = True
    allrun_solver = True
    
    #Solver configs
    move_config_name = 'ilp_move_users'
    min_dis = 2000 #Enlace de rÃ¡dio na prÃ¡tica (m)
    first_antenna_region = 1
    min_time = 2 #Tempo minimo que um antena deve existir ate ser movida
    disaster_percentage = 50 #Porcentagem do alastramento do desastre (%)

    #Simulation configs
    net_dir = '_5G/networks'
    num_bands = [100]
    repetitions = 1
    slice_time = 1 #s
    #multi_carriers = False #Keep False
    #is_micro = True #Keep True
    p_size = 1428 #bytes (for voip = 40)
    app = "video" #video or voip
    extra_config_name= "video"
    target_f = 10 #Mbps
    cmdenv_config = True #Redirects cmdenv outputs to a file

    result = run_multiple_seeds(chosen_seeds= chosen_seeds, size_x= size_x, size_y= size_y, size_sector= size_sector, n_macros= n_macros,
                       min_sinrs= min_sinrs, project_dir= project_dir, sim_dir= sim_dir, modes= modes, result_dir= result_dir,
                       move_config_name= move_config_name, min_dis= min_dis, first_antenna_region= first_antenna_region,
                       net_dir= net_dir, num_bands= num_bands, repetitions= repetitions, slice_time= slice_time, p_size= p_size,
                       app= app, target_f= target_f, extra_config_name= extra_config_name, cmdenv_config= cmdenv_config,
                       min_time= min_time, micro_power= micro_power, extra_dir= extra_dir, num_slices= num_slices, per_slice= per_slice,
                       allrun_solver = allrun_solver, disaster_percentage= disaster_percentage)
    
    if result == SUCCESS:
        print('Executions have been successfully.')
    else:
        print("ERROR!")
    

def run_multiple_seeds(chosen_seeds: List[int], size_x: int, size_y: int, size_sector: int, n_macros: int, min_sinrs: List[int],
                       project_dir: str, sim_dir: str, move_config_name: str, min_dis: int, first_antenna_region: int,
                       net_dir: str, num_bands: List[int], repetitions: int, p_size: int, app: str, target_f: float, modes: List[str]= [],
                       result_dir: str = '.', slice_time: int = 1, multi_carriers: bool= False, is_micro: bool= True,
                       extra_config_name: str = '', cmdenv_config: bool= True, min_time: int = 2, micro_power: int = 30,
                       extra_dir: List[str] = [], num_slices: int= 10, per_slice: bool= True, allrun_solver: bool = False, disaster_percentage: int = 0):
    """This function is used to run multiple 'run_all' functions in diferent processes, one for each value in chosen_seeds."""
    
    # Generating makefile and compiling OMNeT++ and its frameworks
    print(f'\nRunning makefile.')
    run_make()  
    
    # Evaluating maximum runs
    num_seeds = len(chosen_seeds)
    num_modes = len(modes)
    num_minSinrs = len(min_sinrs)
    num_cases = num_seeds * num_modes * num_minSinrs
    num_totalRuns =  num_cases * num_slices * repetitions
    num_cases_simultaneously = ceil(cpu_count()/(num_slices*repetitions))
    print("Simulating at most {} cases, hence {} runs. There are {} CPU cores available".format(num_cases, num_totalRuns, cpu_count()))
    
    # Changing the results directory hierarchy
    extra_dir = ['chosen_seed'] + extra_dir 

    # Checking for the existence of optimizer solution files and running solver for non-existent ones using parallel computing
    missing_snapshots = get_missing_snapshots(chosen_seeds, move_config_name)
    run_missing_snapshots(missing_snapshots, size_x, size_y, size_sector, n_macros, project_dir,sim_dir, move_config_name, num_slices)
    
    if allrun_solver is True:
        missing_solutions = get_missing_solutions(chosen_seeds, min_sinrs, modes, extra_dir, micro_power, disaster_percentage)
        print("There are {} missing solutions.".format(len(missing_solutions)))
        for i in range(len(missing_solutions)):
            print(missing_solutions[i])
        if len(missing_solutions) > num_cases_simultaneously:
            kwargs = {'result_dir': result_dir, 'sim_dir': sim_dir, 'chosen_seed': chosen_seeds, 'micro_power': micro_power, 'disaster_percentage': disaster_percentage}
            run_missing_solutions(missing_solutions, size_x, size_y, size_sector, n_macros, result_dir, move_config_name, min_dis, first_antenna_region, min_time, micro_power, disaster_percentage, num_slices, extra_dir, kwargs)        
    
    print('Running {} cases simultaneously.'.format(num_cases_simultaneously))

    kwargs = {'chosen_seed' : None, 'size_x': size_x, 'size_y': size_y, 'size_sector': size_sector, 'n_macros': n_macros, 'min_sinrs': min_sinrs,
              'modes': modes, 'move_config_name': move_config_name, 'result_dir': result_dir, 'min_dis': min_dis, 'first_antenna_region': first_antenna_region,
              'sim_dir': sim_dir, 'num_bands': num_bands, 'repetitions': repetitions, 'num_cases_simultaneously': num_cases_simultaneously, 'slice_time': slice_time, 'p_size': p_size, 'app': app,
              'target_f': target_f, 'extra_config_name': extra_config_name, 'multi_carriers': multi_carriers, 'is_micro': is_micro, 'cmdenv_config': cmdenv_config,
              'min_time': min_time, 'micro_power': micro_power, 'net_dir': net_dir, 'project_dir': project_dir, 'extra_dir': extra_dir, 'num_slices': num_slices,
              'per_slice': per_slice, 'disaster_percentage': disaster_percentage}
    

    print('\nRunnning cases by seeds one by one.')
    j = 0
    for i in range(len(chosen_seeds)):
        kwargs['chosen_seed'] = chosen_seeds[j]
        print("CHOSEN SEED: {}".format(chosen_seeds[j]))
        result = run_all(**kwargs)
        if result == SUCCESS:
            chosen_seeds.remove(chosen_seeds[j])
        else:
            print('Error in cases with seed {}.'.format(chosen_seeds[j]))
            j += 1

    if chosen_seeds == []:
        return SUCCESS
    else:
        return

def run_all(chosen_seed: int, size_x: int, size_y: int, size_sector: int, n_macros: int, min_sinrs: List[int],
            project_dir: str, sim_dir: str, move_config_name: str, min_dis: int, first_antenna_region: int,
            net_dir: str, num_bands: List[int], repetitions: int, num_cases_simultaneously: int, p_size: int, app: str, target_f: float, modes: List[str]= [],
            result_dir: str = '.', slice_time: int = 1, multi_carriers: bool= False, is_micro: bool= True,
            extra_config_name: str = '', cmdenv_config: bool= True, min_time: int = 2, micro_power: int = 30,
            extra_dir: List[str] = [], num_slices: int= 10, make: bool= False, per_slice: bool= True, disaster_percentage: int= 0):
    """This function is used to run all steps of a scenario study, using one process for each case diferent scenario, determined by the mode and min_sinrs."""
    
    verif_modes = []
    processes = []

    for mode in modes:
        if mode.lower() == 'varying':
            verif_modes.append('varying')
        elif mode.lower() == 'fixed':
            verif_modes.append('fixed')
        elif mode.lower() == 'single':
            verif_modes.append('single')

    # Preparing a row of cases for simulation
    num_modes = len(verif_modes)
    num_minSinrs = len(min_sinrs)
    cases = []
    for i in range(num_modes):
        for j in range(num_minSinrs):
                cases.append((verif_modes[i],min_sinrs[j]))

    move_file = gen_movement_filename(move_config_name, chosen_seed, snapshot= False)
    xml_filename = gen_movement_filename(move_config_name, chosen_seed, snapshot= True)
    
    #Verifying if movement simulation is already done
    done = compare_last_line(xml_filename, '<!--Done-->\n')
    if done:
        print(f'Movement profile already simulated. Results in {xml_filename}.')
    # If not done, do it    
    else:
        move_ini_path = project_dir + '/' + sim_dir + '/' + move_file
        run_movement_simulation(ini_path= move_ini_path, chosen_seed= chosen_seed, size_x= size_x, size_y= size_y,
                                size_sector= size_sector, n_macros= n_macros, config_name= move_config_name,
                                num_slices= num_slices, cpu_num= cpu_count())

    #Varying, fixed or both
    kwargs = {'chosen_seed' : chosen_seed, 'size_x': size_x, 'size_y': size_y, 'size_sector': size_sector, 'n_macros': n_macros, 'min_sinr': None,
              'mode': None, 'xml_filename': xml_filename, 'result_dir': result_dir, 'min_dis': min_dis, 'first_antenna_region': first_antenna_region,
              'sim_dir': sim_dir, 'num_bands': num_bands, 'repetitions': repetitions, 'slice_time': slice_time, 'p_size': p_size, 'app': app,
              'target_f': target_f, 'extra_config_name': extra_config_name, 'multi_carriers': multi_carriers, 'is_micro': is_micro, 'cmdenv_config': cmdenv_config,
              'min_time': min_time, 'micro_power': micro_power, 'net_dir': net_dir, 'project_dir': project_dir, 'num_slices': num_slices, 'per_slice': per_slice,
              'disaster_percentage': disaster_percentage}
    
    for param in extra_dir:
        kwargs['result_dir'] += '/' + param + f'_{kwargs[param]}'
        kwargs['sim_dir'] += '/' + param + f'_{kwargs[param]}'
        kwargs['net_dir'] += '/' + param + f'_{kwargs[param]}'
        Path(kwargs['result_dir']).mkdir(parents=True, exist_ok=True)
        Path(project_dir + '/' + kwargs['sim_dir']).mkdir(parents=True, exist_ok=True)
        Path(project_dir + '/' + kwargs['net_dir']).mkdir(parents=True, exist_ok=True)

    print(f'Starting computations on {cpu_count()} cores.')
    result_dir = kwargs['result_dir']
    sim_dir = kwargs['sim_dir']
    net_dir = kwargs['net_dir']
    
    with parallel_backend('loky'):
        result = Parallel(n_jobs=num_cases_simultaneously)(delayed(process_func)(chosen_seed, size_x, size_y, size_sector, n_macros, min_sinr,
                mode, xml_filename, min_dis, first_antenna_region, project_dir, sim_dir, net_dir, num_bands, repetitions, p_size, app,
                target_f,result_dir, slice_time, multi_carriers,
                is_micro,extra_config_name, cmdenv_config, min_time,
                micro_power, num_slices, per_slice, disaster_percentage) for mode, min_sinr in cases)
    
    return_success = True
    for i in range(len(result)):
        if result[i] != SUCCESS:
            mode, min_sinr = cases[i]
            print('Error in case: mode {} and min SINR {}'.format(mode, min_sinr))
            return_success = False

    if return_success:
        print('\nExporting .CSV files.\n')
        for mode in verif_modes:
            get_csv(mode= mode, sim_path= project_dir + '/' + kwargs['sim_dir'], extra_config_name= extra_config_name)
        return SUCCESS
    else:
        return

def process_func(chosen_seed: int, size_x: int, size_y: int, size_sector: int, n_macros: int, min_sinr: int,
                 mode: str, xml_filename: str, min_dis: int, first_antenna_region: int, project_dir: str,
                 sim_dir: str, net_dir: str, num_bands: List[int], repetitions: int, p_size: int, app: str,
                 target_f: float,result_dir: str = '.', slice_time: int = 1, multi_carriers: bool= False,
                 is_micro: bool= True,extra_config_name: str = '', cmdenv_config: bool = True, min_time: int = 2,
                 micro_power: int= 30, num_slices: int= 10, per_slice: bool = True, disaster_percentage: int = 0):
    """This function defines the behaviour of each process, running both the solver and the simulation of a single scenario."""
    print("\nRunning case {} {} dB, seed {}, micro power {}, disaster percentage {}\n".format(mode,min_sinr, chosen_seed, micro_power, disaster_percentage))
    
    check_mode(mode= mode)

    file_name = gen_file_name(mode= mode, min_sinr= min_sinr)
    sim_path = project_dir + '/' + sim_dir
    #Verifying if solver is already done
    done = compare_last_line(gen_solver_result_filename(result_dir, mode, min_sinr), '--- Done ---\n')
    
    if done:
        print(f'Solver {file_name} already computed. (Seed: {chosen_seed})')
    # If not done, do it    
    else:
        #Running solver
        gen_ilp_info(chosen_seed= chosen_seed, size_x= size_x, size_y= size_y, size_sector= size_sector, n_macros= n_macros,
                    xml_filename= xml_filename, min_sinr= min_sinr, result_dir= result_dir, mode= mode, min_dis= min_dis,
                    first_antenna_region= first_antenna_region, min_time= min_time, micro_power= micro_power, num_slices= num_slices,
                    disaster_percentage= disaster_percentage)

    #while psutil.virtual_memory().percent > 40:
    #    print(f'High memory use ({psutil.virtual_memory().percent}). Sleeping.({file_name} : {chosen_seed})')
    #    time.sleep(600)

    #Generating config and network files
    print("Generating configuration files - Min Snr: {} - {} (Seed: {})".format(min_sinr, mode.capitalize(), chosen_seed))
    
    ini_path_sliced = sim_path + '/' + f'{file_name}.ini'
    network_name = f"ILP{mode.capitalize()}Net{str(min_sinr)}"

    if per_slice and mode != 'single':
        config_name_sliced_list, num_enbs_time = ilp_sliced_ini_per_slice(ini_path_sliced, chosen_seed, size_y= size_y, size_x= size_x, size_sector= size_sector, n_macros= n_macros, repetitions= repetitions,
                                                                min_sinr= min_sinr, num_bands= num_bands, multi_carriers= multi_carriers, is_micro= is_micro, p_size= p_size, app= app, extra_config_name= extra_config_name,
                                                                slice_time= slice_time, target_f= target_f, result_dir= result_dir, mode = mode, network_name= network_name, cmdenv_config= cmdenv_config,
                                                                micro_power= micro_power, net_dir= net_dir, xml_filename= xml_filename)

        if config_name_sliced_list == None and num_enbs_time == None:
            #There was a not feasible solution
            print("The case seed {}, mode {}, min sinr {} dB, {}%% disaster is not feasible.".format(chosen_seed, mode, min_sinr, disaster_percentage))
            return None

        for slice in range(len(num_enbs_time)):
            network_name = f"ILP{mode.capitalize()}Net{str(min_sinr)}Slice{str(slice)}"
            ilp_ned(network = network_name, n_enbs= num_enbs_time[slice], size_x= size_x, size_y= size_y, net_dir= net_dir, project_dir= project_dir)
    
    else:
        config_name_sliced, enbs_sliced_num = ilp_sliced_ini(ini_path_sliced, chosen_seed, size_y= size_y, size_x= size_x, size_sector= size_sector, n_macros= n_macros, repetitions= repetitions,
                                                         min_sinr= min_sinr, num_bands= num_bands, multi_carriers= multi_carriers, is_micro= is_micro, p_size= p_size, app= app, extra_config_name= extra_config_name,
                                                         slice_time= slice_time, target_f= target_f, result_dir= result_dir, mode = mode, network_name= network_name, cmdenv_config= cmdenv_config,
                                                         micro_power= micro_power, net_dir= net_dir, xml_filename= xml_filename)

        ilp_ned(network = network_name, n_enbs= enbs_sliced_num, size_x= size_x, size_y= size_y, net_dir= net_dir, project_dir= project_dir)
    
    #Running the simulation
    run_numbers = get_missing_simulations(mode= mode, num_bands= num_bands, repetitions= repetitions, sim_path= sim_path,
                                          min_sinr= min_sinr, num_slices= num_slices, multi_carriers= multi_carriers, extra_config_name= extra_config_name)
                    
    if run_numbers == []:
        print('All simulations are already computed.')
    else:
        if per_slice and mode != 'single':
            run_simulation_per_slice(ini_path= ini_path_sliced, repetitions= repetitions, config_name_list= config_name_sliced_list, cpu_num= cpu_count(), run_numbers= run_numbers)
        else:
            run_simulation_all_slices(ini_path= ini_path_sliced, config_name= config_name_sliced, cpu_num= cpu_count(), run_numbers= run_numbers)

    return SUCCESS

def get_csv(mode: str, sim_path: str, extra_config_name: str = ''):
    """This function call a scavetool command to create the necessary .csv files"""

    check_mode(mode= mode)

    result_dir = sim_path + '/results'
    if extra_config_name != '':
        extra_config_name = '_' + extra_config_name 
    path = result_dir + f'/ilp_{mode}_sliced_*' + extra_config_name
    path_csv = result_dir + f'/ilp_{mode}_sliced' + extra_config_name

    print(f'Making .csv of {path_csv}.')

    code = subprocess.run(f'scavetool x -o {path_csv}.csv -f "module(**.cellularNic.channelModel[*]) OR module(**.app[*])" {path}/*-*.sca {path}/*-*.vec', shell= True)

    code.check_returncode()

def compare_last_line(filename: str, line: str):
    """This function compare the last line of a file with the informed string."""

    last_line = ''
    count = 0
    try:
        with open(filename, 'r') as f:
            for l in f:
                last_line = l
                count += 1

        if count <= 1:
            return False

    except FileNotFoundError:
                    return False
    else:
        return last_line == line

def get_missing_simulations(mode: str, num_bands: List[int], repetitions: int, sim_path: str, min_sinr: int, num_slices: int, multi_carriers: bool, extra_config_name: str):
    """This function returns the simulation runs that were not executed yet"""

    sim_resultdir = f'{sim_path}/results'
    counter = 0
    missing = []
    config_pattern = gen_sliced_config_pattern(min_sinr= min_sinr, mode= mode, multi_carriers= multi_carriers, extra_config_name= extra_config_name)
    for band in num_bands:
        for slice in range(num_slices):
            for repetition in range(repetitions):
                filename = f'{sim_resultdir}/{config_pattern}-cmdout/{min_sinr}-{band}-{repetition}-{slice}.out'
                done = compare_last_line(filename, '[INFO]\tClear all sockets\n')
                if not done:
                    missing.append(counter)

                counter += 1

    return missing

def get_missing_solutions(chosen_seeds: List[int], min_sinrs: List[int], modes: List[str],\
                          extra_dir: List[str], micro_power: int, disaster_percentage: int) -> List[tuple]:
    """ This function returns the solver solutions that were not computed yet"""
    missing = []
    for chosen_seed in chosen_seeds:
        result_dir = 'Solutions/' + 'chosen_seed_{}'.format(chosen_seed) +  '/{}_{}'.format(extra_dir[1],disaster_percentage)\
            + '/{}_{}'.format(extra_dir[2],micro_power)
        for mode in modes:
            for min_sinr in min_sinrs:
                # Looking for case: 
                done = compare_last_line(gen_solver_result_filename(result_dir,mode,min_sinr),'--- Done ---\n')
                if done is not True:
                    missing.append((chosen_seed,mode,min_sinr))

    return missing

def get_missing_snapshots(chosen_seeds: List[int], move_config_name: str):
    missing = []
    for chosen_seed in chosen_seeds:
        #move_file = gen_movement_filename(move_config_name, chosen_seed, snapshot= False)
        xml_filename = gen_movement_filename(move_config_name, chosen_seed, snapshot= True)
        done = compare_last_line(xml_filename, '<!--Done-->\n')
        if done is not True:
            missing.append(chosen_seed)
    return missing
        
def run_missing_solutions(missing_solutions: List[tuple], size_x: int, size_y: int, size_sector: int, n_macros: int,
                 result_dir: str, move_config_name: str, min_dis: int, first_antenna_region: int, min_time: int,
                 micro_power: int, disaster_percentage: int, num_slices: int, extra_dir: List[str], kwargs: dict):
    if missing_solutions != []:
        print("Running solver for {} missing solutions".format(len(missing_solutions)))

        # Making directories
        for chosen_seed in kwargs['chosen_seed']:
            kwargs['chosen_seed'] = chosen_seed
            kwargs['result_dir'] = result_dir
            for param in extra_dir:
                kwargs['result_dir'] += '/' + param + f'_{kwargs[param]}'
                Path(kwargs['result_dir']).mkdir(parents=True, exist_ok=True)
          
        with parallel_backend('loky'):
            Parallel(n_jobs=cpu_count())(delayed(gen_ilp_info)(chosen_seed, size_x, size_y, size_sector, n_macros,
                        gen_movement_filename(move_config_name, chosen_seed, snapshot= True), min_sinr, f"Solutions/chosen_seed_{chosen_seed}/disaster_percentage_{disaster_percentage}/micro_power_{micro_power}", mode, min_dis,
                        first_antenna_region, min_time, micro_power, num_slices, disaster_percentage) for chosen_seed, mode, min_sinr in missing_solutions)

def run_missing_snapshots(missing_snapshots: List[int], size_x: int, size_y: int, size_sector: int, n_macros: int, project_dir: str,\
                          sim_dir: str, move_config_name: str, num_slices):
    if missing_snapshots != []:
        print("Running movement simulation for {} seeds".format(len(missing_snapshots)))
        with parallel_backend('loky'):
            Parallel(n_jobs=cpu_count())(delayed(run_movement_simulation)(project_dir + '/' + sim_dir + '/' +
                    gen_movement_filename(move_config_name, chosen_seed, snapshot= False), chosen_seed, size_x, size_y,
                    size_sector, n_macros, move_config_name, num_slices, cpu_count()) for chosen_seed in missing_snapshots)
    
if __name__ == "__main__": 
    main()