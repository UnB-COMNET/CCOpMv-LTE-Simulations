# Version 19/01/2023

from math import ceil
from typing import List
from gen_ilp_info import run_movement_simulation, gen_ilp_info
from multiprocessing import cpu_count, Process, current_process, Manager, Queue
from _5G_Scenarios.ILP_configs import ilp_sliced_ini, ilp_sliced_ini_per_slice, ilp_ned
from run_simulations import run_make, run_simulation_all_slices, run_simulation_per_slice
from joblib import Parallel, delayed, parallel_backend
from pathlib import Path
import subprocess
from errors import check_mode, ErrorPackage
import geometry as geo
import general_functions as genf
import sys
import traceback
import errors

SUCCESS = 'SUCCESS'

semaphore_cpucount = Manager().Semaphore(cpu_count())

def main():
    #General configs
    chosen_seeds = [2,3,4,5,6,7,10,11,12,13] #range(20)
    size_x = 4000
    size_y = 4000
    size_sector = 400
    n_macros = 1
    min_sinrs = [5,10,15]
    modes = ['pgwo2'] # fixed or single or ga or gwo
    micro_power = 30 #dBm
    result_dir = "Solutions"
    project_dir = '../Network_CCOpMv'
    sim_dir = '_5G/simulations'
    csv_dir = '_5G/results'
    extra_dir = ['disaster_percentage','micro_power','chosen_seed']
    lambda_poisson_gen_users_t_m = 30
    num_slices = 12
    simtime_move = 1200
    per_slice = True
    
    #Solver configs
    move_config_name = 'ilp_move_users'
    min_dis = 2000 #Enlace de radio na pratica (m)
    first_antenna_region = None #Pega uma posição possível aleatória
    min_time = 2 #Tempo minimo que um antena deve existir ate ser movida
    disaster_percentage = 0 #Porcentagem do alastramento do desastre (%)

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
    interference = False #Enables or disables multicell-interference

    # For the user
    allrun_solver = False # Older version where runs all solvers first
    only_solver = False # Option to run only the solver and never the simulator. Cannot be True if allrun_solver is True.

    if only_solver == True and allrun_solver == True:
        print("The option only_solver connot be True if allrun_solver is also True.")
        return

    result = run_multiple_seeds(chosen_seeds= chosen_seeds, size_x= size_x, size_y= size_y, size_sector= size_sector, n_macros= n_macros,
                                min_sinrs= min_sinrs, project_dir= project_dir, sim_dir= sim_dir, csv_dir= csv_dir, modes= modes,
                                result_dir= result_dir, move_config_name= move_config_name, min_dis= min_dis, first_antenna_region= first_antenna_region,
                                net_dir= net_dir, num_bands= num_bands, repetitions= repetitions, slice_time= slice_time, p_size= p_size,
                                app= app, target_f= target_f, extra_config_name= extra_config_name, cmdenv_config= cmdenv_config,
                                min_time= min_time, micro_power= micro_power, extra_dir= extra_dir, num_slices= num_slices, simtime_move= simtime_move,
                                per_slice= per_slice, allrun_solver = allrun_solver, disaster_percentage= disaster_percentage, only_solver= only_solver,
                                lambda_poisson_gen_users_t_m = lambda_poisson_gen_users_t_m, interference = interference)
    
    if result == SUCCESS:
        print('Executions ended successfully.')
    else:
        print("ERROR!")
    

