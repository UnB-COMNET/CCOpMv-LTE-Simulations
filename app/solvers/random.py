from typing import List, Dict
from time import time, localtime, mktime
import random
from datetime import datetime

from app.core.coordinates import Coordinate
import app.core.sinr_comput as sc
import app.helpers.general_functions as genf
import app.core.geometry as geo
from app.helpers.helper_xml import get_map_ues_time

class RandomSolver:
    def __init__(self, scenario: geo.MapChess):
        self.scenario = scenario
        self.best_sinr_map = None
        self.best_antenna_positions = None

    def run(self, scenario: geo.MapChess, antenna_positions: List[Coordinate]):
        min_sinr_map = scenario.get_min_sinr_map()
        best_antenna_positions = antenna_positions.copy()

        while True:
            new_antenna_positions = self.random_antenna_positions()
            new_sinr_map = self.scenario.get_sinr_map(new_antenna_positions)

            if self.is_better(new_sinr_map, min_sinr_map):
                best_antenna_positions = new_antenna_positions
                min_sinr_map = new_sinr_map

            if self.is_same_sinr_map(new_sinr_map, min_sinr_map):
                break

        return best_antenna_positions

    def random_antenna_positions(self):
        antenna_positions = []
        n_antennas = len(self.scenario.enodeb_positions)
        for i in range(n_antennas):
            antenna_positions.append(self.scenario.enodeb_positions[i].copy())
            while True:
                new_x = random.randint(0, self.scenario.size_x)
                new_y = random.randint(0, self.scenario.size_y)
                new_position = Coordinate(new_x, new_y)
                if self.is_valid_position(new_position, i):
                    antenna_positions[i] = new_position
                    break

        return antenna_positions

    def is_valid_position(self, position: Coordinate, index: int):
        for i, antenna_position in enumerate(self.scenario.enodeb_positions):
            if i == index:
                continue
            if antenna_position.distance_to(position) < self.scenario.size_sector:
                return False
        return True

    def is_better(self, new_sinr_map: Dict[Coordinate, float], min_sinr_map: Dict[Coordinate, float]):
        for coord, sinr in new_sinr_map.items():
            if sinr < min_sinr_map[coord]:
                return False
        return True

    def is_same_sinr_map(self, new_sinr_map: Dict[Coordinate, float], min_sinr_map: Dict[Coordinate, float]):
        for coord, sinr in new_sinr_map.items():
            if sinr != min_sinr_map[coord]:
                return False
        return True

def run_random_solvers(chosen_seeds: List[int], size_x: int, size_y: int, size_sector: int, n_macros: int, move_config_name: str,
                       result_dir: str, min_sinr: int, num_slices: int, extra_dir: List[str], micro_power: int, lambda_poisson_gen_users_t_m: int, min_dis: int, simtime_move: int, slice_time: int, is_micro: bool = True,
                       **kwargs):

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
                            enb_tx_power= micro_power if is_micro else 46, h_enbs= 18, gain_ue= -1, enb_noise_figure= 9, num_slices= num_slices, simtime_move = simtime_move, slice_time = slice_time)

        #Placing UEs
        scen.placeUEs(type= "Random", n_macros= n_macros, n_ues_macro= 60)

        xml_filename = genf.gen_movement_filename(move_config_name, chosen_seed, snapshot= True)

        distance_mn = scen.getRegionsDistanceMatrix()

        tmp_users = genf.gen_users_t_m(chosen_seed, lambda_poisson = lambda_poisson_gen_users_t_m, num_slices=num_slices)             
        ues_per_slice = genf.gen_ue_per_slice(chosen_seed, tmp_users, num_slices=num_slices)
        users_t_m = get_map_ues_time(scen= scen, xml_filename= xml_filename, ues_per_slice=ues_per_slice)

        snr_map_mn = scen.getSinrMap()

        max_users_antenna_m = [60 for i in range(scen.n_sectors)]

        first_antenna_region = genf.gen_first_antenna_region(chosen_seed=chosen_seed, n_sectors=scen.n_sectors)


        #Initiating scenario
        solver = RandomSolver(scen)

        
        n_enodebs = random.randint(1, 10)  # replace with actual range of enodebs
        enodeb_positions = [Coordinate(random.randint(0, size_x), random.randint(0, size_y)) for _ in range(n_enodebs)]
        enodeb_positions.insert(0, Coordinate(0, 0))  # ensure the first enodeb is at (0, 0)

