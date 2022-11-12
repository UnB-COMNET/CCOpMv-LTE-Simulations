from pathlib import Path
from typing import List
from matplotlib import use
import numpy as np
import geometry as geo
import matplotlib.pyplot as plt
from scipy.stats import poisson
from random import choice, randint, seed, random

MODES_NEW_NAMES = {
    'varying': 'VID',
    'single': 'TID',
    'fixed': 'AID',
    'ga': 'AGD'
}

# TODO: Use OmNET absolute path.
def get_frameworks_path():
    user = 'juliano'
    if user == 'juliano':
        return r'../../../OmNET2'
    else:
        return r'../..'

def gen_file_name(mode: str, min_sinr: int):
    return f'ilp_{mode}_sliced_{str(min_sinr)}'

#Result_dir must have a 'logs' subdir
def gen_log_file_name(result_dir: str, file_name: str):
    log_dir = f"{result_dir}/logs"
    Path(log_dir).mkdir(parents=False, exist_ok=True)
    return f"{log_dir}/{file_name}.log"

def gen_sliced_config_pattern(min_sinr: int, mode: str, multi_carriers: bool, extra_config_name: str):
    return 'ilp_{}_sliced_{}'.format(mode, min_sinr) + ('_carriers' if multi_carriers else '') + ('_' + extra_config_name if extra_config_name != '' else '')

def gen_solver_result_filename(result_dir: str, mode: str, min_sinr: int):
    return result_dir + f"/result_{mode}_"+ str(min_sinr)+".txt"

def gen_movement_filename(config_name: str, seed: int, snapshot: bool= True):
    if snapshot:
        return config_name + f'-{seed}.sna'
    else:
        return config_name + f'-{seed}.ini'

def verify_modes(modes: List[str]):
    verif_modes = []

    for mode in modes:
        if mode.lower() == 'varying':
            verif_modes.append('varying')
        elif mode.lower() == 'fixed' or mode.lower() == 'aid':
            verif_modes.append('fixed')
        elif mode.lower() == 'single' or mode.lower() == 'tid':
            verif_modes.append('single')
        elif mode.lower() == 'ga':
            verif_modes.append('ga')

    return np.unique(verif_modes).tolist()

def gen_csv_path(mode: str, sim_path: str, results_path: str, extra_config_name: str = '', interference: bool = False):
    
    result_dir = sim_path + '/results'

    if extra_config_name != '':
        extra_config_name = '_' + extra_config_name 
    sca_vec_dir = result_dir + f'/ilp_{mode}_sliced_*' + extra_config_name
    csv_path = results_path + f'/ilp_{mode}_sliced' + extra_config_name + ('_inter' if interference else '') + '.csv'

    return csv_path, sca_vec_dir

def parse_results_per_slice(filename: str, max_time: int):
    """This function parses the UEs and eNBs necessary information from the solver (ccop_mv_MILP) resulted solution.

    Args:
        filename: string representing the name of the txt file with the solution
        max_time: Max_Time parameter used in the solver

    Return:
        Three structures. The first one is a list of dict (results[t]{n: m}) where t is the simulation time, n is the sector of a UE at that time and m is the sector of its serving cell.
        The second one is a list of lists (list[t][n]) where t is the time of the simulation and n is the number of the eNB, containing the sector where each eNB is located at that time (List[List[int]]).
        The third is a list with the number of eNBs deployed in each slice
    """

    results = []
    enbs = []
    enbs_time = []
    enbs_byslice = []

    for i in range(max_time):
        results.append({})
        enbs_time.append([])
        enbs_byslice.append([])

    try:
        with open(filename, "r") as f:
            for line in f:
                if not line.startswith('---'): 
                    data = [int(x) for x in line.split()]   # data: [t, m, n]
                    if data[2] >= 0:
                        results[data[0]][data[2]] = data[1]
                    enbs_time[data[0]].append(data[1])
                    enbs.append(data[1])
                    enbs = np.unique(enbs).tolist()
    except FileNotFoundError:
        print("File {} not found.".format(filename))
        return None, None, None

    #Get the number of eNBs at each slice
    
    for t in range(max_time):
        enbs_byslice[t] = np.unique(enbs_time[t]).tolist()
        enbs_time[t] = np.unique(enbs_time[t]).size
    
    results_list = max_time*[None]
    for i in range(len(results)):
        results_list[i] = results[i]

    return results_list, enbs_byslice, enbs_time

