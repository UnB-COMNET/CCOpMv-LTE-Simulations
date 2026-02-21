from app.core.sinr_comput import MapScenarioConfig
from app.core.geometry import MapSizeConfig
from app.core.geometry import MapSimulationConfig
from dataclasses import field
from typing import List
import app.core.geometry as geo
from app.core.sinr_comput import db_to_linear
from app.helpers.helper_xml import get_map_ues_time, get_ues_time
from app.solvers.ilp.ILP_fixed_in_time import ccop_mv_MILP as solver_fixed
from app.solvers.ilp.ILP_varying_in_time import ccop_mv_MILP as solver_varying
from app.solvers.ilp.ILP_single import ccop_mv_MILP as solver_single
from app.scenarios.five_g import ILP_configs as ilpc
import subprocess
from time import time, localtime, mktime
from datetime import datetime
from multiprocessing import Process, cpu_count
from pathlib import Path
import sys
import io
from app.core.errors import check_mode
from random import randint, seed, random
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import app.helpers.general_functions as genf
from app.solvers import ga
from app.solvers import gwo
from dataclasses import dataclass


@dataclass
class MovementUEsConfig:
    n_macros: int
    ues_per_slice: list
    n_ues: int

@dataclass
class MovementRunConfig:
    chosen_seed: int
    ini_path: str
    config_name: str
    cpu_num: int = field(default=1)

class MovementSimulationRunner:
    """Runs the movement/mobility simulation: generates .ini, runs OMNeT++, produces .sna snapshot."""

    def __init__(
        self,
        run_config: MovementRunConfig,
        simulation_config: MapSimulationConfig,
        size_config: MapSizeConfig,
        scenario_config: MapScenarioConfig,
        ues_config: MovementUEsConfig,
        ):
        self.run_config = run_config
        self.ues_config = ues_config
        self.simulation_config = simulation_config
        self.size_config = size_config
        self.scenario_config = scenario_config

    def run(self) -> None:
        scen = geo.MapChess(
            chosen_seed=self.run_config.chosen_seed,
            size_config=self.size_config,
            simulation_config=self.simulation_config,
            scenario_config=self.scenario_config
        )
        ilpc.ilp_move_users(
            scen, self.run_config.ini_path, n_macros=self.ues_config.n_macros, n_ues_macro=self.ues_config.n_ues,
            ues_per_slice=self.ues_config.ues_per_slice, config_name=self.run_config.config_name
        )
        snapshot_filename = genf.gen_movement_filename(config_name=self.run_config.config_name, seed_val=self.run_config.chosen_seed, snapshot=True)
        open(snapshot_filename, 'w').close()
        frame_path = genf.get_frameworks_path()
        arg = (
            'cd ../Network_CCOpMv\n'
            f'opp_runall -j{self.run_config.cpu_num} ./Network_CCOpMv -f ' + self.run_config.ini_path + r' -u Cmdenv -c ' + self.run_config.config_name
            + rf' -n .:{frame_path}/inet4/src:{frame_path}/inet4/examples:{frame_path}/inet4/tutorials:{frame_path}/inet4/showcases:{frame_path}/Simu5G-1.1.0/simulations:{frame_path}/Simu5G-1.1.0/src'
        )
        subprocess.check_output(arg, shell=True)
        with open(snapshot_filename, 'a') as f:
            f.write('<!--Done-->\n')


