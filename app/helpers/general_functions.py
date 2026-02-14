from pathlib import Path
from statistics import mean
from typing import List, Union
import numpy as np
import app.core.geometry as geo
import matplotlib.pyplot as plt
from scipy.stats import poisson
from random import choice, randint, seed

MODES_NEW_NAMES = {
    'varying': 'VID',# Varying ILP Deployment
    'single': 'TID',# Traditional ILP Deployment
    'fixed': 'AID',# Additive ILP Deployment
    'pgwo1': 'PGWO-1', #Progressive GWO
    'pgwo2': 'PGWO',
    'pgwo3': 'PGWO-3',
    'ga': 'PGD'# Predicative GA Deployment
}


class SimulationPaths:
    """Groups path and filename generation for simulations, results, and configs."""

    # TODO: Use OmNET absolute path.
    def get_frameworks_path(self) -> str:
        user = 'juliano'
        if user == 'juliano':
            return r'../../../OmNET2'
        return r'../..'

    def gen_file_name(self, mode: str, min_sinr: int) -> str:
        return f'ilp_{mode}_sliced_{min_sinr}'

    def gen_log_file_name(self, result_dir: str, file_name: str) -> str:
        log_dir = f"{result_dir}/logs"
        Path(log_dir).mkdir(parents=False, exist_ok=True)
        return f"{log_dir}/{file_name}.log"

    def gen_sliced_config_pattern(self, min_sinr: int, mode: str, multi_carriers: bool, extra_config_name: str) -> str:
        return 'ilp_{}_sliced_{}'.format(mode, min_sinr) + ('_carriers' if multi_carriers else '') + ('_' + extra_config_name if extra_config_name != '' else '')

    def gen_solver_result_filename(self, result_dir: str, mode: str, min_sinr: int) -> str:
        return result_dir + f"/result_{mode}_" + str(min_sinr) + ".txt"

    def gen_movement_filename(self, config_name: str, seed_val: int, snapshot: bool = True) -> str:
        if snapshot:
            return config_name + f'-{seed_val}.sna'
        return config_name + f'-{seed_val}.ini'

    def gen_csv_path(self, mode: str, sim_path: str, results_path: str, extra_config_name: str = '', interference: bool = False):
        result_dir = sim_path + '/results'
        if extra_config_name != '':
            extra_config_name = '_' + extra_config_name
        sca_vec_dir = result_dir + f'/ilp_{mode}_sliced_*' + extra_config_name
        csv_path = results_path + f'/ilp_{mode}_sliced' + extra_config_name + ('_inter' if interference else '') + '.csv'
        return csv_path, sca_vec_dir


class UserTrafficGenerator:
    """Generates user counts and UE-per-slice assignments for traffic/mobility."""

    def verify_modes(self, modes: List[str]) -> List[str]:
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
            elif mode.lower() == 'pgwo1':
                verif_modes.append('pgwo1')
            elif mode.lower() == 'pgwo2':
                verif_modes.append('pgwo2')
            elif mode.lower() == 'pgwo3':
                verif_modes.append('pgwo3')
        return np.unique(verif_modes).tolist()

    def gen_users_t_m(self, seed_val: int, lambda_poisson: int, num_slices: int) -> List[int]:
        lambda_ = lambda_poisson
        np.random.seed(seed_val)
        while True:
            r = poisson.rvs(lambda_, size=num_slices)
            user_t_m = num_slices * [0]
            for i in range(len(user_t_m)):
                if i < int(num_slices / 2):
                    if i == 0:
                        user_t_m[i] = user_t_m[i] + r[i]
                    else:
                        user_t_m[i] = user_t_m[i - 1] + r[i]
                else:
                    user_t_m[i] = user_t_m[i - 1] - r[i]
            if all(user_t_m[i] > 0 for i in range(len(user_t_m))):
                break
        return user_t_m

    def gen_ue_per_slice(self, chosen_seed: int, user_t_m: List[int], num_slices: int):
        max_user_t_m = max(user_t_m)
        ue_list = list(range(max_user_t_m))
        ue_slice = num_slices * [[]]
        seed(chosen_seed)
        for i in range(len(user_t_m)):
            if i == 0:
                ue_choiced = []
                for j in range(user_t_m[0]):
                    if ue_list:
                        ue = choice(ue_list)
                        ue_choiced.append(ue)
                        ue_list.pop(ue_list.index(ue))
                ue_slice[i] = ue_choiced
            elif user_t_m[i] > user_t_m[i - 1]:
                ue_choiced = []
                for j in range(user_t_m[i] - user_t_m[i - 1]):
                    if ue_list:
                        ue = choice(ue_list)
                        ue_choiced.append(ue)
                        ue_list.pop(ue_list.index(ue))
                ue_slice[i] = ue_choiced
            else:
                pass
        if ue_list:
            print("ERROR in gen_ue_per_slice()")
            return None
        for i in range(len(ue_slice)):
            if ue_slice[i] and i > 0:
                ue_slice[i] = ue_slice[i - 1] + ue_slice[i]
            elif not ue_slice[i]:
                tmp_ue_slice = ue_slice[i - 1].copy()
                for j in range(user_t_m[i - 1] - user_t_m[i]):
                    ue = choice(tmp_ue_slice)
                    tmp_ue_slice.pop(tmp_ue_slice.index(ue))
                    ue_list.append(ue)
                ue_slice[i] = tmp_ue_slice
        for i in range(len(ue_slice)):
            if len(ue_slice[i]) != user_t_m[i]:
                print("ERROR 2 in gen_ue_per_slice()")
                return None
        return ue_slice

    def gen_first_antenna_region(self, chosen_seed: int, n_sectors: int) -> int:
        seed(chosen_seed)
        return randint(0, n_sectors - 1)


