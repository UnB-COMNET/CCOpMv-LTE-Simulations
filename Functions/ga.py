# Import the necessary modules and libraries
import numpy as np
from typing import List, Callable
import geometry as geo
from helper_xml import get_map_ues_time
import general_functions as genf
import pygad
from time import time, localtime, mktime
from datetime import datetime
import sinr_comput as sc
import random
import math
from sinr_comput import linear_to_db

_users_t_m = []
_antennas_last_result = []
_distance_mn = []
_snr_map_mn = []
_min_sinr_w = 0
_min_dis = 0
_first_antenna_region = 0
_max_users_per_antenna_m = []

_last_antennas_regions = []

_connection_results = []

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
    #mode = 'single'
    #is_micro = True #Keep True
    disaster_percentage = 0 #Porcentagem do alastramento do desastre (%)
    move_config_name = 'ilp_move_users'
    min_dis = 2000

    run_ga_solvers(chosen_seeds=chosen_seeds, size_x= size_x, size_y=size_y, size_sector=size_sector, n_macros=n_macros,
                   move_config_name=move_config_name, result_dir=result_dir, min_sinr=min_sinr, num_slices=num_slices, #mode=mode,
                   extra_dir=extra_dir, micro_power= micro_power, min_dis= min_dis,
                   disaster_percentage= disaster_percentage) #Disaster as an extra argument in **kwargs to use with extra_dir
  

def run_ga_solvers(chosen_seeds: List[int], size_x: int, size_y: int, size_sector: int,n_macros: int, move_config_name: str,
                   result_dir: str, min_sinr: int, num_slices: int, extra_dir: List[str], micro_power: int, #mode: str,
                   min_dis: int, is_micro: bool = True, **kwargs):

    params = locals() #get local variables in the beginning of the function (the parameters in this case)
    results = []

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
        scen = geo.MapChess(size_y = size_y, size_x = size_x, size_sector = size_sector, carrier_frequency= 0.7, chosen_seed= chosen_seed, scenario= "URBAN_MICROCELL" if is_micro else "URBAN_MACROCELL",
                            enb_tx_power= micro_power if is_micro else 46, h_enbs= 18, gain_ue= -1, enb_noise_figure= 9, num_slices= num_slices)

        #Placing UEs
        scen.placeUEs(type= "Random", n_macros= n_macros, n_ues_macro= 60)

        xml_filename = genf.gen_movement_filename(move_config_name, chosen_seed, snapshot= True)

        distance_mn = scen.getRegionsDistanceMatrix()

        users_t_m = get_map_ues_time(scen= scen, xml_filename= xml_filename)

        snr_map_mn = scen.getSinrMap()

        max_users_antenna_m = [60 for i in range(scen.n_sectors)]

        #optimized_byslice, antennas_regions_byslice, num_enbs_time = genf.parse_results_per_slice(genf.gen_solver_result_filename(full_result_dir, mode, min_sinr), num_slices)

        #if optimized_byslice == None and antennas_regions_byslice == None and num_enbs_time == None:
            #There was a not feasible solution
        #    print(f'\nNot feasable solution in case: Seed {chosen_seed}, Mode: traditional (single). Ignoring this case.\n')
        #    continue

        #antennas_m = [0 for _ in range(num_sectors)]
        #for region in antennas_regions_byslice[-1]:
        #    antennas_m[region] = 1

        first_antenna_region = genf.gen_first_antenna_region(chosen_seed=chosen_seed, n_sectors=scen.n_sectors)
        print(f'Seed: {chosen_seed}. First Antenna Region: {first_antenna_region}.')

        result = ga_solver(num_regions=scen.n_sectors, users_t_m=users_t_m, distance_mn=distance_mn, snr_map_mn=snr_map_mn, fitness_func=fitness_pygad if pygad else fitness,
                           first_antenna_region=first_antenna_region, num_slices=num_slices, min_dis=min_dis, min_sinr_w= min_sinr_w, max_users_per_antenna_m=max_users_antenna_m,
                           result_dir= full_result_dir)
        results.append(result)

        print(f'Done after {(time() - start_time)/(60*60)} hours. (Seed: {chosen_seed})')

        #print(f'\n{full_result_dir}')
        #print(antennas_regions_byslice[-1])
        #scen.placeAntennas(antennas_regions_byslice[-1])
        #genf.plot_scenario(scen= scen, title= f'{full_result_dir}')

