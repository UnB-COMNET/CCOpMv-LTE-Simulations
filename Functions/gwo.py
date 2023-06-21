import re
import numpy as np
from typing import List
import geometry as geo
import coordinates as coord
from helper_xml import get_map_ues_time
import general_functions as genf
from time import time
import sinr_comput as sc
import random
import copy    
import math

STR_PGWO_1 = 'pgwo1'
STR_PGWO_2 = 'pgwo2'

# wolf class
class wolf:
    def __init__(self, antennas_regions: List[int], users_regions: List[int], dimension: int, scenario: geo.MapChess, seed: int, id: int, fitness_func = None):
        self.id = id
        self.seed = seed
        self.rnd = random.Random(seed)
        self.fitness_func = fitness_func
        self.position = [0 for i in range(dimension)]
        self.min_x = 0
        self.min_y = 0
        self.scenario = scenario
        self.max_x = scenario.size_x
        self.max_y = scenario.size_y
        
        # Wolf is created with a random position
        for i in range(dimension):
            self.position[i] =  coord.Coordinate((self.max_x - self.min_x) * self.rnd.random() + self.min_x,
                                                 (self.max_y - self.min_y) * self.rnd.random() + self.min_y)
            
        if dimension != 0 and fitness_func != None:#TODO evitar calcular a fitness na hora de criar o _wolf. Apenas atualizar depois
            self.fitness = self.fitness_func(self.position, antennas_regions, users_regions, self.scenario)
            """
            if self.fitness_func == fitness_gwo_cov:
                self.fitness = self.fitness_func(self.position, antennas_regions, users_regions, self.scenario)
            else:
                self.fitness = self.fitness_func(self.position, antennas_regions, users_regions, self.scenario)
                #self.fitness, self.fitness_snr = self.fitness_func(self.position, antennas_regions, users_regions, self.scenario)
            """

    def setPosition(self, index, x, y):
        self.position[index] = coord.Coordinate(x,y)

    def updateFitness(self, antennas_regions, users_regions): 
        self.fitness = self.fitness_func(self.position, antennas_regions, users_regions, self.scenario)            

    def setFitnessFunction(self, fitness_func):
        self.fitness_func = fitness_func

    def __str__(self) -> str:
        try:
            str = f'Wolf {self.id} ({self.seed}). Fitness: {self.fitness}, {self.fitness_snr}'
        except(AttributeError):
            str = f'Wolf {self.id} ({self.seed}). Fitness: {self.fitness}'
        
        for i in range(len(self.position)):
            str += f'\n\t{self.position[i]}. Region: {geo.coord2Region(self.position[i], self.scenario.size_sector, self.scenario.size_x, self.scenario.size_y)}'
        
        return str

    def __eq__(self, other):
        result = True
        for region in list(map(lambda self_region: geo.coord2Region(self_region, self.scenario.size_sector, self.scenario.size_x, self.scenario.size_y), self.position)):
            if not region in list(map(lambda other_region: geo.coord2Region(other_region, self.scenario.size_sector, self.scenario.size_x, self.scenario.size_y), other.position)):
                result = False
                return result

        return result

# Global variables
_users_t_m = []
_users_m = []
_antennas_last_result = []
_distance_mn = []
_snr_map_mn = []
_min_sinr_w = 0
_min_dis = 0
_first_antenna_region = 0
_max_users_per_antenna_m = []
_last_antennas_regions = []
_map_of_service = []
_antennasmap_m = []
_connection_results = []

def main():
    #General configs
    chosen_seeds = [2]
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

    return
    run(chosen_seeds=chosen_seeds, size_x= size_x, size_y=size_y, size_sector=size_sector, n_macros=n_macros,
                   move_config_name=move_config_name, result_dir=result_dir, min_sinr=min_sinr, num_slices=num_slices, #mode=mode,
                   extra_dir=extra_dir, micro_power= micro_power, min_dis= min_dis,
                   disaster_percentage= disaster_percentage) #Disaster as an extra argument in **kwargs to use with extra_dir