_paths = SimulationPaths()
_user_traffic = UserTrafficGenerator()


def get_frameworks_path():
    return _paths.get_frameworks_path()

def gen_file_name(mode: str, min_sinr: int):
    return _paths.gen_file_name(mode, min_sinr)

def gen_log_file_name(result_dir: str, file_name: str):
    return _paths.gen_log_file_name(result_dir, file_name)

def gen_sliced_config_pattern(min_sinr: int, mode: str, multi_carriers: bool, extra_config_name: str):
    return _paths.gen_sliced_config_pattern(min_sinr, mode, multi_carriers, extra_config_name)

def gen_solver_result_filename(result_dir: str, mode: str, min_sinr: int):
    return _paths.gen_solver_result_filename(result_dir, mode, min_sinr)

def gen_movement_filename(config_name: str, seed_val: int, snapshot: bool = True):
    return _paths.gen_movement_filename(config_name, seed_val, snapshot)

def verify_modes(modes: List[str]):
    return _user_traffic.verify_modes(modes)

def gen_csv_path(mode: str, sim_path: str, results_path: str, extra_config_name: str = '', interference: bool = False):
    return _paths.gen_csv_path(mode, sim_path, results_path, extra_config_name, interference)

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

def print_map_mn(scen: geo.MapChess, map_name: str, values: List[List[Union[int,float]]]):
    print(map_name)
    num_sector = int(scen.size_y/scen.size_sector)
    for i in range(num_sector):
        print(values[i*num_sector:num_sector*(i+1)])   

