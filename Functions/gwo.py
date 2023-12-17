import numpy as np
from typing import Callable, List, Optional
import geometry as geo
import coordinates as coord
import general_functions as genf
import sinr_comput as sc
import random
import copy    
import math

STR_PGWO_1 = 'pgwo1'
STR_PGWO_2 = 'pgwo2'
STR_PGWO_3 = 'pgwo3'

# Wolf class
class Wolf:
    """
        Represents a Wolf in a scenario.

        Attributes:
            id (int): The ID of the Wolf.
            seed (int): The seed used for random number generation.
            rnd (random.Random): The random number generator.
            fitness_func (Union[Callable, None]): The fitness function for the Wolf.
            min_x (int): The minimum value for the X coordinate.
            min_y (int): The minimum value for the Y coordinate.
            scenario (geo.MapChess): The scenario in which the Wolf exists.
            max_x (int): The maximum value for the X coordinate.
            max_y (int): The maximum value for the Y coordinate.
            position (List[coord.Coordinate]): The position of the Wolf.
            fitness (float): The fitness of the Wolf.

        Methods:
            setPosition(index: int, x: float, y: float) -> None:
                Set the position of the Wolf at a specified index.
            updateFitness(antennas_regions, users_regions) -> None:
                Update the fitness of the Wolf based on its current position.
            setFitnessFunction(fitness_func: Callable) -> None:
                Set the fitness function for the Wolf.
            __str__() -> str:
                Return a string representation of the Wolf object.
            __eq__(other: 'Wolf') -> bool:
                Check if two Wolves are equal based on their positions.
    """
    
    def __init__(self, antennas_regions: List[int], users_regions: List[int], dimension: int, scenario: geo.MapChess,
                 seed: int, id: int, fitness_func: Optional[Callable] = None):
        """
        Initializes a new instance of the Wolf class.

        Args:
            antennas_regions (List[int]): List of antenna regions.
            users_regions (List[int]): List of user regions.
            dimension (int): The dimension of the Wolf's position.
            scenario (geo.MapChess): The scenario in which the Wolf exists.
            seed (int): The seed used for random number generation.
            id (int): The ID that identifies the Wolf in the pack.
            fitness_func (Union[Callable,None]): The fitness function for the Wolf. Defaults to None.
        """
        self.id = id
        self.seed = seed
        self.rnd = random.Random(seed)
        self.fitness_func = fitness_func   
        self.min_x = 0
        self.min_y = 0
        self.scenario = scenario
        self.max_x = scenario.size_x
        self.max_y = scenario.size_y
        
        # Wolf is created with a random position
        self.position = [coord.Coordinate((self.max_x - self.min_x) * self.rnd.random() + self.min_x,
                         (self.max_y - self.min_y) * self.rnd.random() + self.min_y) for _ in range(dimension)]
        #for i in range(dimension):
        #    self.position[i] =  coord.Coordinate((self.max_x - self.min_x) * self.rnd.random() + self.min_x,
        #                                         (self.max_y - self.min_y) * self.rnd.random() + self.min_y)
        if dimension != 0 and fitness_func != None:
            self.fitness = self.fitness_func(self.position, antennas_regions, users_regions, self.scenario)

    def setPosition(self, index: int, x: float, y: float):
        """
            Set the position of the wolf. It requires the index of the position (a list of coordinates) that you want to set.\n
            It cannot define more than one index simultaneously.
             
            Args:
                index (int): 
                x (float): X-coordinate of the new position at the specified index\n
                y (float): Y-coordinate of the new position at the specified index
        """
        self.position[index] = coord.Coordinate(x,y)

    def updateFitness(self, antennas_regions, users_regions):
        """
            Update the wolf's fitness based on its current position.

            Args:
                antennas_regions: 
                users_regions: 
        """
        self.fitness = self.fitness_func(self.position, antennas_regions, users_regions, self.scenario)            

    def setFitnessFunction(self, fitness_func: Callable):
        """
            Set the fitness function for the Wolf. 

            Args:
                fitness_func (Callable): The fitness function to be set for the Wolf.
        """
        self.fitness_func = fitness_func

    def __str__(self) -> str:
        """
            Returns a string representation of the Wolf object, including its ID, seed, fitness and position. The position is shown as a list of regions.

            Returns:
                str: String representation of the Wolf object.
        """
        try:
            str = f'Wolf {self.id} ({self.seed}). Fitness: {self.fitness}, {self.fitness_snr}'
        except(AttributeError):
            str = f'Wolf {self.id} ({self.seed}). Fitness: {self.fitness}'
        
        for i in range(len(self.position)):
            str += f'\n\t{self.position[i]}. Region: {geo.coord2Region(self.position[i], self.scenario.size_sector, self.scenario.size_x, self.scenario.size_y)}'
        
        return str

    def __eq__(self, other: 'Wolf') -> bool:
        """
            Checks if two wolves are equal based on their positions. The wolves are equal if they have exactly the same position.

            Args:
                other (wolf): The second wolf to compare.

            Return:
                bool: True if the wolves have the same position, False otherwise.
        """
        result = True
        for region in list(map(lambda self_region: geo.coord2Region(self_region, self.scenario.size_sector, self.scenario.size_x, self.scenario.size_y), self.position)):
            if not region in list(map(lambda other_region: geo.coord2Region(other_region, self.scenario.size_sector, self.scenario.size_x, self.scenario.size_y), other.position)):
                result = False
                return result

        return result