class SolverRunner:
    """Runs the placement solver (ILP/GA/GWO) for one scenario and mode, writing result_<mode>_<min_sinr>.txt."""

    def __init__(self, scen: geo.MapChess, ues_per_slice: list, xml_filename: str, min_sinr: int, result_dir: str,
                 mode: str, min_dis: int, first_antenna_region: int, min_time: int, disaster_percentage: int = 0):
        self.scen = scen
        self.ues_per_slice = ues_per_slice
        self.xml_filename = xml_filename
        self.min_sinr = min_sinr
        self.result_dir = result_dir
        self.mode = mode
        self.min_dis = min_dis
        self.first_antenna_region = first_antenna_region
        self.min_time = min_time
        self.disaster_percentage = disaster_percentage

    def run(self) -> None:
        self._run_solution()

    def _run_solution(self) -> None:
        scen = self.scen
        ues_per_slice = self.ues_per_slice
        xml_filename = self.xml_filename
        min_sinr = self.min_sinr
        result_dir = self.result_dir
        mode = self.mode
        min_dis = self.min_dis
        first_antenna_region = self.first_antenna_region
        min_time = self.min_time
        disaster_percentage = self.disaster_percentage

        file_name = genf.gen_file_name(mode=mode, min_sinr=min_sinr)
        start_time = time()
        get_solution = True
        show_sinr = False
        show_ues = False
        show_antennas_map = False
        chosen_seed = scen.chosen_seed
        size_x = scen.size_x
        size_y = scen.size_y
        size_sector = scen.size_sector
        num_slices = scen.num_slices

        if show_sinr:
            sinr_map = scen.getSinrMap()
            with open("sinr.txt", 'w') as f:
                for count2, enb in enumerate(sinr_map):
                    for count, snr in enumerate(enb):
                        f.write(f"{count2}:.\t{count}- {snr}\n")

        if get_solution:
            sinr_map = scen.getSinrMap()
            print("Running Solver - Min Snr: {} - {} (Seed: {})".format(min_sinr, mode.capitalize(), chosen_seed))
            seed(chosen_seed)
            max_user_antenna_m = [40 for _ in range(scen.n_sectors)]
            antennas_map_m = [(0 if random() < disaster_percentage / 100 else 1) for _ in range(scen.n_sectors)]
            min_snr_m = [db_to_linear(min_sinr) for _ in range(scen.n_sectors)]
            distance_mn = scen.getRegionsDistanceMatrix()
            max_dimension, pack_size, max_iter = 10, 50, 100
            first_antenna_region = self._resolve_first_antenna(antennas_map_m, first_antenna_region, chosen_seed)
            print("-------------Generating ues map")
            users_t_m = get_map_ues_time(scen=scen, xml_filename=xml_filename, ues_per_slice=ues_per_slice)
            out_file = open(genf.gen_log_file_name(result_dir, file_name), 'wb', 0)
            sys.stdout = io.TextIOWrapper(out_file, write_through=True)
            print(("-------------Calculating Solution (this may take a while)\n"
                  f"+++++++++++++++++++Min Sinr: {min_sinr} dB ({mode})\n"
                  f"+++++++++++++++++++With backhaul constraint. Start: {datetime.fromtimestamp(mktime(localtime(start_time)))}\n"))
            check_mode(mode=mode)
            print('Parameters:')
            print('- chosen seed {}'.format(chosen_seed))
            print('- Map with {} sectors'.format(scen.n_sectors))
            print('- Map {} x {} m'.format(scen.size_x, scen.size_y))
            print('- Sector has a side of {} m'.format(scen.size_sector))
            print('- Max time: ', num_slices)
            print("- users_t_m: ", users_t_m)
            print('MAX_USER_PER_ANTENNAS_m: ', max_user_antenna_m)
            print("antennas_map_m: ", antennas_map_m)
            print("FIRST_ANTENNA: ", first_antenna_region)
            print("MIN_SNR_m: ", min_snr_m)
            print("-MIN_DIST: ", min_dis)
            print("- disaster percentage: ", disaster_percentage)
            self._invoke_solver(
                scen, num_slices, users_t_m, max_user_antenna_m, antennas_map_m, sinr_map, min_snr_m,
                distance_mn, result_dir, min_time, first_antenna_region, max_dimension, pack_size, max_iter
            )
            print(f"--- Done after {(time() - start_time) / (60 * 60)} hours. ---")
            sys.stdout = sys.__stdout__

        elif show_ues:
            ues_coords = get_ues_time(ues_list=scen.getUEsList(), xml_filename=xml_filename)
            for t_ues in ues_coords:
                scen.plotUes(external=True, ues_positions=[u.position for u in t_ues])

        elif show_antennas_map:
            seed(chosen_seed)
            antennas_map_m = [(0 if random() < disaster_percentage / 100 else 1) for _ in range(scen.n_sectors)]
            nrows, ncols = int(size_y / size_sector), int(size_x / size_sector)
            res = np.array(antennas_map_m).reshape((nrows, ncols)).tolist()
            fig, ax = plt.subplots(figsize=(10, 10))
            ax.imshow(res, cmap='gray')
            plt.xticks(np.arange(-.5, ncols, 1))
            plt.yticks(np.arange(-.5, nrows, 1))
            plt.gca().set_xticklabels((np.arange(0, size_x + size_sector, size_sector)))
            plt.gca().set_yticklabels((np.arange(0, size_y + size_sector, size_sector)))
            plt.grid()
            plt.title(f'Antennas Map - {disaster_percentage}% Disaster')
            black_patch = mpatches.Patch(color='black', label='Unavailable')
            white_patch = mpatches.Patch(color='white', label='Available')
            plt.legend(handles=[black_patch, white_patch])
            plt.show()
            print("Plot")

    def _resolve_first_antenna(self, antennas_map_m: list, first_antenna_region, chosen_seed: int):
        while True:
            if first_antenna_region is not None and antennas_map_m[first_antenna_region] == 1:
                return first_antenna_region
            first_antenna_region = genf.gen_first_antenna_region(chosen_seed=chosen_seed, n_sectors=self.scen.n_sectors)

    def _invoke_solver(self, scen, num_slices, users_t_m, max_user_antenna_m, antennas_map_m, sinr_map, min_snr_m,
                       distance_mn, result_dir, min_time, first_antenna_region, max_dimension, pack_size, max_iter):
        mode = self.mode
        min_sinr = self.min_sinr
        min_dis = self.min_dis
        if mode == "varying":
            solver_varying(Max_Space=scen.n_sectors, Max_Time=num_slices, users_t_m=users_t_m,
                           MAX_USER_PER_ANTENNA_m=max_user_antenna_m, antenasmap_m=antennas_map_m, snr_map_mn=sinr_map,
                           MIN_SNR_m=min_snr_m, distance_mn=distance_mn, MIN_DIS=min_dis, result_dir=result_dir,
                           MIN_TIME=min_time, FIRST_ANTENNA=first_antenna_region)
        elif mode == "fixed":
            solver_fixed(Max_Space=scen.n_sectors, Max_Time=num_slices, users_t_m=users_t_m,
                         MAX_USER_PER_ANTENNA_m=max_user_antenna_m, antenasmap_m=antennas_map_m, snr_map_mn=sinr_map,
                         MIN_SNR_m=min_snr_m, distance_mn=distance_mn, MIN_DIS=min_dis, result_dir=result_dir,
                         FIRST_ANTENNA=first_antenna_region)
        elif mode == "single":
            valid_time = 0
            print("- valid_time: ", valid_time)
            solver_single(Max_Space=scen.n_sectors, Max_Time=num_slices, users_t_m=users_t_m,
                          MAX_USER_PER_ANTENNA_m=max_user_antenna_m, antenasmap_m=antennas_map_m, valid_time=valid_time,
                          snr_map_mn=sinr_map, MIN_SNR_m=min_snr_m, distance_mn=distance_mn, MIN_DIS=min_dis,
                          result_dir=result_dir, FIRST_ANTENNA=first_antenna_region)
        elif mode == "ga":
            ga.ga_solver(num_regions=scen.n_sectors, num_slices=num_slices, users_t_m=users_t_m,
                         max_users_per_antenna_m=max_user_antenna_m, snr_map_mn=sinr_map,
                         min_sinr_w=db_to_linear(min_sinr), distance_mn=distance_mn, min_dis=min_dis,
                         result_dir=result_dir, first_antenna_region=first_antenna_region, fitness_func=ga.fitness_pygad)
        elif mode == "pgwo1":
            gwo.pgwo_solver(scenario=scen, num_regions=scen.n_sectors, num_slices=num_slices, users_t_m=users_t_m,
                            max_users_per_antenna_m=max_user_antenna_m, antennasmap_m=antennas_map_m, snr_map_mn=sinr_map,
                            min_sinr_w=db_to_linear(min_sinr), distance_mn=distance_mn, min_dis=min_dis, result_dir=result_dir,
                            first_antenna_region=first_antenna_region, max_dimension=max_dimension, pack_size=pack_size,
                            max_iter=max_iter, version=gwo.STR_PGWO_1)
        elif mode == "pgwo2":
            gwo.pgwo_solver(scenario=scen, num_regions=scen.n_sectors, num_slices=num_slices, users_t_m=users_t_m,
                            max_users_per_antenna_m=max_user_antenna_m, antennasmap_m=antennas_map_m, snr_map_mn=sinr_map,
                            min_sinr_w=db_to_linear(min_sinr), distance_mn=distance_mn, min_dis=min_dis, result_dir=result_dir,
                            first_antenna_region=first_antenna_region, max_dimension=max_dimension, pack_size=pack_size,
                            max_iter=max_iter, version=gwo.STR_PGWO_2)
        elif mode == "pgwo3":
            gwo.pgwo_solver(scenario=scen, num_regions=scen.n_sectors, num_slices=num_slices, users_t_m=users_t_m,
                            max_users_per_antenna_m=max_user_antenna_m, antennasmap_m=antennas_map_m, snr_map_mn=sinr_map,
                            min_sinr_w=db_to_linear(min_sinr), distance_mn=distance_mn, min_dis=min_dis, result_dir=result_dir,
                            first_antenna_region=first_antenna_region, max_dimension=max_dimension, pack_size=pack_size,
                            max_iter=max_iter, version=gwo.STR_PGWO_3)