def get_dict_of_connections(antennas_regions, users_regions, users_m, snr_map_mn, min_sinr_w, max_users_per_antenna_m,
                            ignore_unconnected: bool = False, return_map_of_service: bool = False, verbose = False):
    """
        Retorna um dicionário de conexões entre regiões de antenas e regiões de usuários.

        Args:
            antennas_regions (list): Lista das regiões de antenas.
            users_regions (list): Lista das regiões de usuários.
            users_m (dict): Dicionário que mapeia as regiões de usuários para o número de usuários em cada região.
            snr_map_mn (dict): Dicionário que mapeia as regiões de antenas para as regiões de usuários para valores de SNR.
            min_sinr_w (float): Valor mínimo de SINR (Relação Sinal-Ruído) para uma conexão válida.
            max_users_per_antenna_m (dict): Dicionário que mapeia as regiões de antenas para o número máximo de usuários que cada antena pode atender.
            ignore_unconnected (bool, optional): Indica se as regiões de usuários não conectadas devem ser ignoradas. O padrão é False.
            return_map_of_service (bool, optional): Indica se o mapa de serviço deve ser retornado juntamente com o dicionário de conexões. O padrão é False.

        Returns:
            dict: Dicionário de conexões entre regiões de antenas e regiões de usuários.
            dict or None: Mapa de serviço que indica quais regiões de usuários são atendidas por quais regiões de antenas (retornado apenas se return_map_of_service for True).

    """
    #if (np.array_equal(antennas_regions, np.array([7,21,54,59,70,76,85])) and 
    #np.array_equal(users_regions, np.array([0,1,4,5,7,9,12,13,14,15,16,17,18,19,21,23,25,26,27,28,29,30,31,32,
    #33,34,35,36,37,38,39,41,42,43,44,45,46,48,49,51,52,53,54,55,59,61,62,63,
    #64,65,66,67,68,69,70,71,72,73,74,77,78,81,83,84,86,87,88,89,90,91,92,93,
    #94,99]))):
    antennas_regions = np.sort(antennas_regions)                        # Just to avoid that the order of the elements affect the resul
    """if (np.array_equal(antennas_regions, np.array([7,21,54,59,70,76,85]))):
        print(antennas_regions, "In get_connect verbose is True")
        verbose = True"""
    connect_dict = {}
    antennas_regions_list = [geo.Region(region,0,max_users_per_antenna_m[region],[]) for region in antennas_regions]
    isSaturated = True
    keptMapOfService = False
    if verbose: print("In get_connect: antennas_regions", antennas_regions)
    if verbose: print("In get_connect: users_regions", users_regions)
    while len(users_regions):
        # Main loop to handle all regions with users

        if isSaturated:
            # Rebuilds the map of service considering the new set of antennas available for connection
            # NOTE: It is always executed on the first execution of the main loop. 
            # Afterwards, only if some antenna reaches the maximum number of users.
            _map_of_service = get_map_of_service([region.index for region in antennas_regions_list], snr_map_mn, min_sinr_w,
                                                 minimization=False, threshold=True, full=True, old=False)

            # Updates the list of regions with users based on the current state of the user_region variable
            users_regions_list: list[geo.Region] = [geo.Region(index=region,
                                                               num_users=users_m[region],
                                                               max_users=None,
                                                               serving_antennas=_map_of_service[region]) for region in users_regions]
            # Sorts the regions in ascending order of number of candidate antennas to serve them, i.e., the regions with
            # less possibility of serving antennas receive priority
            users_regions_list.sort(key=lambda x: x.num_serving_antennas, reverse=False)        

            # Preserves the first version of the service map built with the initial set of antennas
            # NOTE: It is used to return the map of service and protect it from overwriting
            if not keptMapOfService and return_map_of_service:
                map_of_service = _map_of_service
                keptMapOfService = True
        
        isSaturated = False

        for usr_region in users_regions_list:
            # Analyzes each region with user to build connection dict
            # There are 4 possible cases:
            # 1 - No antenna serves the sector
            # 2 - More than one antenna can serve the sector
            # 3 - Exactly one antenna can serve the sector
            # 4 - More than one antenna can serve the sector

            if usr_region.serving_antennas == []:
                # The analyzed region cannot be served by any antenna...
                if not ignore_unconnected:
                    if verbose: print("nenhuma antena serve ao ", usr_region)
                    # ..., so the evaluated solution does not serve all users
                    if return_map_of_service:
                        return None, None
                    else:
                        return None
                """else:
                    # ..., but this will be ignored.
                    # TODO: verificar se esse trecho realmente é necessário no caso Single
                    users_regions_list = [x for x in users_regions_list             # Rebuilds the list of regions without the current region 
                                            if x.index != usr_region.index]
                    continue"""
            
            if str(usr_region.index) in usr_region.serving_antennas:
                # The user is in a sector with an antenna, so he must be served by the antenna in this same sector
                # NOTE: This case must be analyzed first because it is directly linked to one of the constraints of the problem

                # Find in antennas_regions_list the Region in which the index corresponds the index of the user region 
                ant_region: geo.Region = list(filter(lambda x: x.index == usr_region.index, antennas_regions_list))[0]    
                
                # Updates the number of users connected to antenna in the Region ant_region
                ant_region.num_users += usr_region.num_users
                
                if ant_region.num_users > ant_region.max_users:
                    if verbose: print("Antena no setor com usuario excedeu seu limite de usuarios ", usr_region)
                    # Exceeded the maximum number of users when it is required to be served by the antenna in its own sector
                    if return_map_of_service:
                        return None, None
                    else:
                        return None

                # Updates the connections dictionary, the list of Regions with users without the current region and 
                # the user regions without the current region
                connect_dict[usr_region.index] = usr_region.index
                """users_regions_list = [x for x in users_regions_list if x.index != usr_region.index]"""
                users_regions = users_regions[~np.isin(users_regions, usr_region.index)]

                if ant_region.num_users == ant_region.max_users:
                    # Reach the maximum number of users for that region
                    antennas_regions_list = [x for x in antennas_regions_list         # Update list of Region by removing the saturated antenna
                                               if x.index != ant_region.index]       
                    isSaturated = True
                    break

                continue
            
            if usr_region.num_serving_antennas == 1:
                # The analyzed region can only be served by a specific antenna             
                
                # Find in antennas_regions_list the Region in which the index corresponds to that of the serving antenna
                ant_region = list(filter(lambda x: x.index == int(usr_region.serving_antennas[0]), antennas_regions_list))[0]
                
                # Updates the number of users connected to antenna in the Region ant_region
                ant_region.num_users += usr_region.num_users
                
                """if ant_region.num_users + usr_region.num_users > ant_region.max_users:"""
                if ant_region.num_users > ant_region.max_users:
                    # Exceeded the maximum number of users...
                    if not ignore_unconnected:
                        if verbose: print("Antena no setor com usuario excedeu seu limite de usuarios ", usr_region)
                        # ... so, the evaluated solution does not serve all users
                        if return_map_of_service:
                            return None, None
                        else:
                            return None
                    """else:
                        # ..., but this will be ignored.
                        users_regions_list = [x for x in users_regions_list if x.index != usr_region.index]
                        continue"""

                else:
                    """ant_region.num_users += usr_region.num_users"""

                    # Updates the connections dictionary, the list of Regions with users without the current region and 
                    # the user regions without the current region
                    connect_dict[usr_region.index] = ant_region.index
                    """users_regions_list = [x for x in users_regions_list if x.index != usr_region.index]"""
                    users_regions = users_regions[~np.isin(users_regions, usr_region.index)]

                    if ant_region.num_users == ant_region.max_users:
                        # After connecting users the maximum number has been reached
                        antennas_regions_list = [x for x in antennas_regions_list       # Update list of Region by removing the saturated antenna
                                                   if x.index != ant_region.index]
                        isSaturated = True
                        break
                
            else:
                # The analyzed region has more than one possibility of connection

                # Find a list of Region of antenna in which the indexes corresponds to that of the serving antenna
                list_ant_region: list[geo.Region] = [x for x in antennas_regions_list if str(x.index) in usr_region.serving_antennas]

                # Sort the antennas in ascending order of number of users already connected
                # NOTE: the objective is to prioritize the antennas that are closer to reaching their capacity
                # This does not guarantee that the connection will be made with the one that provides the best signal,
                # but that is not the purpose of the problem.
                list_ant_region.sort(key=lambda x: x.num_users, reverse=True)
                if verbose: print("Aqui")
                for p in list_ant_region:
                    if verbose: print(p)
                while len(list_ant_region):      
                    ant_region = list_ant_region[0]              
                    if ant_region.num_users + usr_region.num_users <= ant_region.max_users:
                        # Updates the number of users connected to antenna in the Region ant_region
                        ant_region.num_users += usr_region.num_users

                        connect_dict[usr_region.index] = ant_region.index
                        """users_regions_list = [x for x in users_regions_list if x.index != usr_region.index]"""
                        users_regions = users_regions[~np.isin(users_regions, usr_region.index)]

                        if ant_region.num_users == ant_region.max_users:
                            # After connecting users the maximum number has been reached
                            antennas_regions_list = [x for x in antennas_regions_list    # Update list of Region by removing the saturated antenna
                                                       if x.index != ant_region.index]
                            isSaturated = True
                        
                        break                                                           # Stops at the first antenna where it is possible to connect
                    
                    else:
                        # Could not connect to current antenna, so try next one
                        list_ant_region.pop(0)
                
                if isSaturated:
                    break

                if len(list_ant_region) == 0:
                    if verbose: print("Setor coberto por mais de uma antena, mas nenhuma serviu ", usr_region)
                    # None of the serving antennas could service the current sector
                    if not ignore_unconnected:
                        if return_map_of_service:
                            return None, None
                        else:
                            return None      
                    
                    """else:
                        #print(f"Limite de usuário excedido. Não foi possivel conectar os {usr_region.num_users} usuarios em {usr_region.index}")
                        #print("Lista de antenas.")
                        for k in range(len(antennas_regions_list)):
                            print(antennas_regions_list[k])
                        users_regions_list = [x for x in users_regions_list if x.index != usr_region.index]
                        continue       """  
    if return_map_of_service:
        return connect_dict, map_of_service
    else:
        return connect_dict
    
        