def pgwo_solver(scenario: geo.MapChess, num_regions: int, users_t_m: List[List[int]], distance_mn: List[List[float]], snr_map_mn: List[List[float]],
              antennasmap_m: List[int], first_antenna_region: int, num_slices: int, min_dis: int, min_sinr_w: float, max_users_per_antenna_m: List[int],
              result_dir: str, max_dimension: int = 10, pack_size: int = 300, max_iter: int = 200, version: str = STR_PGWO_2):
    """
        Solves the problem using the PGWO (Progressive Grey Wolf Optimizer) algorithm.
        The algorithm runs GWO (Grey Wolf Optimizer) successively with increasing dimension in order to get a valid solution.
        The stopping criterion is given by the parameter max_dimension.

        Args:
            scenario (geo.MapChess): The scenario to be solved.
            num_regions (int): The number of regions in the scenario.
            users_t_m (List[List[int]]): The number of users in each region for each time slice.
            distance_mn (List[List[float]]): The distances between regions.
            snr_map_mn (List[List[float]]): The SNR (Signal-to-Noise Ratio) map between regions.
            antennasmap_m (List[int]): The map of antennas in the scenario.
            first_antenna_region (int): The region of the first antenna.
            num_slices (int): The number of time slices.
            min_dis (int): The minimum distance between antennas.
            min_sinr_w (float): The minimum SINR (Signal-to-Interference-plus-Noise Ratio) requirement.
            max_users_per_antenna_m (List[int]): The maximum number of users per antenna.
            result_dir (str): The directory to save the result files.
            max_dimension (int, optional): The maximum dimension for the solution. Defaults to 10.
            pack_size (int, optional): The pack size for the GWO (Gray Wolf Optimization) algorithm. Defaults to 300.
            max_iter (int, optional): The maximum number of iterations for the GWO algorithm. Defaults to 200.
            version (str, optional): The version of the PGWO algorithm to use. Defaults to STR_PGWO_2, i.e., "pgwo2".

        Returns:
            List[List[int]]: A list of lists representing the antennas selected for each time slice.

    """
    results = []
    
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
    
    # 
    _users_m = num_regions*[0]
    for m in range(num_regions):
        for t in range(num_slices):
            if users_t_m[t][m] > 0:
                _users_m[m] = 1
    
    if version == STR_PGWO_1:
        fitness_func = fitness_pgwo1
    elif version == STR_PGWO_2:
        fitness_func = fitness_pgwo2
    elif version == STR_PGWO_3:
        fitness_func = fitness_pgwo3
    
    antennas_map = [0 if m != first_antenna_region else 1 for m in range(num_regions)]
    seed_base = 0
    for i in range(num_slices):
        print("\nSlice", i)
        _users_t_m = users_t_m[i:]

        # Checks if the scenario needs more antenna to meet requisites
        antennas_regions = np.ravel(np.argwhere(np.array(antennas_map) > 0))
        users_regions = np.ravel(np.argwhere(np.array(_users_t_m[0]) > 0))
        
        dimension = len(antennas_regions) #TODO Refactore dimension to 2*num_antennas, i.e., (x,y) pairs

        _wolf = Wolf(antennas_regions, users_regions, dimension, scenario, None, None, None) # The wolf represents the current scenario
        for dim in range(dimension):
            coord = geo.region2Coord(antennas_regions[dim],scenario.size_sector, scenario.size_x, scenario.size_y)
            _wolf.setPosition(dim, coord.x, coord.y)
        _wolf.setFitnessFunction(fitness_func)
        _wolf.updateFitness(np.array([],dtype='int64'), users_regions)           # update fitness nao teve ter antenas já instaladas, pois _wolf já as implementa
                    
        print("Fitnes _wolf: ", _wolf.fitness)
        if _wolf.fitness == -np.infty:                
            dimension = 1           
            while(dimension <= max_dimension):                
                solution = run_gwo(scenario, antennas_regions, users_regions, pack_size, dimension, max_iter, fitness_func, seed_base)
                seed_base += pack_size
                if solution.fitness != -np.infty:
                    print("Best solution: ", solution)                    
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
    with open(genf.gen_solver_result_filename(result_dir, version, math.ceil(sc.linear_to_db(min_sinr_w))), 'w') as f:
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
            connections = genf.get_dict_of_connections(antennas_regions, users_regions, users_t_m[t],_snr_map_mn, _min_sinr_w,
                                                       _max_users_per_antenna_m, verbose=False)
            print("connections: ", connections)
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
 
