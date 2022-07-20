# Import the necessary modules and libraries
from turtle import distance
import numpy as np
from typing import List, Callable
import geometry as geo
from helper_xml import get_map_ues_time
import general_functions as genf
import pygad
from time import time, localtime, mktime
from datetime import datetime
from random import randint, seed, random
import sinr_comput as sc

_users_t_m = []
_antennas_last_result = []
_distance_mn = []
_snr_map_mn = []
_min_dis = 0
_first_antenna_region = 0

def main():
    #General configs
    chosen_seeds = [2]#[2,3,4,5,6,7,10,11,12,13]#
    size_x = 4000
    size_y = 4000
    size_sector = 400
    n_macros = 1
    micro_power = 30 #dBm
    result_dir = "Solutions"
    extra_dir = ['disaster_percentage', 'micro_power']
    num_slices = 10
    min_sinr = 5
    mode = 'single'
    #is_micro = True #Keep True
    disaster_percentage = 0 #Porcentagem do alastramento do desastre (%)
    move_config_name = 'ilp_move_users'
    min_dis = 2000

    run_ga_solvers(chosen_seeds=chosen_seeds, size_x= size_x, size_y=size_y, size_sector=size_sector, n_macros=n_macros,
                   move_config_name=move_config_name, result_dir=result_dir, mode=mode, min_sinr=min_sinr, num_slices=num_slices,
                   extra_dir=extra_dir, micro_power= micro_power, min_dis= min_dis,
                   disaster_percentage= disaster_percentage) #Disaster as an extra argument in **kwargs to use with extra_dir
  

def run_ga_solvers(chosen_seeds: List[int], size_x: int, size_y: int, size_sector: int,n_macros: int, move_config_name: str,
                   result_dir: str, mode: str, min_sinr: int, num_slices: int, extra_dir: List[str], micro_power: int,
                   min_dis: int, is_micro: bool = True, **kwargs):

    params = locals() #get local variables in the beginning of the function (the parameters in this case)
    results = []

    num_sectors = int(size_x/size_sector) * int(size_y/size_sector)

    for param in extra_dir:
        if param in kwargs: #If is an extra parameter passed by kwargs
            result_dir += '/' + f'{param}_{kwargs[param]}'
        elif param in params: #If is a necessary default parameter
            result_dir += '/' + f'{param}_{params[param]}'

    min_sinr_w = sc.db_to_linear(min_sinr)

    for chosen_seed in chosen_seeds:

        start_time = time()
        print(f'Start: {datetime.fromtimestamp(mktime(localtime(start_time)))} (Seed: {chosen_seed}).')

        full_result_dir = result_dir + f'/chosen_seed_{chosen_seed}'

        #Initiating scenario
        scen = geo.MapChess(size_y, size_x, size_sector, carrier_frequency= 0.7, chosen_seed= chosen_seed, scenario= "URBAN_MICROCELL" if is_micro else "URBAN_MACROCELL",
                            enb_tx_power= micro_power if is_micro else 46, h_enbs= 18, gain_ue= -1, enb_noise_figure= 9)

        #Placing UEs
        scen.placeUEs(type= "Random", n_macros= n_macros, n_ues_macro= 60)

        xml_filename = genf.gen_movement_filename(move_config_name, chosen_seed, snapshot= True)

        distance_mn = scen.getRegionsDistanceMatrix()

        users_t_m = get_map_ues_time(scen= scen, xml_filename= xml_filename)

        snr_map_mn = scen.getSinrMap()

        optimized_byslice, antennas_regions_byslice, num_enbs_time = genf.parse_results_per_slice(genf.gen_solver_result_filename(full_result_dir, mode, min_sinr), num_slices)

        if optimized_byslice == None and antennas_regions_byslice == None and num_enbs_time == None:
            #There was a not feasible solution
            print(f'\nNot feasable solution in case: Seed {chosen_seed}, Mode: traditional (single). Ignoring this case.\n')
            continue

        antennas_m = [0 for _ in range(num_sectors)]
        for region in antennas_regions_byslice[-1]:
            antennas_m[region] = 1

        seed(chosen_seed)
        _ = [(0 if random() < 0/100 else 1) for i in range(scen.n_sectors)]
        first_antenna_region = randint(0, scen.n_sectors - 1)
        print(f'Seed: {chosen_seed}. First Antenna Region: {first_antenna_region}.')

        result = ga_solver(traditional_antennas_map=antennas_m, users_t_m=users_t_m, distance_mn=distance_mn, snr_map_mn=snr_map_mn, fitness_func=fitness,
                           first_antenna_region=first_antenna_region, num_slices=num_slices, min_dis=min_dis, min_sinr_w= min_sinr_w)
        results.append(result)

        print(f'Done after {(time() - start_time)/(60*60)} hours. (Seed: {chosen_seed})')

        #print(f'\n{full_result_dir}')
        #print(antennas_regions_byslice[-1])
        #scen.placeAntennas(antennas_regions_byslice[-1])
        #genf.plot_scenario(scen= scen, title= f'{full_result_dir}')