def get_map_of_service(antennas_regions: List[int], metric_map_mn: List[List[float]], metric_threshold: float = None,
                       minimization: bool= False, threshold: bool = False, full: bool = False, old: bool = True) -> Union[List[List[str]], List[dict]]:
    """Get a map with the antennas that would serve each region.

    Args:
        antennas_regions: List with the antennas regions in the map
        metric_map_mn: Square matrix m x n representing a list of the metric map for each antenna position.
        metric_threshold (float): Indicates a threshold for analysing regions of a map based on a metric.
        minimization (bool): Indicates if a lower (minimization) or a higher (maximization) value is better.
        threshold (bool): Indicates if map of service has only region with metric higher than a metric threshold. The others are
                          assigned with "None". Argument "minimization" must be False and "full" must be True.
        full (bool): If True, indicates that map of service includes a list of all antennas that can serve each region, not just the
              antenna that offers the best or worst metric for each region.
        old (bool): The function works like the old way: 
              

    Returns:
        List[List[str]]: List with the antennas regions that serves each index/region. With full = True.
        List[dict]: List with dicts with antennas region ("antenna") and the metric value ("metric") that best serves each index/region. With full = False.
    """
    metrics_of_service = {}                                                 # A dict where the key is the antenna region and 
                                                                            # the value is your the metrics map (e.g. snr map)
    # Example:
    # metrics_of_service = {'key1': [...,...,...], 'key2': [...,...,...]}
    
    # Every possible pair of antennas to compare
    # TODO: Development the case "1 single antenna"
    antennas_pairs = []                                                     # List of tuples with all possible pairs of antennas
    for i in range(len(antennas_regions)):
        #Initializes metrics_of_service for each antenna
        metrics_of_service[str(antennas_regions[i])] = np.array(metric_map_mn[antennas_regions[i]])
        for j in range(i+1, len(antennas_regions)):
            antennas_pairs.append((antennas_regions[i], antennas_regions[j]))

    ##------------------------------- UNCHANGED ------------
    if not full:
        # Compare the metrics of service between the pair of antennas
        for m, n in antennas_pairs:    
            comp_array = metrics_of_service[str(m)] > metrics_of_service[str(n)]    # List of bool that shows the index where metrics of service 
                                                                                    # is higher in m than in n                                                                                
            # Example:
            # comp_array = [True, True, False, True, ...] 

            if minimization:
                comp_array = ~comp_array                                            # Inverts the comparison to obey that a big value is better
            
            # Setting to +/- inf where metrics_of_service in m does not better than in n and vice versa
            # NOTE: It does not guarantee that the antenna that best serves the region does so with a metric above/below some defined threshold
            metrics_of_service[str(m)][~comp_array] = np.inf if minimization else -np.inf 
            metrics_of_service[str(n)][comp_array] = np.inf if minimization else -np.inf

        if old:
            # The map of service is initialized as a list of integers where each element
            # indicates the antenna that best serves the respective sector regardless of
            # defined threshold.
            map_of_service = [ -1 for _ in range(len(metric_map_mn[-1]))]
        else:
            # The map of service is initialized as a list of dict. The "metric" key is used to apply a threshold.
            map_of_service = [{"antenna": -1, "metric": -1} for _ in range(len(metric_map_mn[-1]))]

        for key in metrics_of_service:
            if minimization:
                served_sectors = np.ravel(np.argwhere(metrics_of_service[key] < np.inf))
            else:
                served_sectors = np.ravel(np.argwhere(metrics_of_service[key] > -np.inf))
            for i in served_sectors:
                if old:
                    map_of_service[i] = key
                else:
                    map_of_service[i] = {"antenna": int(key), "metric": metric_map_mn[int(key)][i]}
        
        if old:
            if -1 in map_of_service:
                raise(ValueError('One region is not served in Map Of Service with value -1.'))
        else:
            if {"antenna": -1, "metric": -1} in map_of_service:
                raise(ValueError('One region is not served in Map Of Service with values -1.'))
        
        # Apply the threshold to map of service
        if threshold and not old:
            for m in range(len(map_of_service)):
                if not minimization:    # higher value is better
                    if map_of_service[m]["metric"] < metric_threshold:
                        map_of_service[m] = None
                else:
                    pass
                    #TODO: To implement if minimization is True

    else:
        # The map of service is a list of list where each element indicates the antennas that serve the respective sector
        map_of_service = [[] for _ in range(len(metric_map_mn[-1]))]
        # Example:
        # map_of_service = [[],[],['key1','key2'],['key1'],[],...]
        
        for key in metrics_of_service:
            served_sectors = []                                 # List of sectors served by antenna <key>
            for region in range(len(metric_map_mn[int(key)])):
                if metric_map_mn[int(key)][region] >= metric_threshold:
                    served_sectors.append(region)
        
            for i in served_sectors:
                map_of_service[i].append(key)

    return map_of_service