def run_gwo(scenario: geo.MapChess, antennas_regions, users_regions, pack_size: int, wolf_dimension: int,
            max_iter: int, fitness_func: Callable, seed_base: int):
    """
        Run the Grey Wolf Optimizer (GWO) algorithm for antenna deployment.

        Args:
            scenario (geo.MapChess): model that represents the scenario (size, number of sectors, users positions, etc.)
            antennas_regions (numpy.ndarray): Array of int to identify the regions where there are already antennas. 
            users_regions (numpy.ndarray): Array of int to identify the regions where there are users.            
            pack_size (int): The size of the population pack (number of wolves).
            wolf_dimension (int): The number of dimensions for each wolf (number of antennas to be deployed).
            max_iter (int): The maximum number of iterations for the GWO algorithm.
            fitness_func (Callable): A callable representing the fitness function to evaluate the wolf's solutions.
            seed_base (int): The seed base for generating random seeds for each wolf. Must be multiple of the number of wolves.
            Thus, each population will have a different set of seeds, avoiding repeated results.
        
        Returns:
            Wolf: The best solution (alpha wolf).
    """
    print(f"\nRun GWO to deployment +{wolf_dimension} antenna on the map")
    print("\tPack size: ", pack_size)
    print("\tWolf dimension", wolf_dimension)
    print("\tMax iter", max_iter)
    print("\tantennas_regions: ", antennas_regions)
    print("\tusers_regions: ", users_regions)
    print("\tFitness function: ", fitness_func)
    print("\tSeed_base: ", seed_base)
    
    # Initializes the population. Population is the pack.
    population = [Wolf(antennas_regions, users_regions, wolf_dimension, scenario, seed_base + i, i, fitness_func) for i in range(pack_size)]
        
    # Sort population in descendenting ordeer
    population = sorted(population, key = lambda temp: temp.fitness, reverse = True)

    # Gets the best three wolves: the alpha, beta and delta wolves
    alpha_wolf, beta_wolf, delta_wolf = copy.copy(population[: 3])
    print("initial_alpha: ", alpha_wolf)
    print("initial_beta: ", beta_wolf)
    print("initial_delta: ", delta_wolf, "\n")
    
    rnd = random.Random(scenario.chosen_seed)
    wolf_list = []
    iter = 0
    while iter < max_iter:
        verbose = False
        # after every 10 iterations
        # print iteration number and best fitness value so far
        if iter % 10 == 0 and iter > 1:
            print("iter = " + str(iter))
            print("Alpha wolf: ", alpha_wolf)
 
        # linearly decreased from 2 to 0
        a = 2*(1 - iter/max_iter)
        
        # updating each population member with the help of best three members
        for n in range(pack_size):
            Xnew:Wolf = copy.deepcopy(population[n]) 
            if verbose == True and population[n].id in wolf_list: print("Updating wolf ", n)
            if verbose == True and population[n].id in wolf_list: print(population[n])
            A1 = list(map(lambda r1: 2*a*r1 - a, [rnd.random() for _ in range(2*wolf_dimension)]))
            A2 = list(map(lambda r1: 2*a*r1 - a, [rnd.random() for _ in range(2*wolf_dimension)]))
            A3 = list(map(lambda r1: 2*a*r1 - a, [rnd.random() for _ in range(2*wolf_dimension)]))

            C1 = list(map(lambda r2: 2*r2, [rnd.random() for _ in range(2*wolf_dimension)]))
            C2 = list(map(lambda r2: 2*r2, [rnd.random() for _ in range(2*wolf_dimension)]))
            C3 = list(map(lambda r2: 2*r2, [rnd.random() for _ in range(2*wolf_dimension)]))

            if verbose == True and population[n].id in wolf_list: print("A1 ", A1)
            if verbose == True and population[n].id in wolf_list: print("A2 ", A2)
            if verbose == True and population[n].id in wolf_list: print("A3 ", A3)
            if verbose == True and population[n].id in wolf_list: print("C1 ", C1)
            if verbose == True and population[n].id in wolf_list: print("C2 ", C2)
            if verbose == True and population[n].id in wolf_list: print("C3 ", C3)            

            X1 = [coord.Coordinate(0.0, 0.0) for i in range(wolf_dimension)]
            X2 = [coord.Coordinate(0.0, 0.0) for i in range(wolf_dimension)]
            X3 = [coord.Coordinate(0.0, 0.0) for i in range(wolf_dimension)]
            
            for j in range(wolf_dimension):
                X = population[n].position[j]
                if verbose == True and population[n].id in wolf_list: print(f"Atualizando x{j} e y{j}")
                if verbose == True and population[n].id in wolf_list: print("X: ", X)

                tmp = coord.Coordinate(C1[2*j]*alpha_wolf.position[j].x, C1[2*j+1]*alpha_wolf.position[j].y)
                tmp = tmp - X
                tmp = abs(tmp)
                tmp.setCoordinate(A1[2*j]*tmp.x, A1[2*j+1]*tmp.y)

                X1[j] = alpha_wolf.position[j] - tmp

                if verbose == True and population[n].id in wolf_list: print("X1: ", X1[j])

                tmp = coord.Coordinate(C2[2*j]*beta_wolf.position[j].x, C2[2*j+1]*beta_wolf.position[j].y)
                tmp = abs(tmp - X)
                tmp.setCoordinate(A2[2*j]*tmp.x, A2[2*j+1]*tmp.y)
                X2[j] = beta_wolf.position[j] - tmp
                if verbose == True and population[n].id in wolf_list: print("X2: ", X2[j])

                tmp = coord.Coordinate(C3[2*j]*delta_wolf.position[j].x, C3[2*j+1]*delta_wolf.position[j].y)
                tmp = abs(tmp - X)
                tmp.setCoordinate(A3[2*j]*tmp.x, A3[2*j+1]*tmp.y)
                X3[j] = delta_wolf.position[j] - tmp
                if verbose == True and population[n].id in wolf_list: print("X3: ", X3[j])

                Xnew.position[j] = X1[j] + X2[j] + X3[j]
                Xnew.position[j] *= 1/3

                if verbose == True and population[n].id in wolf_list: print("Xnew", Xnew.position[j])
                
                # Mirroring
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

                if verbose == True and population[n].id in wolf_list: print("\n")
            
            #updating X_new fitness
            Xnew.updateFitness(antennas_regions, users_regions)
            if verbose == True and population[n].id in wolf_list: print("X: ", population[n])
            if verbose == True and population[n].id in wolf_list: print("X_new: ", Xnew)
            
            if Xnew.fitness >= population[n].fitness:       #TODO: Verify >= or >
                if verbose == True and population[n].id in wolf_list: print("Achou uma solucao melhor:")
                population[n] = Xnew
                if verbose == True and population[n].id in wolf_list: print(population[n])

            if verbose == True and population[n].id in wolf_list: print("\n")

        # Sort population in descendenting ordeer and get new the three best solutions
        population = sorted(population, key = lambda temp: temp.fitness, reverse=True)
        last_alpha_wolf = alpha_wolf                                                            # Keeps the last alpha wolf before updating
        alpha_wolf, beta_wolf, delta_wolf = copy.copy(population[: 3])

        if alpha_wolf.fitness != last_alpha_wolf.fitness:
            print(f"The alpha wolf has been updated to a position with higher fitness. iter = {iter}")
            print("New alpha wolf: ", alpha_wolf)
        
        iter += 1

    if alpha_wolf.fitness != 0: print("\n- Finishing GWO - \n")

    return alpha_wolf
           