def ga_solver(traditional_antennas_map: List[int], users_t_m: List[List[int]], distance_mn: List[List[float]], snr_map_mn: List[List[float]], fitness_func: Callable[..., float],
              first_antenna_region: int, num_slices: int, min_dis: int, min_sinr_w: float):

    if len(users_t_m) < num_slices:
        print('\nError: Missing slices in users behaviour (users_t_m). Returning without solution.\n')
        return

    antennas_regions_byslice = []

    global _distance_mn
    _distance_mn = distance_mn
    global _snr_map_mn
    _snr_map_mn = snr_map_mn
    global _min_dis
    _min_dis = min_dis
    global _min_sinr_w
    _min_sinr_w = min_sinr_w
    global _first_antenna_region
    _first_antenna_region = first_antenna_region

    num_regions = len(traditional_antennas_map)

    global _antennas_last_result
    _antennas_last_result = [ 0 if m != first_antenna_region else 1 for m in range(num_regions)]

    for i in range(num_slices):
        
        print(f'\nStarting GA of slice {i}.\n')

        global _users_t_m
        _users_t_m = users_t_m[i:]

        if i == 0:
            antennas_regions = run_genetic(traditional_antennas_map, fitness_func, callback_gen)
        else:
            antennas_regions = run_genetic(_antennas_last_result, fitness_func, callback_gen)

        #antennas_regions = run_genetic(traditional_antennas_map, fitness_func)

        antennas_m = [0 for _ in range(num_regions)]

        for region in antennas_regions:
            antennas_m[region] = 1

        _antennas_last_result = antennas_m #Update last slice result

        antennas_regions_byslice.append(antennas_regions)

    return antennas_regions_byslice

