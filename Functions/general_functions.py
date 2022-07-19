from cProfile import label
from pathlib import Path
from typing import List
import numpy as np
import geometry as geo
import matplotlib.pyplot as plt

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

    return np.unique(verif_modes).tolist()

def gen_csv_path(mode: str, sim_path: str, results_path: str, extra_config_name: str = ''):
    
    result_dir = sim_path + '/results'

    if extra_config_name != '':
        extra_config_name = '_' + extra_config_name 
    sca_vec_dir = result_dir + f'/ilp_{mode}_sliced_*' + extra_config_name
    csv_path = results_path + f'/ilp_{mode}_sliced' + extra_config_name + '.csv'

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
    
    results_list = 10*[None]
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
                results[data[0]][data[2]] = data[1]
                enbs_time[data[0]].append(data[1])
                enbs.append(data[1])
                enbs = np.unique(enbs).tolist()

    #Get the number of eNBs at each slice
    for t in range(max_time):
        enbs_time[t] = np.unique(enbs_time[t]).size

    return results, enbs, enbs_time

def get_ues_connections(result, ues_coords, antennas_regions: List[int], size_sector, size_x, size_y):
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
    for ue in ues_coords:
        connections.append([])
        for s in range(len(ue)):
            region = geo.coord2Region(ue[s], size_sector, size_x, size_y)
            #Assume-se que a regiao do UE é servida por alguma das antenas
            connections[-1].append(antennas_regions.index(result[s][region])+1)

    return connections

def get_ues_connections_per_slice(result, ues_coords, antennas_regions: List[int], size_sector, size_x, size_y, slice_):
    """This function interpretates the result parsed from the solver in to the elements connections.

    Args:
        result: Dict containing the parsed solution (serving cell for ue region key) from the solver for a specific time (slice_).
        ues_coords: 2D Matrix (n X t) with the coordinates of each UE (n) at each time of simulation (t).
        antennas_regions: List[int] containing the sectors where eNBs are located
        size_sector: sides size of square sectors in meters
        size_x: x dimension size of considered region in meters
        size_y: y dimension size of considered region in meters
        slice_: specific time considered

    Return:
        A Array of size n with the serving cell number for each UE (n).
    """
    connections = []
    
    for ue in ues_coords:
        region = geo.coord2Region(ue[slice_], size_sector, size_x, size_y)
        #Assume-se que a regiao do UE é servida por alguma das antenas
        connections.append(antennas_regions.index(result[region])+1)

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

def get_regions_of_service(antennas_regions: List[int], metric_map_mn: List[List[int]], minimization: bool= False):
    """Get the regions which each antenna serves.

    Args:
        antennas_regions: List with the antennas regions in the map
        metric_map_mn: Matrix m x n representing a list of the metric map for each antenna position. m must be equal to n.
        minimization: Indicates if a lower (minimization) or a higher (maximization) value is better.

    Returns:
        Dictionary with the antennas regions as keys and a list with the serving regions as values.
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
    
    regions_of_service = {}

    for key in metrics_of_service:
        if minimization:
            regions_of_service[key] = np.ravel(np.argwhere(metrics_of_service[key] < np.inf))
        else:
            regions_of_service[key] = np.ravel(np.argwhere(metrics_of_service[key] > -np.inf))

    return regions_of_service