def check_constraints(wolf_position: List[geo.Coordinate], antennas_regions, users_regions, scenario: geo.MapChess):
    """
        Checks the constraints for a given wolf according to the constraint definitions for the problem.

        Args:
            wolf_position (List[geo.Coordinate]): Wolf position represented by a list of coordinates. Each coordinate indicates of an
            antenna that the solution proposes to deply.
            antennas_regions (numpy.ndarray): Array of int to identify the regions where there are already antennas. 
            users_regions (numpy.ndarray): Array of int to identify the regions where there are users.
            scenario (geo.MapChess): model that represents the scenario (size, number of sectors, users positions, etc.)

        Returns:
            bool: If the wolf does not satisfy the constraints, returns False
            tuple[dict, numpy.ndarray, List[List[str]]]: If the wolf satisfies the constraints, returns a dict of connections between users and antennas, 
            the set of antennas given by the union of wolf_position and antennas_regions and the full coverage map.
            The coverage map shows the uncovered regions and the regions covered by one or more antennas.
    """
    global _map_of_service          # NOTE: Por que usar a palavra chave global aqui, mas não para o _antennasmap_m?
    installed_antennas = antennas_regions
    wolf_antennas = [geo.coord2Region(wolf_position[i], scenario.size_sector, scenario.size_x, scenario.size_y) for i in range(len(wolf_position))]
    """if (np.array_equal(antennas_regions, np.array([7,21,54,59,70,76]))) and wolf_antennas == [85]:
        print(antennas_regions, wolf_antennas, "verbose is True")
        verbose = True
    else:
        verbose = False"""
    verbose = False
    # Constraints:
    # There must not be more than one antenna in a sector
    # Checks if there is an item of installed_antennas already existing in wolf_antennas
    if any(elem in wolf_antennas for elem in installed_antennas):
        if verbose: print(f"\tThe wolf ({wolf_antennas}) deploys an antenna where one already exists ({installed_antennas}).")
        return False
    # Checks if there is duplicate item in wolf_antennas
    elif any(wolf_antennas.count(elem) > 1 for elem in wolf_antennas):
        if verbose: print("\tThe wolf deploys more than one antenna in the same region.")
        return False

    antennas_regions = np.concatenate((wolf_antennas,installed_antennas))
    # There is an antenna in a region forbidden
    for region in antennas_regions:
        if _antennasmap_m[region] == 0:
            if verbose: print("The wolf deploys an antenna in a region forbidden")
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
                if verbose: print("There is not a local backhaul")
                return False
    
    
    # Connection constraints:
    # The SNR requirement must be met
    # The antennas have a maximum number of users
    # A user can only connect to one antenna at a time
    # An antenna must serve the sector where it is installed
    # All sector where there are users must be served    
    connections, _map_of_service = genf.get_dict_of_connections(antennas_regions, users_regions,_users_t_m[0],_snr_map_mn, _min_sinr_w,
                                                               _max_users_per_antenna_m, return_map_of_service = True)
    
    if connections == None:
        if verbose: print("Unable to connect to all users")
        return False

    if verbose: print("All connected users: ", connections)

    return connections, antennas_regions, _map_of_service