def main():
    ini_path = r"../Network_CCOpMv/_5G/simulations/ilp_move_users.ini"
    chosen_seed = 123
    size_y = 4000
    size_x = 4000
    size_sector = 400
    n_macros = 1
    num_slices = 10
    xml_filename = genf.gen_movement_filename("ilp_move_users", chosen_seed, snapshot=True)
    min_sinr = 5
    mode = "single"
    min_dis = 2000
    first_antenna_region = None
    min_time = 2
    result_dir = f"Solutions/chosen_seed_{chosen_seed}/micro_power_40"
    disaster_percentage = 0

    scen = geo.MapChess(
        size_x=size_x, size_y=size_y, size_sector=size_sector, carrier_frequency=0.7, chosen_seed=chosen_seed,
        num_slices=num_slices, simtime_move=1000, slice_time=1
    )
    scen.placeUEs(type="Random", n_macros=n_macros, n_ues_macro=0)
    users_t_m = genf.gen_users_t_m(chosen_seed, lambda_poisson=30, num_slices=num_slices)
    ues_per_slice = genf.gen_ue_per_slice(chosen_seed, users_t_m, num_slices)

    gen_ilp_info(
        scen=scen, ues_per_slice=ues_per_slice, xml_filename=xml_filename, min_sinr=min_sinr, result_dir=result_dir,
        mode=mode, min_dis=min_dis, first_antenna_region=first_antenna_region, min_time=min_time,
        disaster_percentage=disaster_percentage
    )
    #run_all_solvers(ini_path= ini_path, chosen_seed= chosen_seed, size_x= size_x, size_y= size_y, size_sector= size_sector, n_macros= n_macros,
    #                xml_filename= xml_filename, min_sinrs= min_sinrs, result_dir= result_dir, min_dis= min_dis, first_antenna_region= first_antenna_region)