def run_multiple_seeds(chosen_seeds: List[int], size_x: int, size_y: int, size_sector: int, n_macros: int, min_sinrs: List[int], project_dir: str,
                       sim_dir: str, csv_dir: str, move_config_name: str, min_dis: int, first_antenna_region: int, net_dir: str, num_bands: List[int],
                       repetitions: int, p_size: int, app: str, target_f: float, modes: List[str]= [], result_dir: str = '.', slice_time: int = 1,
                       multi_carriers: bool= False, is_micro: bool= True, extra_config_name: str = '', cmdenv_config: bool= True, min_time: int = 2,
                       micro_power: int = 30, extra_dir: List[str] = [], num_slices: int= 10, simtime_move: int=1000, per_slice: bool= True,
                       allrun_solver: bool = False, disaster_percentage: int = 0, lambda_poisson_gen_users_t_m: int = 10, only_solver: bool = False,
                       interference: bool = False):
    """This function is used to run multiple 'run_all' functions in diferent processes, one for each value in chosen_seeds."""
    
    # Generating makefile and compiling OMNeT++ and its frameworks
    if not only_solver:
        print(f'\nRunning makefile.')
        run_make()
    else:
        print(f'Solver only option selected.')
        if allrun_solver:
            # BUG: The option in this case is not correctly implemented, so better not allow using it.
            # It is necessary to deal with simultaneous large memory and CPU usage.             
            print(f'Error: Not possible to run with both allrun_solve and only_solver set to True.')
            return
    
    # Evaluating maximum runs
    num_seeds = len(chosen_seeds)
    num_modes = len(modes)
    num_minSinrs = len(min_sinrs)
    num_cases = num_seeds * num_modes * num_minSinrs
    num_totalRuns =  num_cases * num_slices * repetitions
    num_cases_simultaneously = ceil(cpu_count()/(num_slices*repetitions))
    print("Simulating at most {} cases, hence {} runs. There are {} CPU cores available".format(num_cases, num_totalRuns, cpu_count()))
    
    # TODO: REMOVE. Changing the results directory hierarchy
    # TODO: REMOVE. extra_dir = extra_dir + ['chosen_seed'] 
    """
    if allrun_solver is True:
        # Checking for the existence of optimizer solution files and running solver for non-existent ones using parallel computing
        missing_snapshots = get_missing_snapshots(chosen_seeds, move_config_name)
        run_missing_snapshots(missing_snapshots, size_x, size_y, size_sector, n_macros, project_dir,sim_dir, move_config_name, num_slices)
    
        missing_solutions = get_missing_solutions(chosen_seeds, min_sinrs, modes, extra_dir, micro_power, disaster_percentage)
        print("There are {} missing solutions.".format(len(missing_solutions)))
        for i in range(len(missing_solutions)):
            print(missing_solutions[i])
        if len(missing_solutions) > num_cases_simultaneously:
            kwargs_tmp = {'result_dir': result_dir, 'sim_dir': sim_dir, 'chosen_seed': chosen_seeds, 'micro_power': micro_power, 'disaster_percentage': disaster_percentage}
            run_missing_solutions(missing_solutions, size_x, size_y, size_sector, n_macros, result_dir, move_config_name, min_dis, first_antenna_region, min_time, micro_power, num_slices, extra_dir, kwargs_tmp)        
    """
    print('Running {} cases simultaneously.'.format(num_cases_simultaneously))

    kwargs = {'chosen_seed' : None, 'size_x': size_x, 'size_y': size_y, 'size_sector': size_sector, 'n_macros': n_macros, 'min_sinrs': min_sinrs,
              'modes': modes, 'move_config_name': move_config_name, 'result_dir': result_dir, 'min_dis': min_dis, 'first_antenna_region': first_antenna_region,
              'sim_dir': sim_dir, 'csv_dir': csv_dir, 'num_bands': num_bands, 'repetitions': repetitions, 'num_cases_simultaneously': num_cases_simultaneously,
              'slice_time': slice_time, 'p_size': p_size, 'app': app, 'target_f': target_f, 'extra_config_name': extra_config_name, 'multi_carriers': multi_carriers,
              'is_micro': is_micro, 'cmdenv_config': cmdenv_config, 'min_time': min_time, 'micro_power': micro_power, 'net_dir': net_dir, 'project_dir': project_dir,
              'extra_dir': extra_dir, 'num_slices': num_slices, 'simtime_move': simtime_move , 'per_slice': per_slice, 'disaster_percentage': disaster_percentage,
              'allrun_solver': allrun_solver, 'lambda_poisson_gen_users_t_m': lambda_poisson_gen_users_t_m, 'interference': interference}  

    if allrun_solver is True:
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
    
    else:
        processes = []
        q = Queue()
        kwargs['queue'] = q
        kwargs['only_solver'] = only_solver
        for chosen_seed in chosen_seeds:
            kwargs['chosen_seed'] = chosen_seed
            processes.append(Process(target= run_all, kwargs= kwargs))
            processes[-1].start()
        
        for p in processes:
            p.join()

        errors = []
        while not q.empty():
            errors.append(q.get())

        if errors == []:
            chosen_seeds = []
        else:
            for error in errors:
                print(error)

    if chosen_seeds == []:
        return SUCCESS
    else:
        return