def fitness_pgwo1(wolf_position: List[geo.Coordinate], antennas_regions, users_regions, scenario: geo.MapChess) -> float:
    """
        PGWO Fitness Version 1
        This fitness prioritizes the solutions that increase the coverage area absolutely, however, it depends on future entries.
        This means that to get the solution for a time slice, it needs to know the position of users in subsequent slices.
        
        Fitness definition: sum(region covered by the current solution) / sum(regions with users during some slice of time).

        Fitness value is a number from 0 to 1, i.e., 0% and 100%

        Args:
            wolf_position (List[geo.Coordinate]): Wolf position represented by a list of coordinates. Each coordinate indicates of an
            antenna that the solution proposes to deply.
            antennas_regions (numpy.ndarray): Array of int to identify the regions where there are already antennas. 
            users_regions (numpy.ndarray): Array of int to identify the regions where there are users.
            scenario (geo.MapChess): model that represents the scenario (size, number of sectors, users positions, etc.)

        Return:
            float: The value of the fitness function for the evaluated solution.

    """
    if (check_constraints(wolf_position, antennas_regions, users_regions, scenario)):
        # Coverage
        # Fitness definition: sum(region covered by the current solution) / sum(regions with users during some slice of time)
        # Fitness is a number from 0 and 1, i.e., 0% and 100%
        score = 0
        for m in _map_of_service:
            if m != []:
                score += 1

        score /= sum(_users_m)
    else:
        score = -np.infty
    
    return score