def gen_ilp_info(scen: geo.MapChess, ues_per_slice: list, xml_filename: str,
                 min_sinr: int, result_dir: str, mode: str, min_dis: int, first_antenna_region: int, min_time: int,
                 disaster_percentage: int = 0) -> None:
    """Run the placement solver for one scenario and mode. Delegates to SolverRunner."""
    SolverRunner(
        scen, ues_per_slice, xml_filename, min_sinr, result_dir, mode, min_dis,
        first_antenna_region, min_time, disaster_percentage
    ).run()


def run_movement_simulation(
    run_config: MovementRunConfig,
    simulation_config: MapSimulationConfig,
    size_config: MapSizeConfig,
    scenario_config: MapScenarioConfig,
    ues_config: MovementUEsConfig,
) -> None:
    """Run movement/mobility simulation: generate .ini, run OMNeT++, produce .sna. Delegates to MovementSimulationRunner."""
    MovementSimulationRunner(
        run_config=run_config,
        simulation_config=simulation_config,
        size_config=size_config,
        scenario_config=scenario_config,
        ues_config=ues_config,
    ).run()


def run_all_solvers(chosen_seed: int, xml_filename: str, size_x: int, size_y: int, size_sector: int, n_macros: int,
                    min_sinrs: List[int], result_dir: str, min_dis: int, first_antenna_region: int, mode: str = ''):

    var = []
    processes = []

    if mode.lower() == 'varying':
        var = [True]
    elif mode.lower() == 'fixed':
        var = [False]
    else:
        var = [True, False]

    #Varying, fixed or both
    kwargs = {'chosen_seed' : chosen_seed, 'size_x': size_x, 'size_y': size_y, 'size_sector': size_sector, 'n_macros': n_macros, 'min_sinr': None,
              'xml_filename': xml_filename, 'result_dir': result_dir, 'varying': None, 'min_dis': min_dis, 'first_antenna_region': first_antenna_region}


    print(f'Starting computations on {cpu_count()} cores.')
    for varying in var:
        kwargs['varying'] = varying

        for min_snr in min_sinrs:
    
            kwargs['min_sinr'] = min_snr

            processes.append(Process(target= gen_ilp_info, kwargs= kwargs))
            processes[-1].start()

        #gen_ilp_info(chosen_seed= chosen_seed, size_x= size_x, size_y= size_y, size_sector= size_sector, n_macros= n_macros, xml_filename= xml_filename,
        #                       min_sinr= min_sinr, result_dir= result_dir, varying= varying, min_dis= min_dis, first_antenna_region= first_antenna_region)
    
    for p in processes:
        p.join()


if __name__ == "__main__":
    main()
    print("Done")