def parse_results(filename: str, max_time: int):
    """This function parses the UEs and eNBs necessary information from the solver (ccop_mv_MILP) resulted solution.

    Args:
        filename: string representing the name of the txt file with the solution
        max_time: Max_Time parameter used in the solver

    Return:
        Three structures. The first one is a list of dict (results[t]{n: m}) where t is the simulation time, n is the sector of a UE at that time and m is the sector of its serving cell.
        The second one is a list with the sectors where the eNBs were located (List[int]).
        The third is a list with the number of eNBs deployed in each slice
    """

    results = []
    enbs = []
    enbs_time = []
    for i in range(max_time):
        results.append({})
        enbs_time.append([])

    with open(filename, "r") as f:
        for line in f:
            if not line.startswith('---'): 
                data = [int(x) for x in line.split()]   # data: [t, m, n]
                if data[2] >= 0:
                    results[data[0]][data[2]] = data[1]
                enbs_time[data[0]].append(data[1])
                enbs.append(data[1])
                enbs = np.unique(enbs).tolist()

    #Get the number of eNBs at each slice
    for t in range(max_time):
        enbs_time[t] = np.unique(enbs_time[t]).size

    return results, enbs, enbs_time

def get_ues_connections(result, ues_coords, ues_per_slice:list, antennas_regions: List[int], size_sector, size_x, size_y):
    """This function interpretates the result parsed from the solver in to the elements connections.

    Args:
        result: List[Dict] containing the parsed solution from the solver
        ues_coords: 2D Matrix (n X t) with the coordinates of each UE (n) at each time of simulation (t).
        antennas_regions: List[int] containing the sectors where eNBs are located
        size_sector: sides size of square sectors in meters
        size_x: x dimension size of considered region in meters
        size_y: y dimension size of considered region in meters

    Return:
        A 2D Matrix (n X t) with the serving cell number for each UE (n) at each time (t).
    """
    connections = []

    ue_target = 0
    for ue in ues_coords:
        connections.append([])
        for s in range(len(ue)):        
            region = geo.coord2Region(ue[s], size_sector, size_x, size_y)
            
            #for ue_find in ues_per_slice[s]:
            #    if ue_find == ue_target:
            #        ue_find = ue_target
            #        break

            if ue_target in ues_per_slice[s]:
                if region in result[s]:
                    connections[-1].append(antennas_regions.index(result[s][region])+1)
                else:
                    connections[-1].append(0)
            else:
                connections[-1].append(1)   # unreal connection; 1 is default
        
        ue_target += 1

    return connections

def get_ues_connections_per_slice(result, ues_coords, ues_list: List[int], antennas_regions: List[int], size_sector, size_x, size_y, slice_):
    """This function interpretates the result parsed from the solver in to the elements connections.

    Args:
        result: Dict containing the parsed solution (serving cell for ue region key) from the solver for a specific time (slice_).
        ues_coords: 2D Matrix (n X t) with the coordinates of each UE (n) at each time of simulation (t).
        ues_list: List[int] containig the index of users who are present in the respective slice.
        antennas_regions: List[int] containing the sectors where eNBs are located.
        size_sector: sides size of square sectors in meters.
        size_x: x dimension size of considered region in meters.
        size_y: y dimension size of considered region in meters.
        slice_: specific time considered.

    Return:
        A Array of size n with the serving cell number for each UE (n).
    """
    connections = []
    
    ue_target = 0
    for ue in ues_coords:
        region = geo.coord2Region(ue[slice_], size_sector, size_x, size_y)

        #for ue_find in ues_list:
        #    if ue_find == ue_target:
        #        ue_find = ue_target
        #        break
        
        if ue_target in ues_list: #Se for um UE ativo
            if region in result: #Se sua região estiver nos resultados
                connections.append(antennas_regions.index(result[region])+1)
            else:
                connections.append(0)
        else:
            connections.append(1)   # unreal connection; 1 is default

        ue_target += 1

    return connections

def plot_scenario(scen: geo.MapChess, title: str):

    antennas_coords = scen.getAntennasPositionList()
    ues_coords = scen.getUEsPositionList()
    plt.plot([c.x for c in antennas_coords], [c.y for c in antennas_coords], linestyle='', marker='*', color='red', markersize= 5, label= 'antenna')
    plt.plot([c.x for c in ues_coords], [c.y for c in ues_coords], linestyle='', marker='.', color='blue', markersize= 2, label= 'ue')
    plt.gca().invert_yaxis()
    plt.title(title)
    plt.legend(loc="upper left")
    plt.xlim(0, 4000)
    plt.ylim(0, 4000)
    plt.show()
    print("Plot")