def run_all(chosen_seed: int, size_x: int, size_y: int, size_sector: int, n_macros: int, min_sinrs: List[int],
            project_dir: str, sim_dir: str, csv_dir: str, move_config_name: str, min_dis: int, first_antenna_region: int,
            net_dir: str, num_bands: List[int], repetitions: int, num_cases_simultaneously: int, p_size: int, app: str, target_f: float,
            modes: List[str]= [], result_dir: str = '.', slice_time: int = 1, multi_carriers: bool= False, is_micro: bool= True,
            extra_config_name: str = '', cmdenv_config: bool= True, min_time: int = 2, micro_power: int = 30,
            extra_dir: List[str] = [], num_slices: int= 10, simtime_move: int = 1000, make: bool= False, per_slice: bool= True,
            disaster_percentage: int= 0, lambda_poisson_gen_users_t_m: int = 10, allrun_solver: bool= False, queue: Queue= None,
            only_solver: bool = False, interference: bool = False):
    """ This function is used to run all steps of a scenario study, using one process for each case diferent scenario,
        determined by the mode and min_sinrs."""
    
    if not allrun_solver:
        print(f'Started process run_all {current_process().name} {current_process().pid}. (Seed: {chosen_seed})')
    
    verif_modes = genf.verify_modes(modes)

    # Preparing a row of cases for simulation
    num_modes = len(verif_modes)
    num_minSinrs = len(min_sinrs)
    cases = []
    for i in range(num_modes):
        for j in range(num_minSinrs):
                cases.append((verif_modes[i],min_sinrs[j]))

    # Generating amount of users following the Poisson process
    users_t_m = genf.gen_users_t_m(chosen_seed, lambda_poisson = lambda_poisson_gen_users_t_m, num_slices=num_slices)             
    ues_per_slice = genf.gen_ue_per_slice(chosen_seed, users_t_m, num_slices=num_slices)
    max_ues = max(users_t_m)

    print("Number of users over time, mu poisson: ", lambda_poisson_gen_users_t_m)
    print(users_t_m)
    print('\nUEs per slice')
    for i in range(len(ues_per_slice)):
        print(ues_per_slice[i])
    print('\n')
    
    move_filename = genf.gen_movement_filename(move_config_name, chosen_seed, snapshot= False)
    xml_filename = genf.gen_movement_filename(move_config_name, chosen_seed, snapshot= True)

    # Semaphore to control the use of the cpu
    with semaphore_cpucount:
        try:
            #Verifying if movement simulation is already done
            done = compare_last_line(xml_filename, '<!--Done-->\n')
            if done:
                print(f'Movement profile already simulated. Results in {xml_filename}.')
            # If not done, do it    
            else:
                if only_solver:
                    print(f'Error: Moviment profile missing (Seed: {chosen_seed}) with only_solver True. Returning.')
                    return
                else:
                    move_ini_path = project_dir + '/' + sim_dir + '/' + move_filename
                    run_movement_simulation(ini_path= move_ini_path, chosen_seed= chosen_seed, size_x= size_x, size_y= size_y,
                                            size_sector= size_sector, n_macros= n_macros, ues_per_slice = ues_per_slice, n_ues = max_ues,
                                            config_name= move_config_name, num_slices= num_slices, simtime_move=simtime_move, slice_time=slice_time, cpu_num= 1)
                    
        except Exception as e:
            if queue is not None:
                queue.put(ErrorPackage(exc_info= sys.exc_info(), pname= current_process().name, pid= current_process().pid, **{'seed': chosen_seed}))
            print(f'Terminated because of exception while running {xml_filename}.')
            return

    #Varying, fixed or both
    kwargs = {'chosen_seed' : chosen_seed, 'size_x': size_x, 'size_y': size_y, 'size_sector': size_sector, 'n_macros': n_macros, 'min_sinr': None,
              'mode': None, 'xml_filename': xml_filename, 'result_dir': result_dir, 'min_dis': min_dis, 'first_antenna_region': first_antenna_region,
              'sim_dir': sim_dir, 'num_bands': num_bands, 'repetitions': repetitions, 'slice_time': slice_time, 'p_size': p_size, 'app': app,
              'target_f': target_f, 'extra_config_name': extra_config_name, 'multi_carriers': multi_carriers, 'is_micro': is_micro, 'cmdenv_config': cmdenv_config,
              'min_time': min_time, 'micro_power': micro_power, 'net_dir': net_dir, 'project_dir': project_dir, 'num_slices': num_slices, 'per_slice': per_slice,
              'simtime_move': simtime_move,'disaster_percentage': disaster_percentage, 'allrun_solver': allrun_solver, 'interference': interference}
    
    for param in extra_dir:
        kwargs['result_dir'] += '/' + param + f'_{kwargs[param]}'
        kwargs['sim_dir'] += '/' + param + f'_{kwargs[param]}'
        kwargs['net_dir'] += '/' + param + f'_{kwargs[param]}'
        csv_dir += '/' + param + f'_{kwargs[param]}'

    Path(kwargs['result_dir']).mkdir(parents=True, exist_ok=True)
    Path(project_dir + '/' + kwargs['sim_dir']).mkdir(parents=True, exist_ok=True)
    Path(project_dir + '/' + kwargs['net_dir']).mkdir(parents=True, exist_ok=True)
    Path(project_dir + '/' + csv_dir).mkdir(parents=True, exist_ok=True)
    
    print(f'Starting computations on {cpu_count()} cores.')
    result_dir = kwargs['result_dir']
    sim_dir = kwargs['sim_dir']
    net_dir = kwargs['net_dir']
    
    failed_modes = []
    processes = []
    mode_queues = {}
    """
    if allrun_solver:
        # BUG: The option in this case is not correctly implemented, so better not allow using it.
        # It is necessary to deal with simultaneous large memory and CPU usage.   
        # TODO: REMOVE this block.
        with parallel_backend('loky', n_jobs= num_cases_simultaneously):
            result = Parallel()(delayed(process_func)(chosen_seed, size_x, size_y, size_sector, n_macros, n_ues, ues_per_slice, min_sinr, mode, xml_filename, min_dis,
                                                      first_antenna_region, project_dir, sim_dir, net_dir, num_bands, repetitions, p_size, app,
                                                      target_f, result_dir, slice_time, multi_carriers, is_micro,extra_config_name, cmdenv_config,
                                                      min_time, micro_power, num_slices, per_slice, disaster_percentage, allrun_solver)
                                                      for mode, min_sinr in cases)
                                                                                            
        for i in range(len(result)):
            if result[i] != SUCCESS:
                mode, min_sinr = cases[i]
                print('Error in case: mode {} and min SINR {}.'.format(mode, min_sinr))
                if mode not in failed_modes: failed_modes.append(mode)
    """ 

    kwargs['only_solver'] = only_solver
    kwargs['ues_per_slice'] = ues_per_slice
    kwargs['max_ues'] = max_ues
    for mode in verif_modes:
        mode_queues[mode]= Queue()

    for mode, min_sinr in cases:
        kwargs['queue'] = mode_queues[mode]
        kwargs['mode'] = mode
        kwargs['min_sinr'] = min_sinr
        processes.append(Process(target= process_func, kwargs= kwargs))
        processes[-1].start()
    
    for p in processes:
        p.join()

    for mode in verif_modes:
        while not mode_queues[mode].empty():
            errors = mode_queues[mode].get()
            print(f'Error in process_func of Mode: {mode.capitalize()}, Seed: {chosen_seed}.\n')
            if mode not in failed_modes:
                failed_modes.append(mode)
            queue.put(errors)

    if not only_solver:
        for mode in verif_modes:
            if mode not in failed_modes:
                # Semaphore to control the use of the cpu
                with semaphore_cpucount:
                    print(f'\nExporting .CSV files (Mode: {mode}, Seed: {chosen_seed}).\n')
                    get_csv(mode= mode, sim_path= project_dir + '/' + kwargs['sim_dir'], results_path= project_dir + '/' + csv_dir,
                            extra_config_name= extra_config_name, interference= interference)

    else:
        print(f'\nEnding (Seed {chosen_seed}) with only_solver True.\n')

    if failed_modes == []:
        return SUCCESS
    else:
        return