def ga_solver(num_regions: int, users_t_m: List[List[int]], distance_mn: List[List[float]], snr_map_mn: List[List[float]], fitness_func,
              first_antenna_region: int, num_slices: int, min_dis: int, min_sinr_w: float, max_users_per_antenna_m: List[int], result_dir: str):

    if len(users_t_m) < num_slices:
        print('\nError: Missing slices in users behaviour (users_t_m). Returning without solution.\n')
        return

    antennas_regions_byslice = []
    connections_dict_byslice = []

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
    global _max_users_per_antenna_m
    _max_users_per_antenna_m = max_users_per_antenna_m

    global _antennas_last_result
    _antennas_last_result = [ 0 if m != first_antenna_region else 1 for m in range(num_regions)]

    for i in range(num_slices):
        
        print(f'\nStarting GA of slice {i}.\n')

        global _users_t_m
        _users_t_m = users_t_m[i:]

        #if i == 0:
            #antennas_regions = run_genetic(traditional_antennas_map, fitness_func, callback_gen)
            #_antennas_last_result = traditional_antennas_map #Update last slice result
            #continue
            #Not running GA for slice 0
        #else:
        antennas_regions, connections_dict = run_genetic(_antennas_last_result, fitness_func, callback_gen)
        #print(f'\nAntennas Regions: {antennas_regions}.\n\nConnections: {connections_dict}.\n')

        #antennas_regions = run_genetic(traditional_antennas_map, fitness_func)

        antennas_m = [0 for _ in range(num_regions)]

        for region in antennas_regions:
            antennas_m[region] = 1

        _antennas_last_result = antennas_m #Update last slice result

        antennas_regions_byslice.append(antennas_regions)
        connections_dict_byslice.append(connections_dict)

    write_file_result(result_dir=result_dir, users_t_m=users_t_m, distance_mn=distance_mn, snr_map_mn=snr_map_mn, min_sinr_w=min_sinr_w,
                      antennas_regions_byslice=antennas_regions_byslice, connections_dict_byslice=connections_dict_byslice)

    return antennas_regions_byslice, connections_dict_byslice

def run_genetic(base_genome: List[int], fitness_func: Callable[..., float], on_generation_callback: Callable):

    global _connection_results
    _connection_results = []

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
    parent_selection_type = "sss"

    """
    crossover_type options
    Type of the crossover operation. Supported types are 
    single_point (for single-point crossover),
    two_points (for two points crossover), 
    uniform (for uniform crossover), 
    and scattered (for scattered crossover).
    """
    crossover_type = "two_points"

    """
    Type of the mutation operation. Supported types are 
    random (for random mutation), 
    swap (for swap mutation), 
    inversion (for inversion mutation), 
    scramble (for scramble mutation), 
    and adaptive (for adaptive mutation).
    """
    mutation_type = antennas_mutation#"random" 
    #mutation_by_replacement = True #Works with random mutation
    random_mutation_min_val = 0
    random_mutation_max_val = 1

    num_generations = 100
    num_parents_mating = 4 # Número de pais a serem selecionados

    population_size = 100 # Tamanho da população

    num_genes = len(base_genome)

    #colocar solução valida
    
    keep_parents = 4 # Nr de indivíduos que serão selecionados para a próxima geração sem sofrer crossover nem mutação

    #mutation_percent_genes = 10 #% de porcentagem dos genes a mutar
    mutation_probability = 0.2 # chance de ocorrer a mutação em um gene (entre 0 e 1)
    #mutation_num_genes = 5 # vai mutar essa quantidade de genes
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
                        random_mutation_min_val= random_mutation_min_val,
                        random_mutation_max_val= random_mutation_max_val,
                        mutation_probability=mutation_probability,
                        #mutation_num_genes= mutation_num_genes,
                        #mutation_percent_genes=mutation_percent_genes,
                        #mutation_by_replacement=mutation_by_replacement,
                        gene_space=gene_space,
                        on_generation=on_generation_callback,
                        stop_criteria=[f"saturate_20"],
                        gene_type=int,
                        #save_solutions=True
                        )

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

    # # Must be connected to the backhaul
    # cleared = []
    # for m in antennas_regions:
    #     if m in cleared or m == _first_antenna_region:
    #         continue
    #     for n in antennas_regions:
    #         if m!=n:
    #             if _distance_mn[m][n] <= _min_dis:
    #                 if m not in cleared:
    #                     cleared.append(m)
    #                 if n not in cleared and n != _first_antenna_region:
    #                     cleared.append(n)

    # print(f'Cleared: {np.sort(cleared, kind= "heapsort")}.\nAntennas: {np.sort(antennas_regions, kind= "heapsort")}')
    # print(f'Distances:')

    for i in range(len(antennas_regions)):
        for j in range(i+1, len(antennas_regions)):
            print(f'\n{antennas_regions[i]} : {antennas_regions[j]} => {_distance_mn[antennas_regions[i]][antennas_regions[j]]}')

    #for key in regions_of_service:
    #    print(f'Antenna: {key}. Number Regions: {len(regions_of_service[key])}.\n\tRegions: {regions_of_service[key]}.')

    #print('Solutions: ', ga_instance.solutions.tolist())
    #print('Connections: ', _connection_results)

    return antennas_regions, _connection_results[solution_idx]

