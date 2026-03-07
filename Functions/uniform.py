import gwo
import numpy as np
import geometry as geo
import coordinates as coord
from typing import List
import general_functions as genf
import random
import copy    
import math
import sinr_comput as sc

def uniform_dist(scenario: geo.MapChess, num_regions: int, users_t_m: List[List[int]], distance_mn: List[List[float]], snr_map_mn: List[List[float]],
              antennasmap_m: List[int], first_antenna_region: int, num_slices: int, min_dis: int, min_sinr_w: float, max_users_per_antenna_m: List[int],
              result_dir: str):
    
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

    gwo._antennasmap_m = antennasmap_m
    gwo._first_antenna_region = first_antenna_region
    gwo._users_t_m = users_t_m
    gwo._snr_map_mn = snr_map_mn
    gwo._min_sinr_w = min_sinr_w
    gwo._max_users_per_antenna_m = max_users_per_antenna_m
    gwo._distance_mn = distance_mn
    gwo._min_dis = min_dis
    gwo._map_of_service = []        #TODO: verificar


    _users_m = num_regions*[0]
    for m in range(num_regions):
        for t in range(num_slices):
            if users_t_m[t][m] > 0:
                _users_m[m] = 1

    antennas_map = [0 if m != first_antenna_region else 1 for m in range(num_regions)]

    for i in range(num_slices):
        regions_available = list(range(0,num_regions))
        print("\nSlice", i)
        _users_t_m = users_t_m[i:]
        gwo._users_t_m = users_t_m[i:]
        print("Separando _users_t_m", _users_t_m)
        # Checks if the scenario needs more antenna to meet requisites
        antennas_regions = np.ravel(np.argwhere(np.array(antennas_map) > 0))
        print("antenas regions", antennas_regions)
        for x in antennas_regions:
            regions_available.remove(x)
        print("disponivel", regions_available)
        print("_users_t_m[0]", _users_t_m[0])
        users_regions = np.ravel(np.argwhere(np.array(_users_t_m[0]) > 0))
        
        dimension = len(antennas_regions) #TODO Refactore dimension to 2*num_antennas, i.e., (x,y) pairs
        
        _wolf = gwo.Wolf(antennas_regions, users_regions, dimension, scenario, None, None, None)        
        for dim in range(dimension):
            coord = geo.region2Coord(antennas_regions[dim],scenario.size_sector, scenario.size_x, scenario.size_y)
            _wolf.setPosition(dim, coord.x, coord.y)
        _wolf.setFitnessFunction(gwo.fitness_pgwo2)   
        print("Calculando fitness") 
        _wolf.updateFitness(np.array([],dtype='int64'), users_regions)

        print(_wolf)
        if _wolf.fitness == -np.infty:
            while regions_available:
                print("Escolhe uma regiao para colocar + uma antena")
                region_chosen = random.choice(regions_available)
                regions_available.remove(region_chosen)
                print("Escolheu", region_chosen)
                print("disponivel", regions_available)
                antennas_regions = np.append(antennas_regions, region_chosen)
                print("antenas regions", antennas_regions)
                dimension = len(antennas_regions)
                _wolf = gwo.Wolf(antennas_regions, users_regions, dimension, scenario, None, None, None)        
                for dim in range(dimension):
                    coord = geo.region2Coord(antennas_regions[dim],scenario.size_sector, scenario.size_x, scenario.size_y)
                    _wolf.setPosition(dim, coord.x, coord.y)
                _wolf.setFitnessFunction(gwo.fitness_pgwo2)    
                _wolf.updateFitness(np.array([],dtype='int64'), users_regions)


                if _wolf.fitness != -np.infty:
                    print(_wolf)
                    for n in antennas_regions:
                        antennas_map[n] = 1
                    results.append(np.ravel(np.argwhere(np.array(antennas_map) > 0)))
                    print("Results: ", results)
                    break
        else:
            results.append(antennas_regions)
            print("The set of antennas serves the scenario in the respective slice.")
            print("Results: ", results)

    print("RESULTS: ",len(results),results)
    print(num_slices)
    # Writing the log and result files
    with open(genf.gen_solver_result_filename(result_dir, 'unif', math.ceil(sc.linear_to_db(min_sinr_w))), 'w') as f:
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