def gen_first_antenna_region(chosen_seed: int, n_sectors: int):
    return _user_traffic.gen_first_antenna_region(chosen_seed, n_sectors)

def gen_users_t_m(seed_val, lambda_poisson, num_slices):
    return _user_traffic.gen_users_t_m(seed_val, lambda_poisson, num_slices)

def gen_ue_per_slice(chosen_seed, user_t_m, num_slices):
    return _user_traffic.gen_ue_per_slice(chosen_seed, user_t_m, num_slices)

def get_coordinate_eccentricity(scen: geo.MapChess, coords: List[geo.Coordinate]):
    centre = scen.centre_coord
    
    if len(coords) == 1:
        #
        dist_centre = geo.euclidianDistance(coords[0], centre)
        if dist_centre == 0:
            dist_centre = 1

        dist_boundary = dist2NearestBoundary(scen, coords[0])
        if dist_boundary == 0:
            dist_boundary = 1
        
        eccentricity = 1/(1/dist_centre + 1/dist_boundary)
        print(eccentricity)
    else:
        # 
        mean_dist_by_coord = [None]*len(coords)
        dist_centre_by_coord = [None]*len(coords)
        dist_boundary_by_coord = [None]*len(coords)
        for i in range(len(coords)):
            dist = 0
            for j in range(len(coords)):
                if i != j:
                    dist += geo.euclidianDistance(coords[i], coords[j])
            
            dist = dist/(len(coords)-1)
            if dist == 0:
                dist = 1
            mean_dist_by_coord[i] = dist
            
            dist_centre = geo.euclidianDistance(coords[i], centre)
            if dist_centre == 0:
                dist_centre = 1
            dist_centre_by_coord[i] = dist_centre
            
            dist_boundary = dist2NearestBoundary(scen, coords[i])
            if dist_boundary == 0:
                dist_boundary = 1
            dist_boundary_by_coord[i] = dist_boundary
            
        eccentricity = mean([mean_dist_by_coord[i] + dist_centre_by_coord[i] + 10*dist_boundary_by_coord[i] for i in range(len(coords))])
        
    eccentricity = eccentricity/(12*scen.max_length)

    return eccentricity


def dist2NearestBoundary(scen: geo.MapChess, coord: geo.Coordinate):
    upper_boundary_dist = scen.size_y - coord.y
    bottom_boundary_dist = coord.y
    left_boundary_dist = coord.x
    right_boundary_dist = scen.size_x - coord.x

    return min([upper_boundary_dist, bottom_boundary_dist, left_boundary_dist, right_boundary_dist])