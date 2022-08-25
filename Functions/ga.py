# Import the necessary modules and libraries
from typing_extensions import Self
import numpy as np
from typing import List, Callable, Union
import geometry as geo
from helper_xml import get_map_ues_time
import general_functions as genf
import pygad
from time import time, localtime, mktime
from datetime import datetime
import sinr_comput as sc
import random

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

        max_users_antenna_m = [60 for i in range(scen.n_sectors)]

        optimized_byslice, antennas_regions_byslice, num_enbs_time = genf.parse_results_per_slice(genf.gen_solver_result_filename(full_result_dir, mode, min_sinr), num_slices)

        if optimized_byslice == None and antennas_regions_byslice == None and num_enbs_time == None:
            #There was a not feasible solution
            print(f'\nNot feasable solution in case: Seed {chosen_seed}, Mode: traditional (single). Ignoring this case.\n')
            continue

        antennas_m = [0 for _ in range(num_sectors)]
        for region in antennas_regions_byslice[-1]:
            antennas_m[region] = 1

        first_antenna_region = genf.gen_first_antenna_region(chosen_seed=chosen_seed, n_sectors=scen.n_sectors)
        print(f'Seed: {chosen_seed}. First Antenna Region: {first_antenna_region}.')

        result = ga_solver(traditional_antennas_map=antennas_m, users_t_m=users_t_m, distance_mn=distance_mn, snr_map_mn=snr_map_mn, fitness_func=fitness,
                           first_antenna_region=first_antenna_region, num_slices=num_slices, min_dis=min_dis, min_sinr_w= min_sinr_w, max_users_per_antenna_m=max_users_antenna_m)
        results.append(result)

        print(f'Done after {(time() - start_time)/(60*60)} hours. (Seed: {chosen_seed})')

        #print(f'\n{full_result_dir}')
        #print(antennas_regions_byslice[-1])
        #scen.placeAntennas(antennas_regions_byslice[-1])
        #genf.plot_scenario(scen= scen, title= f'{full_result_dir}')

def ga_solver(traditional_antennas_map: List[int], users_t_m: List[List[int]], distance_mn: List[List[float]], snr_map_mn: List[List[float]], fitness_func: Callable[..., float],
              first_antenna_region: int, num_slices: int, min_dis: int, min_sinr_w: float, max_users_per_antenna_m: List[int]):

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
    global _max_users_per_antenna_m
    _max_users_per_antenna_m = max_users_per_antenna_m

    num_regions = len(traditional_antennas_map)

    global _antennas_last_result
    _antennas_last_result = [ 0 if m != first_antenna_region else 1 for m in range(num_regions)]

    for i in range(num_slices):
        
        print(f'\nStarting GA of slice {i}.\n')

        global _users_t_m
        _users_t_m = users_t_m[i:]

        if i == 0:
            #antennas_regions = run_genetic(traditional_antennas_map, fitness_func, callback_gen)
            _antennas_last_result = traditional_antennas_map #Update last slice result
            continue
            #Not running GA for slice 0
        else:
            antennas_regions = run_genetic(_antennas_last_result, fitness_func, callback_gen)

        #antennas_regions = run_genetic(traditional_antennas_map, fitness_func)

        antennas_m = [0 for _ in range(num_regions)]

        for region in antennas_regions:
            antennas_m[region] = 1

        _antennas_last_result = antennas_m #Update last slice result

        antennas_regions_byslice.append(antennas_regions)

        # After having the result, get the connections using the run_genetic_connections again.
        # The result may not be the same but it will obey the contraints. Valid because the fitness value is 0 or 1, not optimizing the SINR.

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
    crossover_type = "uniform"#"two_points"

    """
    Type of the mutation operation. Supported types are random (for random mutation), 
    swap (for swap mutation), 
    inversion (for inversion mutation), 
    scramble (for scramble mutation), 
    and adaptive (for adaptive mutation).
    """
    mutation_type = "random" 
    mutation_by_replacement = True #Works with random mutation
    random_mutation_min_val = 0
    random_mutation_max_val = 1

    num_generations = 100
    num_parents_mating = 4 # Número de pais a serem selecionados

    population_size = 100 # Tamanho da população

    num_genes = len(base_genome)

    #colocar solução valida
    
    keep_parents = -1#All? #2 # Nr de indivíduos que serão selecionados para a próxima geração sem sofrer crossover nem mutação

    mutation_percent_genes = 10 #% de porcentagem dos genes a mutar
    #mutation_probability = 0.2 # chance de ocorrer a mutação em um gene (entre 0 e 1)
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
                        #mutation_probability=mutation_probability,
                        #mutation_num_genes= mutation_num_genes,
                        mutation_percent_genes=mutation_percent_genes,
                        mutation_by_replacement=mutation_by_replacement,
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
        return 0

    users_regions = np.ravel(np.argwhere(np.array(_users_t_m[0]) > 0))
    base_connections_genome = [map_of_service[n] for n in users_regions]
    global _last_antennas_regions
    _last_antennas_regions = antennas_regions
    connect_solution, connect_fitness_score = run_genetic_connections(base_genome=base_connections_genome, fitness_func=fitness_connections, gene_space=antennas_regions)

    global _connection_results
    _connection_results.append((connect_solution, solution_idx))

    return fitness_score * connect_fitness_score

def callback_gen(ga_instance):
    print("Generation : ", ga_instance.generations_completed)
    print("Fitness of the best solution :", ga_instance.best_solution()[1])