def fitness_pgwo2(wolf_position: List[geo.Coordinate], antennas_regions, users_regions, scenario: geo.MapChess) -> float:
    """
        PGWO Fitness Version 2
        This fitness  prioritizes the solutions that meet the constraints with the lowest Weighted Root Mean Square Error (WRMSE) values.
        This prevents antennas from being deployed over user concentration points. There is a weight equivalent to the coverage percentage
        for favoring solution with similar WRMSE but offering higher coverage.

        Fitness definition: 10000 * inverse of WRMSE of SNR values * coverage percentage
        NOTE: 10000 is a scale factor to make reading the fitness value easier during debugging.

        Args:
            wolf_position (List[geo.Coordinate]): Wolf position represented by a list of coordinates. Each coordinate indicates of an
            antenna that the solution proposes to deply.
            antennas_regions (numpy.ndarray): Array of int to identify the regions where there are already antennas. 
            users_regions (numpy.ndarray): Array of int to identify the regions where there are users.
            scenario (geo.MapChess): model that represents the scenario (size, number of sectors, users positions, etc.)

        Return:
            float: The value of the fitness function for the evaluated solution.

    """
    result = check_constraints(wolf_position, antennas_regions, users_regions, scenario)
    if(result):
        connections, antennas_regions, _map_of_service = result
        sum_eta_m = len([e for e in _map_of_service if e != []])       # Number of sectors served by the evaluated solution
        M = scenario.n_sectors                                         # Number of sectors on the map
              
        wmse = 0                                                       # Weighted Mean Square Error (WMSE); it is not WRMSE
        sum_u_tm = 0                                                   # Sum of users
        for region in users_regions:
            u_tm = _users_t_m[0][region]                               # Amount of user at region
            snr_mn = _snr_map_mn[connections[region]][region]          # SNR due connection between user and his antenna
            min_snr = _min_sinr_w                                      # Threshold of SNR at region
            wmse += u_tm*(snr_mn - min_snr)**2
            sum_u_tm += u_tm

        wmse /= sum_u_tm
        score = 10000*(1/(math.sqrt(wmse)))*sum_eta_m/M
    else:
        score = -np.infty
    return score

def fitness_pgwo3(wolf_position: List[geo.Coordinate], antennas_regions, users_regions, scenario: geo.MapChess) -> float:
    """
        PGWO Fitness Version 3
        This fitness  prioritizes the solutions that meet the constraints with the lowest Weighted Root Mean Square Error (WRMSE) values.
        This prevents antennas from being deployed over user concentration points. There is a weight equivalent to the coverage percentage
        for favoring solution with similar WRMSE but offering higher coverage.

        Fitness definition: 10000 * inverse of WRMSE of SNR values * coverage percentage
        NOTE: 10000 is a scale factor to make reading the fitness value easier during debugging.

        Args:
            wolf_position (List[geo.Coordinate]): Wolf position represented by a list of coordinates. Each coordinate indicates of an
            antenna that the solution proposes to deply.
            antennas_regions (numpy.ndarray): Array of int to identify the regions where there are already antennas. 
            users_regions (numpy.ndarray): Array of int to identify the regions where there are users.
            scenario (geo.MapChess): model that represents the scenario (size, number of sectors, users positions, etc.)

        Return:
            float: The value of the fitness function for the evaluated solution.

    """
    result = check_constraints(wolf_position, antennas_regions, users_regions, scenario)
    if(result):
        connections, antennas_regions, _map_of_service = result
        sum_eta_m = len([e for e in _map_of_service if e != []])       # Number of sectors served by the evaluated solution
        M = scenario.n_sectors                                         # Number of sectors on the map
              
        wmse = 0                                                       # Weighted Mean Square Error (WMSE); it is not WRMSE
        sum_u_tm = 0                                                   # Sum of users
        for region in users_regions:
            u_tm = _users_t_m[0][region]                               # Amount of user at region
            snr_mn = _snr_map_mn[connections[region]][region]          # SNR due connection between user and his antenna
            min_snr = _min_sinr_w                                      # Threshold of SNR at region
            wmse += u_tm*(snr_mn - min_snr)**2
            sum_u_tm += u_tm

        wmse /= sum_u_tm
        eccentricity = genf.get_coordinate_eccentricity(scenario, [geo.region2Coord(i, scenario.size_sector, scenario.size_x, scenario.size_y) 
                            for i in antennas_regions.tolist()])
        score = 10000*(1/(math.sqrt(wmse)))*eccentricity
    else:
        score = -np.infty
    return score