from pathlib import Path
from typing import List, Union
from matplotlib import use
import numpy as np
import geometry as geo
import matplotlib.pyplot as plt
from scipy.stats import poisson
from random import choice, randint, seed, random

MODES_NEW_NAMES = {
    'varying': 'VID',# Varying ILP Deployment
    'single': 'TID',# Traditional ILP Deployment
    'fixed': 'AID',# Additive ILP Deployment
    'ga': 'PGD',# Predicative GA Deployment
    'gwo': 'PGWO' #Progressive GWO
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
        elif mode.lower() == 'gwo':
            verif_modes.append('gwo')

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

def print_map_mn(scen: geo.MapChess, map_name: str, values: List[List[Union[int,float]]]):
    print(map_name)
    num_sector = int(scen.size_y/scen.size_sector)
    for i in range(num_sector):
        print(values[i*num_sector:num_sector*(i+1)])   

def get_dict_of_connections(antennas_regions, users_regions, users_m, snr_map_mn, min_sinr_w, max_users_per_antenna_m, ignore_unconnected: bool = False, verbose: bool = False):
    connect_dict = {}
    antennas_regions_list = [geo.Region(region,0,max_users_per_antenna_m[region],[]) for region in antennas_regions]
    isSaturated = True
    users_regions_list = [None]
    if verbose: print("MinSINR: ", min_sinr_w)
    while len(users_regions_list):
        if isSaturated:
            map_of_service = get_map_of_service([region.index for region in antennas_regions_list], snr_map_mn, min_sinr_w, minimization=False, threshold=True, full=True)
            users_regions_list = [geo.Region(region,users_m[region],None,map_of_service[region]) for region in users_regions]
            users_regions_list.sort(key=lambda x: x.num_serving_antennas, reverse=False)
    
        isSaturated = False
        for usr_region in users_regions_list:
            #if ignore_unconnected: print("usr: ", usr_region)            
            if usr_region.serving_antennas == []:
                if verbose: print("Algum usuario nao atendido por nenhuma antena")
                if not ignore_unconnected:
                    return None
                else:
                    #print(f"Usuario em {usr_region.index} nao pode ser atendido por nenhuma antena.")
                    users_regions_list = [x for x in users_regions_list if x.index != usr_region.index]
                    continue
            
            #print(f"\n{usr_region.num_users} usuarios no setor {usr_region.index} atendido por: ", usr_region.serving_antennas)
            
            if str(usr_region.index) in usr_region.serving_antennas:
                #print("Users must be served by antenna in same sector")
                ant_region = list(filter(lambda x: x.index == usr_region.index, antennas_regions_list))[0]
                ant_region.num_users += usr_region.num_users
                
                if ant_region.num_users > ant_region.max_users:
                    # NOTE: Mesmo que esteja sendo usada para avaliar as conexoes em slices futuros (ignore_unconnected),
                    # se cair no caso de que o numero de  usuarios da regiao em que ha uma antena for maior que max_users
                    # entao nao e uma solucao valida, pois fixar uma antena nesse local impossibilitaria de encontrar
                    # alguma solucao valida por causa da restricao de que uma antena serve aos usuarios do proprio setor 
                    #if ignore_unconnected : print("Limite de usuário excedido")
                    return None

                #print("Connectando with...")
                #print(ant_region)
                connect_dict[usr_region.index] = usr_region.index
                users_regions_list = [x for x in users_regions_list if x.index != usr_region.index]
                users_regions = users_regions[~np.isin(users_regions, usr_region.index)]

                #print("Conexões_1: ", connect_dict)

                if ant_region.num_users == ant_region.max_users:
                    #print("Antena saturada")
                    antennas_regions_list = [x for x in antennas_regions_list if x.index != ant_region.index]
                    isSaturated = True
                    break

                continue
            
            if usr_region.num_serving_antennas == 1:                
                ant_region = list(filter(lambda x: x.index == int(usr_region.serving_antennas[0]), antennas_regions_list))[0]
                
                if ant_region.num_users + usr_region.num_users > ant_region.max_users:
                    if verbose: print(f"Limite de usuário excedido (*). Não foi possivel conectar o usuario em {usr_region.index}")
                    if not ignore_unconnected:
                        return None
                    else:
                        users_regions_list = [x for x in users_regions_list if x.index != usr_region.index]
                        continue

                else:
                    #if ignore_unconnected:
                    #    print("\nlista de antenas antes")
                    #    for k in range(len(antennas_regions_list)):
                    #        print("Ant: ", antennas_regions_list[k])
                    ant_region.num_users += usr_region.num_users
                    #if ignore_unconnected:
                    #    print("\nlista de antenas depois")
                    #    for k in range(len(antennas_regions_list)):
                    #        print("Ant': ", antennas_regions_list[k])
                    #    print('\n')
                    connect_dict[usr_region.index] = ant_region.index
                    users_regions_list = [x for x in users_regions_list if x.index != usr_region.index]
                    users_regions = users_regions[~np.isin(users_regions, usr_region.index)]

                    #print("Conexões_2: ", connect_dict)
                    if ant_region.num_users == ant_region.max_users:
                        #print("Antena saturada!!!")
                        antennas_regions_list = [x for x in antennas_regions_list if x.index != ant_region.index]
                        isSaturated = True
                        break
                
            else:
                tmp = [x for x in antennas_regions_list if str(x.index) in usr_region.serving_antennas]
                tmp.sort(key=lambda x: x.num_users, reverse=True)
                #if ignore_unconnected:
                #    for k in range(len(tmp)):
                #        print("Ant:", tmp[k])
        
                while len(tmp):                    
                    if tmp[0].num_users + usr_region.num_users <= tmp[0].max_users:
                        #if ignore_unconnected: print("Buscando conectar com uma antena que ja possui ", tmp[0].num_users, " usuarios.")
                        tmp = [x for x in tmp if x.num_users == tmp[0].num_users]

                        snr = -np.infty
                        for k in tmp:
                            if snr_map_mn[k.index][usr_region.index] > snr:
                                ant_index = k.index
                                snr = snr_map_mn[k.index][usr_region.index]
                        #if ignore_unconnected: print("Conectando com ", k.index)
                        for ant_region in antennas_regions_list:
                            if ant_region.index == ant_index:#int(usr_region.serving_antennas[0]):
                                break
                        #if ignore_unconnected:
                        #    print("\nlista de antenas antes")
                        #    for k in range(len(antennas_regions_list)):
                        #        print("Ant: ", antennas_regions_list[k])
                        ant_region.num_users += usr_region.num_users
                        #if ignore_unconnected:
                        #    print("\nlista de antenas depois")
                        #    for k in range(len(antennas_regions_list)):
                        #        print("Ant': ", antennas_regions_list[k])
                        #    print('\n')
                        
                        connect_dict[usr_region.index] = ant_region.index
                        users_regions_list = [x for x in users_regions_list if x.index != usr_region.index]
                        users_regions = users_regions[~np.isin(users_regions, usr_region.index)]

                        #print("Conexões_3: ", connect_dict)
                        if ant_region.num_users == ant_region.max_users:
                            antennas_regions_list = [x for x in antennas_regions_list if x.index != ant_region.index]
                            isSaturated = True
                        break
                    else:
                        # Descarta a antena para tentar com a proxima possibilidade
                        tmp.pop(0)
                
                if isSaturated:
                    break

                if len(tmp) == 0:
                    if not ignore_unconnected:
                        if verbose: print("Nao foi possivel conectar com nenhuma antena dentre as possiveis")
                        return None      
                    else:
                        #print(f"Limite de usuário excedido. Não foi possivel conectar os {usr_region.num_users} usuarios em {usr_region.index}")
                        #print("Lista de antenas.")
                        for k in range(len(antennas_regions_list)):
                            print(antennas_regions_list[k])
                        users_regions_list = [x for x in users_regions_list if x.index != usr_region.index]
                        continue         
            
    #print("Saindo do loop")
    return connect_dict
    
        

def get_map_of_service(antennas_regions: List[int], metric_map_mn: List[List[int]], metric_threshold: int = None, minimization: bool= False, threshold: bool = False, full: bool = False, old: bool = True):
    """Get a map with the antennas that would serve each region.

    Args:
        antennas_regions: List with the antennas regions in the map
        metric_map_mn: Matrix m x n representing a list of the metric map for each antenna position. m must be equal to n.
        metric_threshold: Indicates a threshold for analysing regions of a map based on a metric.
        minimization: Indicates if a lower (minimization) or a higher (maximization) value is better.
        threshold: Indicates if map of service has only region with metric higher than a metric threshold. 
                   Argument "minimization" must be False.
        full: Indicates if map of service includes a list of antennas that can serve each region, not just the
              antenna that offers the best or worst metric for each region.
        old: Changes the output of the default
              

    Returns:
        if old is True: List with the antennas regions that serves each index/region.
        else: List with dicts with antennas region ("antenna") and the metric value ("metric") that serves each index/region.
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
    
    if not full:
        
        if old:
            map_of_service = [ -1 for _ in range(len(metric_map_mn[-1]))]
        else:
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

    else:
        map_of_service = [[] for _ in range(len(metric_map_mn[-1]))]

        for key in metrics_of_service:
            served_sectors = []
            for region in range(len(metric_map_mn[int(key)])):
                if metric_map_mn[int(key)][region] >= metric_threshold:
                    served_sectors.append(region)
        
            for i in served_sectors:
                map_of_service[i].append(key)

    if threshold and not full:
        for m in range(len(map_of_service)):
            if not minimization:    # higher value is better
                if metric_map_mn[int(map_of_service[m])][m] < metric_threshold:
                    map_of_service[m] = None
            #TODO: To implement if minimization is True
    
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