def fitness_pygad(solution, solution_idx):

    score, connect_dict = fitness(solution, solution_idx)

    global _connection_results
    _connection_results.append((connect_dict, solution_idx))

    return score

def fitness(solution, solution_idx):
    """Evaluates how good a solution is.
    """
    num_genes = len(solution)
    fitness_score = (num_genes - sum(solution))#Antennas per time #+ M*M*T

    antennas_regions = np.ravel(np.argwhere(np.array(solution) > 0))

    # After installed an antenna can never be removed
    for m in range(num_genes):
           if _antennas_last_result[m] == 1 and solution[m] != 1:
                return 0, None

    # Must provide a minimum amount of SINR to all users
    map_of_service = genf.get_map_of_service(antennas_regions=antennas_regions, metric_map_mn= _snr_map_mn, minimization= False)

    
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
        return 0, None

    users_regions = np.ravel(np.argwhere(np.array(_users_t_m[0]) > 0))
    base_connections_genome = [map_of_service[n] for n in users_regions]
    global _last_antennas_regions
    _last_antennas_regions = antennas_regions
    connect_solution, connect_fitness_score = run_genetic_connections(base_genome=base_connections_genome, fitness_func=fitness_connections, gene_space=antennas_regions)

    connect_dict = {}
    for i in len(users_regions):
        connect_dict[str(users_regions[i])] = connect_solution[i]

    return fitness_score * connect_fitness_score, connect_dict

def callback_gen(ga_instance):
    print("Generation : ", ga_instance.generations_completed)
    print("Fitness of the best solution :", ga_instance.best_solution()[1])

def create_population(base_genome, population_size):
    """Create the population of genomes.

    Returns:
        A List of List[int] where each List[int] represents a genome.
    """
    return[base_genome for _ in range(population_size)]

def antennas_mutation(offspring: np.ndarray, ga_instance: pygad.GA):
    #Necessary: gene_space como lista
    #Usando somente mutation_probability

    parents_idx = ga_instance.last_generation_parents_indices
    keep_count = ga_instance.keep_parents

    new_offspring = offspring.copy()

    for genome_idx in range(offspring.shape[0]):

        #If is a parent and keep_count is not zero, ignore the genome
        if genome_idx in parents_idx and keep_count != 0:
            keep_count -= 1
            continue


        for gene_idx in range(offspring[genome_idx].shape[0]):

            #Check probability
            if random.random() < ga_instance.mutation_probability:

                #Select new value
                value_id = ga_instance.gene_space.index(new_offspring[genome_idx][gene_idx])
                new_value_id = random.randint(0, len(ga_instance.gene_space) - 2)
                if new_value_id >= value_id:
                    new_value_id += 1

                # If it was not a valid solution, do normal mutation
                if ga_instance.last_generation_fitness[genome_idx] <= 0:

                    new_offspring[genome_idx][gene_idx] = ga_instance.gene_space[new_value_id]

                # If it was a valid solution, try to reduce the number of antennas
                else:
                    #If antenna, mutates normally removing the antenna
                    if new_offspring[genome_idx][gene_idx] > 0:
                        new_offspring[genome_idx][gene_idx] = ga_instance.gene_space[new_value_id]

                    #If it is empty, only swap values, to not increase the number of antennas
                    else:
                        other_idx = random.randint(0, new_offspring[genome_idx].shape[0] - 2)

                        #To not be the same gene
                        if other_idx >= gene_idx:
                            other_idx += 1

                        #Swap values
                        new_offspring[genome_idx][gene_idx], new_offspring[genome_idx][other_idx] = new_offspring[genome_idx][other_idx], new_offspring[genome_idx][gene_idx] 
    
    return new_offspring