def run_genetic(base_genome: List[int], fitness_func: Callable[..., float], on_generation_callback: Callable):

    # The attribures

    """
    parent_selection_type options
    sss (for steady-state selection), 
    rws (for roulette wheel selection), 
    sus (for stochastic universal selection), 
    rank (for rank selection), <- (truncation)
    random (for random selection), 
    and tournament (for tournament selection)
    """
    parent_selection_type = "rank"

    """
    crossover_type options
    Type of the crossover operation. Supported types are single_point (for single-point crossover),
    two_points (for two points crossover), 
    uniform (for uniform crossover), 
    and scattered (for scattered crossover).
    """
    crossover_type = "two_points"

    """
    Type of the mutation operation. Supported types are random (for random mutation), 
    swap (for swap mutation), 
    inversion (for inversion mutation), 
    scramble (for scramble mutation), 
    and adaptive (for adaptive mutation).
    """
    mutation_type = "random" 

    num_generations = 100
    num_parents_mating = 4 # Número de pais a serem selecionados

    population_size = 100 # Tamanho da população

    num_genes = len(base_genome)

    #colocar solução valida
    
    keep_parents = 2 # Nr de indivíduos que serão selecionados para a próxima geração sem sofrer crossover nem mutação

    #mutation_percent_genes = 10 #% de porcentagem dos genes a mutar
    mutation_probability = 0.2 # chance de ocorrer a mutação em um gene (entre 0 e 1)
    crossover_probability = 0.8

    gene_space = [0, 1]

    initial_population = create_population(base_genome=base_genome, population_size=population_size)

    ga_instance=pygad.GA(num_generations=num_generations,
                        num_parents_mating=num_parents_mating,
                        fitness_func=fitness_func,
                        initial_population=initial_population,
                        parent_selection_type=parent_selection_type,
                        keep_parents=keep_parents,
                        crossover_type=crossover_type,
                        crossover_probability=crossover_probability,
                        mutation_type=mutation_type,
                        mutation_probability=mutation_probability,
                        gene_space=gene_space,
                        on_generation=on_generation_callback,
                        #stop_criteria=[f"reach_{M*T}"],
                        gene_type=int)

    ga_instance.run()

    solution, solution_fitness, solution_idx = ga_instance.best_solution()
    print("Parameters of the best solution : {solution}".format(solution=solution))
    print("Number of antennas of the best solution = {solution_fitness}".format(solution_fitness=num_genes - solution_fitness))
    print("Index of the best solution : {solution_idx}".format(solution_idx=solution_idx))
    #print(f"Percentage of optimal: {solution_fitness/(M*T) * 100}%")
    print(f"Total generations: {ga_instance.generations_completed}.")

    if ga_instance.best_solution_generation != -1:
        print("Best fitness value reached after {best_solution_generation} generations.".format(best_solution_generation=ga_instance.best_solution_generation))
        #ga_instance.plot_fitness()

    antennas_regions = np.ravel(np.argwhere(solution > 0))

    regions_of_service = genf.get_regions_of_service(antennas_regions=antennas_regions, metric_map_mn= _snr_map_mn, minimization= False)

    # Must be connected to the backhaul
    cleared = []
    for m in antennas_regions:
        if m in cleared or m == _first_antenna_region:
            continue
        for n in antennas_regions:
            if m!=n:
                if _distance_mn[m][n] <= _min_dis:
                    if m not in cleared:
                        cleared.append(m)
                    if n not in cleared and n != _first_antenna_region:
                        cleared.append(n)

    print(f'Cleared: {np.sort(cleared, kind= "heapsort")}.\nAntennas: {np.sort(antennas_regions, kind= "heapsort")}')
    print(f'Distances:')

    for i in range(len(antennas_regions)):
        for j in range(i+1, len(antennas_regions)):
            print(f'\n{antennas_regions[i]} : {antennas_regions[j]} => {_distance_mn[antennas_regions[i]][antennas_regions[j]]}')

    #for key in regions_of_service:
    #    print(f'Antenna: {key}. Number Regions: {len(regions_of_service[key])}.\n\tRegions: {regions_of_service[key]}.')

    return antennas_regions

def fitness(solution, solution_idx):
    """Evaluates how good a solution is.
    """

    num_genes = len(solution)
    fitness_score = (num_genes - sum(solution))#Antennas per time #+ M*M*T

    antennas_regions = np.ravel(np.argwhere(solution > 0))

    # After installed an antenna can never be removed
    for m in range(num_genes):
           if _antennas_last_result[m] == 1 and solution[m] != 1:
                return 0

    # Must provide a minimum amount of SINR to all users
    regions_of_service = genf.get_regions_of_service(antennas_regions=antennas_regions, metric_map_mn= _snr_map_mn, minimization= False)

    for n in range(num_genes):
        if _users_t_m[0][n] > 0: #Only verifies the snr of regions with users
            snr_value = -np.inf
            for key in regions_of_service: #Discovers the serving antenna and the snr value
                if n in regions_of_service[key]:
                    snr_value = _snr_map_mn[int(key)][n]
                    break
            if snr_value < _min_sinr_w:
                return 0

    
    # Must be connected to the backhaul
    cleared = []
    for m in antennas_regions:
        if m in cleared or m == _first_antenna_region:
            continue
        for n in antennas_regions:
            if m!=n:
                if _distance_mn[m][n] <= _min_dis:
                    if m not in cleared:
                        cleared.append(m)
                    if n not in cleared and n != _first_antenna_region:
                        cleared.append(n)
    # Compares the sorted cleared array with the sorted antennas regions without the first antenna
    sorted_antennas = np.sort(antennas_regions, kind= "heapsort")
    sorted_cleared = np.sort(cleared + [_first_antenna_region], kind= "heapsort")
    if not np.array_equal(sorted_cleared, sorted_antennas):
        return 0

    return fitness_score

def callback_gen(ga_instance):
    print("Generation : ", ga_instance.generations_completed)
    print("Fitness of the best solution :", ga_instance.best_solution()[1])

def create_population(base_genome, population_size):
    """Create the population of genomes.

    Returns:
        A List of List[int] where each List[int] represents a genome.
    """
    return[base_genome for _ in range(population_size)]

if __name__ == '__main__':
    main()