def process_func(chosen_seed: int, size_x: int, size_y: int, size_sector: int, n_macros: int, max_ues: int, ues_per_slice: list, min_sinr: int,
                 mode: str, xml_filename: str, min_dis: int, first_antenna_region: int, project_dir: str,
                 sim_dir: str, net_dir: str, num_bands: List[int], repetitions: int, p_size: int, app: str,
                 target_f: float, result_dir: str = '.', slice_time: int = 1, multi_carriers: bool= False,
                 is_micro: bool= True,extra_config_name: str = '', cmdenv_config: bool = True,
                 min_time: int = 2, micro_power: int= 30, num_slices: int= 10, simtime_move: int = 1000, per_slice: bool = True,
                 disaster_percentage: int = 0, allrun_solver: bool = False, queue: Queue = None,
                 only_solver: bool = False, interference: bool = False):
    """This function defines the behaviour of each process, running both the solver and the simulation of a single scenario."""
    if not allrun_solver:
        print(f'Started process process_func {current_process().name} {current_process().pid}. (Seed: {chosen_seed}, Mode: {mode}, Min_sinr: {min_sinr})')
        semaphore_cpucount.acquire()

    try:
        print(f"\nRunning case {mode} {min_sinr} dB, seed {chosen_seed}, micro power {micro_power}, disaster percentage {disaster_percentage}.\n")
        
        check_mode(mode= mode)

        file_name = genf.gen_file_name(mode= mode, min_sinr= min_sinr)
        sim_path = project_dir + '/' + sim_dir

        # Verifying if solver is already done
        done = compare_last_line(genf.gen_solver_result_filename(result_dir, mode, min_sinr), '--- Done ---\n')

        # Initiating scenario with no user equipment (UE).
        scen = geo.MapChess(size_y = size_y, size_x = size_x, size_sector = size_sector, carrier_frequency= 0.7, chosen_seed= chosen_seed,
                            scenario= "URBAN_MICROCELL" if is_micro else "URBAN_MACROCELL", enb_tx_power= micro_power if is_micro else 46,
                            h_enbs= 18, gain_ue= -1, enb_noise_figure= 9, simtime_move = simtime_move, num_slices = num_slices,
                            slice_time = slice_time)
        scen.placeUEs(type= "Random", n_macros= n_macros, n_ues_macro= 0)

        if done:
            print(f'Solver {file_name} already computed. (Seed: {chosen_seed})')
        
        else:
            # Running solver
            gen_ilp_info(scen = scen, ues_per_slice = ues_per_slice, xml_filename= xml_filename, min_sinr= min_sinr, result_dir= result_dir, mode= mode, min_dis= min_dis,
                        first_antenna_region= first_antenna_region, min_time= min_time, disaster_percentage= disaster_percentage)

        if not only_solver:
            # Generating config and network files
            print("Generating configuration files - Min Snr: {} - {} (Seed: {})".format(min_sinr, mode.capitalize(), chosen_seed))
            
            ini_path_sliced = sim_path + '/' + f'{file_name}{"_inter" if interference else ""}.ini'
            network_name = f"ILP{mode.capitalize()}Net{str(min_sinr)}"

            if per_slice:
                config_name_sliced_list, num_enbs_time = ilp_sliced_ini_per_slice(scen, ini_path_sliced, n_macros= n_macros, ues_per_slice = ues_per_slice, max_ues = max_ues, repetitions= repetitions,
                                                                                min_sinr= min_sinr, num_bands= num_bands, multi_carriers= multi_carriers, is_micro= is_micro, p_size= p_size, app= app,
                                                                                extra_config_name= extra_config_name, target_f= target_f, result_dir= result_dir, mode = mode, network_name= network_name,
                                                                                cmdenv_config= cmdenv_config, net_dir= net_dir, xml_filename= xml_filename, interference= interference)

                if config_name_sliced_list == None and num_enbs_time == None:
                    #There was a not feasible solution
                    raise errors.SolutionNotFeasible("The case seed {}, mode {}, min sinr {} dB, {}%% disaster is not feasible.".format(chosen_seed, mode, min_sinr, disaster_percentage))
                    #print("The case seed {}, mode {}, min sinr {} dB, {}%% disaster is not feasible.".format(chosen_seed, mode, min_sinr, disaster_percentage))
                    #return None

                for slice in range(len(num_enbs_time)):
                    network_name = f"ILP{mode.capitalize()}Net{str(min_sinr)}Slice{str(slice)}"
                    ilp_ned(network = network_name, n_enbs= num_enbs_time[slice], size_x= size_x, size_y= size_y, net_dir= net_dir, project_dir= project_dir)
            
            else:
                config_name_sliced, enbs_sliced_num = ilp_sliced_ini(scen, ini_path_sliced, n_macros= n_macros, ues_per_slice = ues_per_slice , max_ues = max_ues, repetitions= repetitions,
                                                                min_sinr= min_sinr, num_bands= num_bands, multi_carriers= multi_carriers, is_micro= is_micro, p_size= p_size, app= app, extra_config_name= extra_config_name,
                                                                target_f= target_f, result_dir= result_dir, mode = mode, network_name= network_name, cmdenv_config= cmdenv_config,
                                                                net_dir= net_dir, xml_filename= xml_filename, interference= interference)

                ilp_ned(network = network_name, n_enbs= enbs_sliced_num, size_x= size_x, size_y= size_y, net_dir= net_dir, project_dir= project_dir)

            if interference:
                extra_out_name = 'inter'
            else:
                extra_out_name = ''
            #Running the simulation
            run_numbers = get_missing_simulations(mode= mode, num_bands= num_bands, repetitions= repetitions, sim_path= sim_path, min_sinr= min_sinr,
                                                  num_slices= num_slices, multi_carriers= multi_carriers, extra_config_name= extra_config_name,
                                                  extra_out_name=extra_out_name)          
            if run_numbers == []:
                print('All simulations are already computed. Min Snr: {} - {} (Seed: {})'.format(min_sinr, mode.capitalize(), chosen_seed))
            else:
                print("Executing Simulations - Min Snr: {} - {} (Seed: {})".format(min_sinr, mode.capitalize(), chosen_seed))
                if per_slice:
                    run_simulation_per_slice(ini_path= ini_path_sliced, repetitions= repetitions, config_name_list= config_name_sliced_list, cpu_num= cpu_count() if allrun_solver else 1, run_numbers= run_numbers)
                else:
                    run_simulation_all_slices(ini_path= ini_path_sliced, config_name= config_name_sliced, cpu_num= cpu_count() if allrun_solver else 1, run_numbers= run_numbers)

    except Exception as e:
        if queue is not None:
            queue.put(ErrorPackage(exc_info= "".join(traceback.format_exception(*sys.exc_info())), pname= current_process().name, pid= current_process().pid, **{'seed': chosen_seed, 'mode': mode, 'min_sinr': min_sinr}))
        return
    
    finally:
        if not allrun_solver:
            semaphore_cpucount.release()

    return SUCCESS