def create_population(base_genome, population_size):
    """Create the population of genomes.

    Returns:
        A List of List[int] where each List[int] represents a genome.
    """
    return[base_genome for _ in range(population_size)]

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
            
class Genome:

    def __init__(self, values: List[int]):
        self.values = values
        self.fitness = 0
        self.extra = {}

    def __str__(self):

        return f'(values: {self.values}, fitness: {self.fitness}, extra: {self.extra})'

class Population:

    def __init__(self, genomes: List[Genome]):

        if genomes == []:
            raise ValueError('genomes must be a Genome list with at least one object')

        self.genomes = genomes
        self.genomes.sort(key= lambda g : g.fitness, reverse= True) #Os com maior fitness primeiro

    def sort(self):

        self.genomes.sort(key= lambda g : g.fitness, reverse= True) #Os com maior fitness primeiro

        return self.genomes[0]

    def __str__(self):

        p = '['
        for genome in self.genomes:
            p += f'{genome},\n'
        p = p[:-2] + ']'

        return p

class AntennasGA:

    def __init__(self, initial_genome: List[int], num_generations: int, fitness_func: Callable[[List[int], int], Union[float, tuple]],
                 population_size: int = 100, elitism: int = 1, gene_space: List[int] = [0, 1], saturate: int = None, num_parents_mating: int = 2,
                 selection_type: str = 'truncation', crossover_type: str = 'two_points', crossover_probability: float = 0.2,
                 on_generation: Callable[[Self], None] = None):

        self.initial_genome = Genome(initial_genome)
        self.population_size = population_size
        self.curr_population = Population([self.initial_genome for _ in range(population_size)])
        self.num_generations = num_generations
        self.gene_space = gene_space
        self.fitness_func = fitness_func
        self.elitism = elitism
        self.best_solution = Genome(initial_genome)
        self.saturated_gens = 0
        self.saturate = saturate
        self.generations_completed = 0
        self.on_generation = on_generation
        self.num_parents_mating = num_parents_mating
        self.selection_type = selection_type
        self.crossover_type = crossover_type
        self.crossover_probability = crossover_probability if not crossover_probability > 1 else 1

    def run(self):
        self.curr_population= Population([Genome(list(map(lambda x: (x+1)%2 if (i%2) == 1 else x%2, self.initial_genome.values))) for i in range(self.population_size)])

        self._fitness() #Calculate new fitness values and update best_solution based on the initial_population

        for _ in range(self.num_generations):

            self._selection_and_crossover()
            #self._mutation()

            self._fitness()#Calculate new fitness values and update best_solution

            self.generations_completed += 1

            if self.on_generation is not None:
                self.on_generation(self)

            if self._stop_criteria():
                break
        


    def _fitness(self):
        
        count = 0

        #Update fitness results for each genome
        for genome in self.curr_population.genomes:
            result = self.fitness_func(genome.values, self.population_size*self.generations_completed + count)

            if type(result) == tuple:
                genome.fitness = result[0]
                genome.extra = result[1]
            else:
                genome.fitness = result

            count += 1

        #Sort the genomes based on their fitness value and return the best one
        self.best_solution = self.curr_population.sort()
    
    def _selection_and_crossover(self):
        selected = []

        #Selection

        #Truncation (select the best ones)
        if self.selection_type == 'truncation':
            if self.num_parents_mating < 2:
                #Para somente um parente o crossover vai gerar cópias dele.
                selected = 2*self.curr_population.genomes[:1]
            else:
                selected = self.curr_population.genomes[:self.num_parents_mating]
        else:
            raise ValueError('selection_type deve ser "truncation"')

        #Crossover

        #Each genome excluding the best defined by elitism
        for genome in self.curr_population.genomes[self.elitism:]:

            #Check probability
            if random.random() < self.crossover_probability:
                
                parents = random.sample(selected, 2)

                #Two-points crossover
                if self.crossover_type == "two_points":
                    point1 = random.randint(1, self.population_size - 1)
                    point2 = random.randint(1, self.population_size - 2)
                    #Making sure point2 > point1
                    if point2 >= point1:
                        point2 += 1
                    else:  # Swap the two points
                        point1, point2 = point2, point1

                    genome.values[:point1] = parents[0].values[:point1]
                    genome.values[point1:point2] = parents[1].values[point1:point2]
                    genome.values[point2:] = parents[0].values[point2:]

                #Single-point crossover
                elif self.crossover_type == "one_point":
                    point = random.randint(1, self.population_size - 1)
                    genome.values[:point] = parents[0].values[:point]
                    genome.values[point:] = parents[1].values[point:]

                else:
                    raise ValueError('crossover_type deve ser "two_points" ou "single_point"')         

    def _stop_criteria(self):

        #Se chegar no limite da gerações
        if self.generations_completed >= self.num_generations:
            return True
        
        #Se uma solução saturar
        elif self.saturate != None and self.saturated_gens >= self.saturate:
            return True

        else:
            return False

def test():
    ga = AntennasGA(initial_genome= [0,0,0,0,0,1,1,1,1,1], num_generations= 10, fitness_func= fit_test, on_generation= on_gen_test)
    ga.run()

def fit_test(genes, id):
    return np.sum(genes)

def on_gen_test(ga: AntennasGA):
    print(f'\nGeneration {ga.generations_completed}:\n{ga.curr_population}')

if __name__ == '__main__':
    test()
    #main()