def run_genetic_connections(base_genome: List[int], fitness_func: Callable[..., float], gene_space: List[int]):
    # The attribures

    parent_selection_type = "rank"
    crossover_type = "two_points"
    mutation_type = "random" 

    num_generations = 10
    num_parents_mating = 4 # Número de pais a serem selecionados

    population_size = 100 # Tamanho da população

    num_genes = len(base_genome)

    #colocar solução valida
    
    keep_parents = 2 # Nr de indivíduos que serão selecionados para a próxima geração sem sofrer crossover nem mutação

    #mutation_percent_genes = 10 #% de porcentagem dos genes a mutar
    mutation_probability = 0.2 # chance de ocorrer a mutação em um gene (entre 0 e 1)
    crossover_probability = 0.8

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
                        #stop_criteria=[f"reach_{M*T}"],
                        gene_type=int)

    ga_instance.run()

    solution, solution_fitness, solution_idx = ga_instance.best_solution()

    return solution, solution_fitness

def fitness_connections(solution, solution_idx):
    """Evaluates how good a solution is. Expect a connection solution.
    """
    #MUSTCONNECT
    #MUSTCONNECTTOENB
    #REGIONTOONEENB

    num_genes = len(solution)

    users_regions = np.ravel(np.argwhere(np.array(_users_t_m[0]) > 0)) #Regions that have users

    # Must provide a minimum amount of SINR to all users
    for i in range(num_genes):
        n = users_regions[i] #Region of the gene i of the genome
        serving_antenna = solution[i]
        snr_value = _snr_map_mn[int(serving_antenna)][n]
        if snr_value < _min_sinr_w:
            return 0

    # Constraint - if antenna in m then serve m
    for i in range(num_genes):
        n = users_regions[i] #Region of the gene i of the genome
        serving_antenna = solution[i]
        if n in _last_antennas_regions and serving_antenna != n:
            return 0

    # Antenas m support a max number of users connected
    users_connected_count = dict(zip(_last_antennas_regions, [ 0 for _ in _last_antennas_regions]))
    for i in range(num_genes):
        n = users_regions[i] #Region of the gene i of the genome
        serving_antenna = solution[i]
        users_connected_count[serving_antenna] += _users_t_m[0][n]
        if users_connected_count[serving_antenna] > _max_users_per_antenna_m[serving_antenna]:
            return 0

    fitness_score = 1
    return fitness_score
            
def write_file_result(result_dir: str, users_t_m: List[List[int]], distance_mn: List[List[float]], snr_map_mn: List[List[float]], min_sinr_w: float,
                      antennas_regions_byslice: List[List[int]], connections_dict_byslice: List[dict]):
    
    mean = 0

    with open(genf.gen_solver_result_filename(result_dir, 'ga', math.ceil(linear_to_db(min_sinr_w))), 'w') as f:
        for t in range(len(antennas_regions_byslice)):
            mean += len(antennas_regions_byslice[t])
            print(f"t={t}")
            counter = {}
            mean_snr = {}
            total_users = {}
            for m in antennas_regions_byslice[t]:
                counter[m] = 0
                mean_snr[m] = 0
                total_users[m] = 0
            for n in connections_dict_byslice[t]:
                m = connections_dict_byslice[t][n]
                counter[m]+=1
                mean_snr[m]+=snr_map_mn[m][n]
                total_users[m]+=users_t_m[t][n]
                "$y_{%d,%d,%d}$"%(t,m,n)
                print(f"\t y_{t},{m},{n} = {10*math.log10(snr_map_mn[m][n])} dB")
                f.write("{t} {m} {n}\n".format(t= t, m= m, n= n))
                if counter[m] > 0 :
                    print("\t\tSNR medio:", 10*math.log10(mean_snr[m]/counter[m]))
                print("\t\tUsuarios totais:", total_users[m])
            print("Distances:")
            for i in antennas_regions_byslice[t]:
                for j in antennas_regions_byslice[t]:
                    if i < j :
                        print(f"{i} : {j} = {distance_mn[i][j]}")
        print("\nMédia de carros:", mean/len(antennas_regions_byslice))

        f.write("--- Done ---\n")

if __name__ == '__main__':
    main()