def run(chosen_seeds: List[int], size_x: int, size_y: int, size_sector: int,n_macros: int, move_config_name: str,
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
        
        full_result_dir = result_dir + f'/chosen_seed_{chosen_seed}'

        #Initiating scenario
        scen = geo.MapChess(size_y = size_y, size_x = size_x, size_sector = size_sector, carrier_frequency= 0.7, chosen_seed= chosen_seed, scenario= "URBAN_MICROCELL" if is_micro else "URBAN_MACROCELL",
                            enb_tx_power= micro_power if is_micro else 46, h_enbs= 18, gain_ue= -1, enb_noise_figure= 9, num_slices= num_slices)

        #Placing UEs
        scen.placeUEs(type= "Random", n_macros= n_macros, n_ues_macro= 60)

        xml_filename = genf.gen_movement_filename(move_config_name, chosen_seed, snapshot= True)

        distance_mn = scen.getRegionsDistanceMatrix()
        
        lambda_poisson_gen_users_t_m = 30
        users_t_m = genf.gen_users_t_m(chosen_seed, lambda_poisson = lambda_poisson_gen_users_t_m, num_slices=num_slices)             
        #ues_per_slice = genf.gen_ue_per_slice(chosen_seed, users_t_m, num_slices=num_slices)
        ues_per_slice = [[60, 152, 140, 33, 96, 159, 124, 167, 154, 16, 164, 3, 126, 70, 150, 63, 52, 130, 151, 156, 132, 109, 41, 66, 42, 153, 111, 4, 19, 47, 12, 91, 9, 83, 146, 119, 134, 122],
                        [60, 152, 140, 33, 96, 159, 124, 167, 154, 16, 164, 3, 126, 70, 150, 63, 52, 130, 151, 156, 132, 109, 41, 66, 42, 153, 111, 4, 19, 47, 12, 91, 9, 83, 146, 119, 134, 122, 141, 43, 114, 30, 13, 46, 170, 74, 87, 148, 101, 144, 179, 131, 117, 90, 99, 71, 102, 38, 172, 59, 125, 177, 5, 168, 51, 112],
                        [60, 152, 140, 33, 96, 159, 124, 167, 154, 16, 164, 3, 126, 70, 150, 63, 52, 130, 151, 156, 132, 109, 41, 66, 42, 153, 111, 4, 19, 47, 12, 91, 9, 83, 146, 119, 134, 122, 141, 43, 114, 30, 13, 46, 170, 74, 87, 148, 101, 144, 179, 131, 117, 90, 99, 71, 102, 38, 172, 59, 125, 177, 5, 168, 51, 112, 128, 137, 28, 139, 62, 104, 110, 108, 21, 158, 138, 40, 136, 118, 55, 58, 24, 14, 100, 157, 103, 20, 78, 15, 92, 35, 2, 73, 105, 98, 31, 10],
                        [60, 152, 140, 33, 96, 159, 124, 167, 154, 16, 164, 3, 126, 70, 150, 63, 52, 130, 151, 156, 132, 109, 41, 66, 42, 153, 111, 4, 19, 47, 12, 91, 9, 83, 146, 119, 134, 122, 141, 43, 114, 30, 13, 46, 170, 74, 87, 148, 101, 144, 179, 131, 117, 90, 99, 71, 102, 38, 172, 59, 125, 177, 5, 168, 51, 112, 128, 137, 28, 139, 62, 104, 110, 108, 21, 158, 138, 40, 136, 118, 55, 58, 24, 14, 100, 157, 103, 20, 78, 15, 92, 35, 2, 73, 105, 98, 31, 10, 173, 175, 11, 95, 174, 85, 165, 76, 155, 67, 8, 86, 0, 27, 37, 18, 68, 143, 94, 107, 49, 32, 129, 7, 171, 65, 64, 77],
                        [60, 152, 140, 33, 96, 159, 124, 167, 154, 16, 164, 3, 126, 70, 150, 63, 52, 130, 151, 156, 132, 109, 41, 66, 42, 153, 111, 4, 19, 47, 12, 91, 9, 83, 146, 119, 134, 122, 141, 43, 114, 30, 13, 46, 170, 74, 87, 148, 101, 144, 179, 131, 117, 90, 99, 71, 102, 38, 172, 59, 125, 177, 5, 168, 51, 112, 128, 137, 28, 139, 62, 104, 110, 108, 21, 158, 138, 40, 136, 118, 55, 58, 24, 14, 100, 157, 103, 20, 78, 15, 92, 35, 2, 73, 105, 98, 31, 10, 173, 175, 11, 95, 174, 85, 165, 76, 155, 67, 8, 86, 0, 27, 37, 18, 68, 143, 94, 107, 49, 32, 129, 7, 171, 65, 64, 77, 34, 81, 82, 106, 121, 84, 161, 147, 169, 135, 26, 163, 127, 61, 115, 56, 79, 123, 69, 176, 88, 97, 1, 145, 54, 93, 48, 6],
                        [60, 152, 140, 33, 96, 159, 124, 167, 154, 16, 164, 3, 126, 70, 150, 63, 52, 130, 151, 156, 132, 109, 41, 66, 42, 153, 111, 4, 19, 47, 12, 91, 9, 83, 146, 119, 134, 122, 141, 43, 114, 30, 13, 46, 170, 74, 87, 148, 101, 144, 179, 131, 117, 90, 99, 71, 102, 38, 172, 59, 125, 177, 5, 168, 51, 112, 128, 137, 28, 139, 62, 104, 110, 108, 21, 158, 138, 40, 136, 118, 55, 58, 24, 14, 100, 157, 103, 20, 78, 15, 92, 35, 2, 73, 105, 98, 31, 10, 173, 175, 11, 95, 174, 85, 165, 76, 155, 67, 8, 86, 0, 27, 37, 18, 68, 143, 94, 107, 49, 32, 129, 7, 171, 65, 64, 77, 34, 81, 82, 106, 121, 84, 161, 147, 169, 135, 26, 163, 127, 61, 115, 56, 79, 123, 69, 176, 88, 97, 1, 145, 54, 93, 48, 6, 72, 142, 133, 162, 29, 22, 75, 120, 89, 113, 53, 149, 50, 17, 160, 23, 25, 80, 57, 166, 45, 44, 116, 36, 178, 39],
                        [60, 152, 140, 33, 96, 159, 167, 154, 16, 164, 3, 126, 70, 150, 63, 52, 130, 151, 156, 132, 41, 66, 42, 4, 19, 12, 91, 9, 83, 146, 134, 122, 141, 43, 114, 30, 13, 46, 170, 74, 87, 148, 144, 131, 117, 90, 99, 71, 102, 38, 172, 125, 177, 5, 168, 28, 139, 62, 104, 110, 21, 158, 138, 136, 118, 58, 24, 14, 100, 103, 20, 78, 15, 92, 35, 2, 105, 31, 173, 175, 95, 85, 165, 76, 155, 8, 86, 0, 27, 37, 18, 68, 143, 94, 107, 49, 32, 129, 7, 171, 65, 64, 34, 81, 82, 106, 121, 84, 147, 169, 135, 26, 127, 61, 115, 56, 79, 123, 69, 176, 88, 97, 1, 145, 54, 93, 6, 142, 133, 162, 29, 22, 75, 120, 89, 113, 53, 149, 50, 17, 160, 23, 25, 80, 57, 45, 44, 116, 36, 178, 39],
                        [60, 152, 140, 33, 159, 167, 154, 164, 3, 126, 70, 150, 63, 52, 130, 151, 156, 132, 41, 4, 19, 12, 91, 9, 83, 122, 141, 43, 114, 30, 46, 170, 74, 87, 148, 144, 131, 117, 90, 99, 71, 38, 125, 177, 5, 168, 28, 139, 104, 21, 138, 136, 118, 58, 24, 14, 100, 20, 78, 15, 92, 35, 2, 105, 175, 95, 85, 155, 0, 27, 37, 18, 68, 143, 94, 107, 32, 129, 171, 65, 64, 81, 82, 106, 121, 84, 147, 169, 135, 26, 127, 61, 115, 79, 123, 69, 176, 97, 1, 54, 93, 142, 133, 162, 29, 22, 75, 120, 113, 53, 149, 50, 17, 23, 80, 57, 44, 116, 36, 39],
                        [152, 140, 33, 159, 154, 164, 3, 126, 150, 63, 52, 130, 151, 156, 132, 4, 19, 12, 91, 9, 83, 122, 141, 43, 114, 46, 170, 87, 148, 144, 131, 90, 71, 38, 177, 5, 168, 28, 104, 21, 138, 136, 118, 58, 24, 14, 20, 78, 15, 92, 35, 175, 95, 85, 0, 27, 37, 18, 68, 94, 32, 129, 171, 64, 82, 106, 121, 84, 147, 169, 135, 26, 61, 115, 123, 69, 176, 1, 54, 93, 142, 133, 162, 22, 75, 149, 50, 17, 23, 80, 44, 116, 36, 39],
                        [152, 33, 3, 126, 63, 52, 151, 156, 132, 4, 19, 12, 91, 83, 141, 43, 46, 148, 144, 131, 90, 71, 38, 177, 5, 168, 104, 21, 138, 136, 118, 58, 20, 78, 15, 92, 35, 175, 95, 85, 0, 37, 18, 94, 32, 129, 171, 82, 106, 121, 169, 135, 26, 61, 115, 69, 176, 1, 93, 142, 133, 22, 149, 50, 17, 23, 80, 116, 36],
                        [33, 3, 126, 52, 151, 4, 12, 83, 141, 43, 148, 144, 90, 71, 177, 168, 138, 58, 20, 78, 15, 35, 175, 85, 0, 37, 94, 129, 82, 106, 169, 135, 69, 176, 1, 142, 17, 80, 116],
                        [3, 141, 71, 78, 175, 69, 17, 80, 116]]
        project_dir = '../Network_CCOpMv'
        sim_dir = '_5G/simulations'

        users_t_m = get_map_ues_time(scen= scen, xml_filename= xml_filename, ues_per_slice = ues_per_slice)

        snr_map_mn = scen.getSinrMap()

        max_users_antenna_m = [60 for i in range(scen.n_sectors)]

        first_antenna_region = genf.gen_first_antenna_region(chosen_seed=chosen_seed, n_sectors=scen.n_sectors)
        result = pgwo_solver(num_regions=scen.n_sectors, users_t_m=users_t_m, distance_mn=distance_mn, snr_map_mn=snr_map_mn, fitness_func=fitness_gwo,
                           first_antenna_region=first_antenna_region, num_slices=num_slices, min_dis=min_dis, min_sinr_w= min_sinr_w, max_users_per_antenna_m=max_users_antenna_m,
                           result_dir= full_result_dir)
        results.append(result)

def pgwo_solver(scenario: geo.MapChess, num_regions: int, users_t_m: List[List[int]], distance_mn: List[List[float]], snr_map_mn: List[List[float]],
              antennasmap_m: List[int], first_antenna_region: int, num_slices: int, min_dis: int, min_sinr_w: float, max_users_per_antenna_m: List[int],
              result_dir: str, max_dimension: int = 10, pack_size: int = 300, max_iter: int = 200, version: str = STR_PGWO_2):
    results = []
    
    #TODO: ver as variaveis globais
    
    global _snr_map_mn
    global _min_sinr_w
    global _max_users_per_antenna_m
    global _antennasmap_m
    global _users_t_m
    global _users_m
    global _distance_mn
    global _min_dis
    global _first_antenna_region
    global _map_of_service

    _snr_map_mn = snr_map_mn
    _min_sinr_w = min_sinr_w
    _max_users_per_antenna_m = max_users_per_antenna_m
    _antennasmap_m = antennasmap_m
    _users_t_m = users_t_m
    _distance_mn = distance_mn
    _min_dis = min_dis
    _first_antenna_region = first_antenna_region   
    _map_of_service = []
    
    # mapa de usuários totais: TODO transformar em função get_visited_regions
    _users_m = num_regions*[0]
    for m in range(num_regions):
        for t in range(num_slices):
            if users_t_m[t][m] > 0:
                _users_m[m] = 1
    
    if version == STR_PGWO_1:
        fitness_func = fitness_pgwo1
    elif version == STR_PGWO_2:
        fitness_func = fitness_pgwo2
    
    antennas_map = [0 if m != first_antenna_region else 1 for m in range(num_regions)]

    for i in range(num_slices):
        print("\nSlice ", i)
        _users_t_m = users_t_m[i:]

        # Checks if the scenario needs more antenna to meet requisites
        antennas_regions = np.ravel(np.argwhere(np.array(antennas_map) > 0))
        users_regions = np.ravel(np.argwhere(np.array(_users_t_m[0]) > 0))
        
        dimension = len(antennas_regions) #TODO Refactore dimension to 2*num_antennas, i.e., (x,y) pairs

        #TODO Evitar calcular a fitness sem necessidade na hora de criar o lobo
        _wolf = wolf(antennas_regions, users_regions, dimension, scenario, None, None, None) # The wolf represents the current scenario
        for dim in range(dimension):
            coord = geo.region2Coord(antennas_regions[dim],scenario.size_sector, scenario.size_x, scenario.size_y)
            _wolf.setPosition(dim, coord.x, coord.y)
        _wolf.setFitnessFunction(fitness_func)
        _wolf.updateFitness(np.array([],dtype='int64'), users_regions)           # update fitness nao teve ter antenas já instaladas, pois _wolf já as implementa
                    
        print("Fitnes _wolf: ", _wolf.fitness)
        if _wolf.fitness == 0:                
            dimension = 1           
            while(dimension <= max_dimension):                
                solution = run_gwo(scenario, antennas_regions, users_regions, pack_size, dimension, max_iter, fitness_func)
                
                if solution.fitness != 0:
                    print("Best solution: ", solution)                    
                    #print(np.ravel(np.argwhere(np.array(antennas_map) > 0)))
                    for n in range(len(solution.position)):
                        antennas_map[geo.coord2Region(solution.position[n], scenario.size_sector, scenario.size_x, scenario.size_y)] = 1
                    print(f"Antennas in slice {i}: ", np.ravel(np.argwhere(np.array(antennas_map) > 0)))
                    results.append(np.ravel(np.argwhere(np.array(antennas_map) > 0)))
                    print("Results: ", results)
                    break
                elif dimension == max_dimension:
                    print("Not feasible")
                    return None
                
                dimension+=1           
        else:
            results.append(antennas_regions)
            print("The set of antennas serves the scenario in the respective slice.")
            print("Results: ", results)
        
        #NOTE: Ainda que a fitness do último alfa seja 1.0, é necessário continuar a verificar
        #      Por causa das outras restrições
    
    print("Results: ", results)
    
    # Writing the log and result files
    with open(genf.gen_solver_result_filename(result_dir, 'pgwo', math.ceil(sc.linear_to_db(min_sinr_w))), 'w') as f:
        num_vehicles = 0
        for i in range(num_slices):
            num_vehicles += len(results[i])
        
        print("\nMédia de carros:", num_vehicles/num_slices)

        for t in range(0,num_slices):
            print("t=%d"%t)    
            antennas_regions = results[t]
            users_regions = np.ravel(np.argwhere(np.array(users_t_m[t]) > 0))
            print("Antennas:", antennas_regions)
            print("Users:", users_regions)
            connections = genf.get_dict_of_connections(antennas_regions, users_regions, users_t_m[t],_snr_map_mn, _min_sinr_w, _max_users_per_antenna_m)
            for antenna in antennas_regions:
                print(f"$x_{{{t},{antenna}}}$")
                users_regions = [key for key, value in connections.items() if value == antenna]
                num_users = 0
                mean_snr = 0
                for region in users_regions:
                    snr = sc.linear_to_db(_snr_map_mn[antenna][region])
                    print(f"\t $y_{{{t},{antenna},{region}}}$ = {snr} dB")
                    mean_snr += snr
                    num_users += users_t_m[t][region]
                    f.write(f"{t} {antenna} {region}\n")
                
                if len(users_regions) > 0:
                    mean_snr /= num_users
                    print("\t\tSNR medio: ", mean_snr)
                print("\t\tUsuarios totais:", num_users)

                if num_users == 0:
                    f.write(f"{t} {antenna} -1\n")
            
            print("Distances:")
            for i in antennas_regions:
                for j in antennas_regions:
                    if i < j :
                        print(f"{i} : {j} = {distance_mn[i][j]}")

        f.write("--- Done ---\n")

    return results
 
def run_gwo(scenario: geo.MapChess, antennas_regions: List[int], users_regions: List[int], pack_size: int, wolf_dimension: int, max_iter: int, fitness_func):
    print(f"\nRun GWO to deployment +{wolf_dimension} antenna on the map")
    print("\tPack size: ", pack_size)
    print("\tWolf dimension", wolf_dimension)
    print("\tMax iter", max_iter)
    print("\tantennas_regions: ", antennas_regions)
    print("\tusers_regions: ", users_regions)
    print("\tFitness function: ", fitness_func)
    rnd = random.Random()                    
    seed_base = rnd.randint(1000,100000)     
    print("\tSeed_base: ", seed_base)
    
    # NOTE: perde-se o controle das seeds utilizadas para gerar a populacao inicial do GWO
    
    # create n random wolves
    population = [wolf(antennas_regions, users_regions, wolf_dimension, scenario, seed_base + i, i, fitness_func) for i in range(pack_size)]
        
    rnd = random.Random(scenario.chosen_seed)

    population = sorted(population, key = lambda temp: temp.fitness, reverse=True)

    # alpha, beta and delta wolves
    alpha_wolf, beta_wolf, delta_wolf = copy.copy(population[: 3])
    print("initial_alpha: ", alpha_wolf)
    print("initial_beta: ", beta_wolf)
    print("initial_delta: ", delta_wolf, "\n")
    
    wolf_list = []
    iter = 0
    while iter < max_iter:
        verbose = True
        # after every 10 iterations
        # print iteration number and best fitness value so far
        if iter % 10 == 0 and iter > 1:
            print("iter = " + str(iter))
            print("Alpha wolf: ", alpha_wolf)
 
        # linearly decreased from 2 to 0
        a = 2*(1 - iter/max_iter)
        
        # updating each population member with the help of best three members
        for i in range(pack_size):
            Xnew:wolf = copy.deepcopy(population[i])                    #TODO REMOVE #X_new = population.copy()  
            if verbose == True and population[i].id in wolf_list: print("Updating wolf ", i)
            if verbose == True and population[i].id in wolf_list: print(population[i])
            A1 = list(map(lambda r1: 2*a*r1 - a, [rnd.random() for _ in range(2*wolf_dimension)]))
            A2 = list(map(lambda r1: 2*a*r1 - a, [rnd.random() for _ in range(2*wolf_dimension)]))
            A3 = list(map(lambda r1: 2*a*r1 - a, [rnd.random() for _ in range(2*wolf_dimension)]))

            C1 = list(map(lambda r2: 2*r2, [rnd.random() for _ in range(2*wolf_dimension)]))
            C2 = list(map(lambda r2: 2*r2, [rnd.random() for _ in range(2*wolf_dimension)]))
            C3 = list(map(lambda r2: 2*r2, [rnd.random() for _ in range(2*wolf_dimension)]))

            if verbose == True and population[i].id in wolf_list: print("A1 ", A1)
            if verbose == True and population[i].id in wolf_list: print("A2 ", A2)
            if verbose == True and population[i].id in wolf_list: print("A3 ", A3)
            if verbose == True and population[i].id in wolf_list: print("C1 ", C1)
            if verbose == True and population[i].id in wolf_list: print("C2 ", C2)
            if verbose == True and population[i].id in wolf_list: print("C3 ", C3)            
            X1 = [coord.Coordinate(0.0, 0.0) for i in range(wolf_dimension)]
            X2 = [coord.Coordinate(0.0, 0.0) for i in range(wolf_dimension)]
            X3 = [coord.Coordinate(0.0, 0.0) for i in range(wolf_dimension)]
            
            for j in range(wolf_dimension):
                #TODO: verificar se o alfa, beta e gama tambem sao atualizados conforme os indices A e C
                if verbose == True and population[i].id in wolf_list: print(f"Atualizando x{j} e y{j}")
                X = population[i].position[j]
                if verbose == True and population[i].id in wolf_list: print("X: ", X)

                tmp = coord.Coordinate(C1[2*j]*alpha_wolf.position[j].x, C1[2*j+1]*alpha_wolf.position[j].y)
                tmp = tmp - X
                tmp = abs(tmp)
                tmp.setCoordinate(A1[2*j]*tmp.x, A1[2*j+1]*tmp.y)

                X1[j] = alpha_wolf.position[j] - tmp

                if verbose == True and population[i].id in wolf_list: print("X1: ", X1[j])

                tmp = coord.Coordinate(C2[2*j]*beta_wolf.position[j].x, C2[2*j+1]*beta_wolf.position[j].y)
                tmp = abs(tmp - X)
                tmp.setCoordinate(A2[2*j]*tmp.x, A2[2*j+1]*tmp.y)
                X2[j] = beta_wolf.position[j] - tmp
                if verbose == True and population[i].id in wolf_list: print("X2: ", X2[j])

                tmp = coord.Coordinate(C3[2*j]*delta_wolf.position[j].x, C3[2*j+1]*delta_wolf.position[j].y)
                tmp = abs(tmp - X)
                tmp.setCoordinate(A3[2*j]*tmp.x, A3[2*j+1]*tmp.y)
                X3[j] = delta_wolf.position[j] - tmp
                if verbose == True and population[i].id in wolf_list: print("X3: ", X3[j])

                #X_new[i].position[j] = X1[j] + X2[j] + X3[j]
                Xnew.position[j] = X1[j] + X2[j] + X3[j]
                Xnew.position[j] *= 1/3
                #X_new[i].position[j].scalarMultiply(1/3)

                if verbose == True and population[i].id in wolf_list: print("Xnew", Xnew.position[j])
                
                # Reflexion
                while Xnew.position[j].x < 0 or Xnew.position[j].x > scenario.size_x:
                    if Xnew.position[j].x < 0:
                        Xnew.position[j].x = -Xnew.position[j].x
                    else:
                        Xnew.position[j].x = 2*scenario.size_x - Xnew.position[j].x

                while Xnew.position[j].y < 0 or Xnew.position[j].y > scenario.size_y:
                    if Xnew.position[j].y < 0:
                        Xnew.position[j].y = -Xnew.position[j].y
                    else:
                        Xnew.position[j].y = 2*scenario.size_y - Xnew.position[j].y

                #if verbose == True and population[i].id in wolf_list: print("X ", if verbose == True and population[i].id in wolf_list: print(population[i].position[0]))
                #if verbose == True and population[i].id in wolf_list: print(A1[2*j], A1[2*j+1])
                #if verbose == True and population[i].id in wolf_list: print(C1[2*j], C1[2*j+1])
                if verbose == True and population[i].id in wolf_list: print("\n")
            
            #updating X_new fitness
            Xnew.updateFitness(antennas_regions, users_regions)
            if verbose == True and population[i].id in wolf_list: print("X: ", population[i])
            if verbose == True and population[i].id in wolf_list: print("X_new: ", Xnew)
            
            if Xnew.fitness >= population[i].fitness:
                #print(Xnew.fitness , population[i].fitness)
                if verbose == True and population[i].id in wolf_list: print("Achou uma solucao melhor:")
                population[i] = Xnew
                if verbose == True and population[i].id in wolf_list: print(population[i])

            if verbose == True and population[i].id in wolf_list: print("\n")

        population = sorted(population, key = lambda temp: temp.fitness, reverse=True)
        
        """
        print("populacao atualizada")
        for k in range(len(population)):
            print(population[k])
        print("--------")
        #"""
        # best 3 solutions: alpha, beta and delta
        last_alpha_wolf = alpha_wolf
        # escolhendo como alfa o que tiver maior fitness:
        alpha_wolf, beta_wolf, delta_wolf = copy.copy(population[: 3])

        if alpha_wolf.fitness != last_alpha_wolf.fitness:
            print(f"The alpha wolf has been updated to a position with higher fitness. iter = {iter}")
            print("New alpha wolf: ", alpha_wolf)
        
        iter += 1

    if alpha_wolf.fitness != 0: print("\n- Finishing GWO - \n")

    return alpha_wolf
           
 
#-------------------------
def problem_constraint_check(position, antennas_regions, users_regions, scenario: geo.MapChess, verbose:bool = False):
    global _map_of_service      # Por que tive que usar a palavra chave global aqui, mas não para o _antennasmap_m?
    installed_antennas = antennas_regions
    wolf_antennas = [geo.coord2Region(position[i], scenario.size_sector, scenario.size_x, scenario.size_y) for i in range(len(position))]
    
    if verbose: print("wolf_antennas", wolf_antennas, len(wolf_antennas))
    if verbose: print("installed_antennas", installed_antennas, len(installed_antennas))
    if verbose: print("antennas_regions: ", antennas_regions)
    if verbose: print("users_regions: ", users_regions)
    # Constraints:
    # There must not be more than one antenna in a sector
    # Checks if there is an item of installed_antennas already existing in wolf_antennas
    if any(elem in wolf_antennas for elem in installed_antennas):
        if verbose: print("\tlobo no mesmo setor que antena ja instalada")
        return False

    # Checks if there is duplicate item in wolf_antennas
    elif any(wolf_antennas.count(elem) > 1 for elem in wolf_antennas):
        if verbose: print("\tLobo com regiões duplicadas. Possivelmente ocorreu ao gerar aleatoriamente")
        return False

    #else:
    antennas_regions = np.concatenate((wolf_antennas,installed_antennas))
    
    # There is an antenna in a region forbidden
    # TODO: verificar se funciona por causa da variavel global
    for region in antennas_regions:
        if _antennasmap_m[region] == 0:
            if verbose: print("Antenna in a region forbidden")
            return False
    
    # Every antenna, except the first antenna, must be connected to a backhaul with at least one neighbor (distance < MIN_DIST)
    for i in antennas_regions:
        if i != _first_antenna_region:
            has_antenna_nearby = False
            for j in antennas_regions:
                if i != j:           
                    if _distance_mn[i][j] <= _min_dis:
                        has_antenna_nearby = True
                        break
        
            if not has_antenna_nearby:
                if verbose: print("Sem backhaul local")
                return False
    
    if verbose: print("Antennas_regions: ", antennas_regions)
    
    # An antenna must serve the sector where it is installed
    # The antennas have a maximum number of users
    # All sector must be served    
    connections, _map_of_service = genf.get_dict_of_connections(antennas_regions, users_regions,_users_t_m[0],_snr_map_mn, _min_sinr_w,
                                                               _max_users_per_antenna_m, return_map_of_service = True)
    
    if connections == None:
        if verbose: print("Não foi possivel estabelecer conexao com todos os usuarios.")
        return False
    if verbose: print("Todos usuários conectados: ", connections)
    
    return True

def fitness_pgwo1(position, antennas_regions, users_regions, scenario: geo.MapChess, verbose:bool = False):
    if(problem_constraint_check(position, antennas_regions, users_regions, scenario, verbose)):
        # Coverage
        # Fitness definition: sum(region covered by the current solution) / sum(regions with users during some slice of time)
        # Fitness is a number from 0 and 1, i.e., 0% and 100%
        score = 0
        for m in _map_of_service:
            if m != []:
                score += 1

        score /= sum(_users_m)
    else:
        score = 0
    
    return score

def fitness_pgwo2(position, antennas_regions, users_regions, scenario: geo.MapChess, verbose:bool = False):
    if(problem_constraint_check(position, antennas_regions, users_regions, scenario, verbose)):
        ##------------------
        pass
    else:
        score = 0
    return score

"""
def fitness_gwo(position, antennas_regions, users_regions, scenario: geo.MapChess, verbose:bool = False):
    Unsed
        #TODO: Remove
    
    #NOTE: quando tamanho de position for diferente de 0 posso obter as regioes do respectivo lobo para concatenar com antennas regions
    #if len(position) != 0:
    #verbose = True
    wolf_antennas = [geo.coord2Region(position[i], scenario.size_sector, scenario.size_x, scenario.size_y) for i in range(len(position))]
    if verbose: print("wolf_antennas", type(wolf_antennas), wolf_antennas, len(wolf_antennas))
    if verbose: print("antennas_regions", type(antennas_regions), antennas_regions, len(antennas_regions))
    
    for i in range(len(position)):
        # TODO: verificar caso que uma antena do lobo coincide com uma já instalada
        if wolf_antennas[i] in antennas_regions:
            if verbose: print("\tlobo no mesmo setor que antena ja instalada")
            score = 0
            return score

        antennas_regions = np.append(antennas_regions,wolf_antennas[i]) #np.append(antennas_regions, wolf_antennas[i])
    
    for region in antennas_regions:
        if _antenasmap_m[region] == 0:
            if verbose: print('\tLobo possui uma das antenas em local restrito')
            score = 0
            return score

    #antennas_regions = np.append(antennas_regions, wolf_antennas)
    if verbose: print("antennas_regions", antennas_regions)
    #antennas_regions.append(wolf_antennas)
    
    #print(users_regions)
    _map_of_service = genf.get_map_of_service(antennas_regions,_snr_map_mn, minimization=False, threshold = False)
    if verbose == True: print(map_of_service)
    #print("snr_map[7]", _snr_map_mn[7])
    #print("snr_map[11", _snr_map_mn[11])
    score = 0
    for region in users_regions:
        snr_region = _snr_map_mn[int(map_of_service[region])][region]
        #if map_of_service[region] == '72':
        #    print('\tusuario na regiao ', region, " e servido pela antena instalada em ", map_of_service[region], "com snr ", snr_region)
        #print("limiar é ", _min_sinr_w)
        # TODO: considerar o min_snr_map
        if(snr_region < _min_sinr_w):
            # constraint: user shall be served with SNR greater than minimum SNR
            if verbose == True: print(f"\tUsuario em {region} e melhor servido pela antena {map_of_service[region]} com SNR {snr_region},\n\
                                        mas o limiar é {_min_sinr_w}")
            if verbose == True: print("\tSNR min nao atendido")

            return 0
        
        score += pow(snr_region - _min_sinr_w,2)

    #score = sqrt(score/len(users_regions))
    score = math.sqrt(score/sum(_users_t_m[0]))
    
    return score
"""     
if __name__ == "__main__": 
    main()