def get_map_of_service(antennas_regions: List[int], metric_map_mn: List[List[int]], minimization: bool= False):
    """Get a map with the antennas that would serve each region.

    Args:
        antennas_regions: List with the antennas regions in the map
        metric_map_mn: Matrix m x n representing a list of the metric map for each antenna position. m must be equal to n.
        minimization: Indicates if a lower (minimization) or a higher (maximization) value is better.

    Returns:
        List with the antennas region that serves each index/region.
    """
    metrics_of_service = {}

    #Every possible pair of antennas to compare
    antennas_pairs = []
    for i in range(len(antennas_regions)):
        #Initializes metrics_of_service for each antenna
        metrics_of_service[str(antennas_regions[i])] = np.array(metric_map_mn[antennas_regions[i]])
        for j in range(i+1, len(antennas_regions)):
            antennas_pairs.append((antennas_regions[i], antennas_regions[j]))

    for m, n in antennas_pairs:
        #Compare the metrics of service between the pair of antennas
        comp_array = metrics_of_service[str(m)] > metrics_of_service[str(n)]
        if minimization:
            comp_array = ~comp_array #Inverts the comparison to obey that a big value is better

        #New values of the metric of service to discard already rulled out regions
        metrics_of_service[str(m)][~comp_array] = np.inf if minimization else -np.inf #Inverts comp_array because we want the values of m that lost to n
        metrics_of_service[str(n)][comp_array] = np.inf if minimization else -np.inf #Changing the values of n that lose to those of m
    
    map_of_service = [ -1 for _ in range(len(metric_map_mn[-1]))]

    for key in metrics_of_service:
        if minimization:
            served_sectors = np.ravel(np.argwhere(metrics_of_service[key] < np.inf))
        else:
            served_sectors = np.ravel(np.argwhere(metrics_of_service[key] > -np.inf))
        for i in served_sectors:
                map_of_service[i] = key

    if -1 in map_of_service:
        raise(ValueError('One region is not served in Map Of Service with value -1.'))

    return map_of_service

def gen_first_antenna_region(chosen_seed: int, n_sectors: int):

    seed(chosen_seed)

    for _ in range(n_sectors):
        random()

    first_antenna_region = randint(0, n_sectors - 1)

    return first_antenna_region

def gen_users_t_m(seed, lambda_poisson, num_slices):
    lambda_ = lambda_poisson
    np.random.seed(seed)
    while(True):
        r = poisson.rvs(lambda_, size=num_slices)
        user_t_m = num_slices*[0]
        for i in range(len(user_t_m)):    
            if i < int(num_slices/2):
                # to sum
                if i == 0:
                    user_t_m[i] = user_t_m[i] + r[i]        
                else:
                    user_t_m[i] = user_t_m[i-1] + r[i]        

            else:
                # to subtract
                user_t_m[i] = user_t_m[i-1] - r[i]

        is_valid = True
        for i in range(len(user_t_m)):
            if user_t_m[i] <= 0:
                is_valid = False
        
        if is_valid:   
            break
    
    return user_t_m

def gen_ue_per_slice(chosen_seed, user_t_m, num_slices):
    max_user_t_m = max(user_t_m)
    ue_list = max_user_t_m*[0]
    
    for i in range(len(ue_list)):
        ue_list[i] = i

    bck = ue_list.copy()
    ue_slice = num_slices*[[]]
    seed(chosen_seed)
    for i in range(len(user_t_m)):
        if i == 0:
            ue_choiced = []
            for j in range(user_t_m[0]):
                if ue_list != []:
                    ue = choice(ue_list)
                    ue_choiced.append(ue)
                    ue_list.pop(ue_list.index(ue))
            
            ue_slice[i] = ue_choiced

        elif user_t_m[i] > user_t_m[i-1]:
            # additive
            ue_choiced = []
            for j in range(user_t_m[i] - user_t_m[i-1]):
                if ue_list != []:
                    ue = choice(ue_list)
                    ue_choiced.append(ue)
                    ue_list.pop(ue_list.index(ue))

            ue_slice[i] = ue_choiced
        else:
            pass
    
    if ue_list != []:
        print("ERROR in gen_ue_per_slice()")
        return None
    
    for i in range(len(ue_slice)):
        # cumulative adding
        if ue_slice[i] != [] and i > 0:
            ue_slice[i] = ue_slice[i-1] + ue_slice[i]
            ue_slice[i]

        elif ue_slice[i] == []:
            ue_choiced = []
            tmp_ue_slice = ue_slice[i-1].copy()
            for j in range(user_t_m[i-1] - user_t_m[i]):
                ue = choice(tmp_ue_slice)
                tmp_ue_slice.pop(tmp_ue_slice.index(ue))
                ue_list.append(ue)

            ue_slice[i] = tmp_ue_slice

    # Verifying
    for i in range(len(ue_slice)):
        if len(ue_slice[i]) != user_t_m[i]:
            print("ERROR 2 in gen_ue_per_slice()")
            return None

    # contagem de duração para cada UE
    '''for i in range(max_user_t_m):
        c = 0
        first = None
        last = None
        for j in range(len(ue_slice)):
            for k in ue_slice[j]:            
                if k == i:
                    c += 1
                    if first == None:
                        first = j
        print("UE {} esta ativo por {} slices, entrou no slice {}".format(i, c, first))
        if c == 0: break
    '''
    return ue_slice