def get_csv(mode: str, sim_path: str, results_path: str, extra_config_name: str = '', interference: bool = False):
    """This function call a scavetool command to create the necessary .csv files"""

    check_mode(mode= mode)

    csv_path, sca_vec_dir = genf.gen_csv_path(mode, sim_path, results_path, extra_config_name, interference)

    print(f'Making {csv_path}.')

    if not interference:
        code = subprocess.run(f'scavetool x -o {csv_path} -f "module(**.cellularNic.channelModel[*]) OR module(**.app[*])" {sca_vec_dir}/*-*-.sca {sca_vec_dir}/*-*-.vec', shell= True)
    else:
        code = subprocess.run(f'scavetool x -o {csv_path} -f "module(**.cellularNic.channelModel[*]) OR module(**.app[*])" {sca_vec_dir}/*-*-inter.sca {sca_vec_dir}/*-*-inter.vec', shell= True)

    code.check_returncode()

def compare_last_line(filename: str, line: str) -> bool:
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

def get_missing_simulations(mode: str, num_bands: List[int], repetitions: int, sim_path: str, min_sinr: int, num_slices: int,
                            multi_carriers: bool, extra_config_name: str, extra_out_name: str):
    """This function returns the simulation runs that were not executed yet"""

    sim_resultdir = f'{sim_path}/results'
    counter = 0
    missing = []
    config_pattern = genf.gen_sliced_config_pattern(min_sinr= min_sinr, mode= mode, multi_carriers= multi_carriers, extra_config_name= extra_config_name)
    for band in num_bands:
        for slice in range(num_slices):
            for repetition in range(repetitions):
                filename = f'{sim_resultdir}/{config_pattern}-cmdout/{min_sinr}-{band}-{repetition}-{slice}{("-"+extra_out_name) if extra_out_name != "" else "-"}.out'
                done = compare_last_line(filename, '[INFO]\tClear all sockets\n')
                if not done:
                    missing.append(counter)

                counter += 1

    return missing

if __name__ == "__main__": 
    main()
