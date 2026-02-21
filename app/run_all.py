# Version 16/12/2023

from app.gen_ilp_info import MovementUEsConfig
from app.core.sinr_comput import MapScenarioConfig
from app.core.geometry import MapSizeConfig
from app.core.geometry import MapSimulationConfig
from app.gen_ilp_info import MovementRunConfig
from math import ceil
from typing import List, Tuple
from app.gen_ilp_info import run_movement_simulation, gen_ilp_info
from multiprocessing import cpu_count, Process, current_process, Manager, Queue
from app.scenarios.five_g.ILP_configs import (
    ilp_sliced_ini,
    ilp_sliced_ini_per_slice,
    ilp_ned,
)
from app.run_simulations import (
    run_make,
    run_simulation_all_slices,
    run_simulation_per_slice,
)
from pathlib import Path
import subprocess
from app.core.errors import check_mode, ErrorPackage
import app.core.geometry as geo
import app.helpers.general_functions as genf
import sys
import traceback
from app.core import errors
from dataclasses import dataclass, field
from enum import StrEnum

SUCCESS = "SUCCESS"

semaphore_cpucount = Manager().Semaphore(cpu_count())


class SolutionType(StrEnum):
    GA = "ga"
    PGWO2 = "pgwo2"
    ILP_FIXED = "fixed"
    ILP_SINGLE = "single"


@dataclass
class ScenarioConfig:
    size_x: int = field(default=4000)
    size_y: int = field(default=4000)
    size_sector: int = field(default=400)
    n_macros: int = field(default=1)
    min_sinrs: List[int] = field(default=[5, 10, 15])
    modes: List[SolutionType] = field(
        default=[
            SolutionType.ILP_SINGLE,
            SolutionType.ILP_FIXED,
            SolutionType.PGWO2,
            SolutionType.GA,
        ]
    )
    micro_power: int = field(default=30)
    lambda_poisson_gen_users_t_m: int = field(default=30)
    num_slices: int = field(default=12)
    simtime_move: int = field(default=1200)
    per_slice: bool = field(default=True)
    move_config_name: str = field(default="ilp_move_users")
    min_dis: int = field(default=2000)
    first_antenna_region: int = field(default=None)
    min_time: int = field(default=2)
    disaster_percentage: int = field(default=0)
    num_bands: List[int] = field(default=[100])
    repetitions: int = field(default=1)
    slice_time: int = field(default=1)
    p_size: int = field(default=1428)
    app: str = field(default="video")
    extra_config_name: str = field(default="video")
    target_f: float = field(default=10)
    cmdenv_config: bool = field(default=True)
    interference: bool = field(default=False)
    multi_carriers: bool = field(default=False)
    is_micro: bool = field(default=True)


@dataclass
class RunConfig:
    allrun_solver: bool = field(default=False)
    only_solver: bool = field(default=False)


@dataclass
class DirectoryConfig:
    project_dir: str = field(default="../Network_CCOpMv")
    sim_dir: str = field(default="_5G/simulations")
    csv_dir: str = field(default="_5G/results")
    net_dir: str = field(default="_5G/networks")
    result_dir: str = field(default="Solutions")
    extra_dir: List[str] = field(
        default=["disaster_percentage", "micro_power", "chosen_seed"]
    )


@dataclass
class RunAllConfig:
    chosen_seed: int
    scenario_config: ScenarioConfig
    run_config: RunConfig
    directory_config: DirectoryConfig


class SimulationPipeline:
    """Orchestrates the full simulation pipeline: movement, solvers, config generation, OMNeT++ runs, CSV export."""

    def __init__(
        self,
        chosen_seeds: List[int],
        scenario_config: ScenarioConfig,
        run_config: RunConfig,
        directory_config: DirectoryConfig,
    ):
        self.chosen_seeds = chosen_seeds
        self.scenario_config = scenario_config
        self.run_config = run_config
        self.directory_config = directory_config

    def run(self):
        """Run the full pipeline for all configured seeds and modes."""
        if self.only_solver and self.allrun_solver:
            print(
                "The option only_solver cannot be True if allrun_solver is also True."
            )
            return
        result = run_multiple_seeds(
            chosen_seeds=self.chosen_seeds,
            scenario_config=self.scenario_config,
            run_config=self.run_config,
            directory_config=self.directory_config,
        )
        if result == SUCCESS:
            print("Executions ended successfully.")
        else:
            print("ERROR!")


def main():
    """Entry point: build default pipeline config and run."""
    pipeline = SimulationPipeline(
        chosen_seeds=[2, 6, 10, 12, 13, 14, 15, 21, 22, 24, 25],
        scenario_config=ScenarioConfig(),
        run_config=RunConfig(),
        directory_config=DirectoryConfig(),
    )
    pipeline.run()


def run_multiple_seeds(
    chosen_seeds: List[int],
    scenario_config: ScenarioConfig,
    run_config: RunConfig,
    directory_config: DirectoryConfig,
):
    """This function is used to run multiple 'run_all' functions in diferent processes, one for each value in chosen_seeds."""

    # Generating makefile and compiling OMNeT++ and its frameworks
    if not run_config.only_solver:
        print("\nRunning makefile.")
        run_make()
    else:
        print("Solver only option selected.")
        if run_config.allrun_solver:
            # BUG: The option in this case is not correctly implemented, so better not allow using it.
            # It is necessary to deal with simultaneous large memory and CPU usage.
            print(
                "Error: Not possible to run with both allrun_solve and only_solver set to True."
            )
            return

    # Evaluating maximum runs
    num_seeds = len(chosen_seeds)
    num_modes = len(scenario_config.modes)
    num_minSinrs = len(scenario_config.min_sinrs)
    num_cases = num_seeds * num_modes * num_minSinrs
    num_totalRuns = num_cases * scenario_config.num_slices * scenario_config.repetitions
    num_cases_simultaneously = ceil(
        cpu_count() / (scenario_config.num_slices * scenario_config.repetitions)
    )
    print(
        "Simulating at most {} cases, hence {} runs. There are {} CPU cores available".format(
            num_cases, num_totalRuns, cpu_count()
        )
    )

    # TODO: REMOVE. Changing the results directory hierarchy
    # TODO: REMOVE. extra_dir = extra_dir + ['chosen_seed']
    """
    if allrun_solver is True:
        # Checking for the existence of optimizer solution files and running solver for non-existent ones using parallel computing
        missing_snapshots = get_missing_snapshots(chosen_seeds, move_config_name)
        run_missing_snapshots(missing_snapshots, size_x, size_y, size_sector, n_macros, project_dir,sim_dir, move_config_name, num_slices)
    
        missing_solutions = get_missing_solutions(chosen_seeds, min_sinrs, modes, extra_dir, micro_power, disaster_percentage)
        print("There are {} missing solutions.".format(len(missing_solutions)))
        for i in range(len(missing_solutions)):
            print(missing_solutions[i])
        if len(missing_solutions) > num_cases_simultaneously:
            kwargs_tmp = {'result_dir': result_dir, 'sim_dir': sim_dir, 'chosen_seed': chosen_seeds, 'micro_power': micro_power, 'disaster_percentage': disaster_percentage}
            run_missing_solutions(missing_solutions, size_x, size_y, size_sector, n_macros, result_dir, move_config_name, min_dis, first_antenna_region, min_time, micro_power, num_slices, extra_dir, kwargs_tmp)        
    """
    print("Running {} cases simultaneously.".format(num_cases_simultaneously))

    if run_config.allrun_solver:
        print("\nRunnning cases by seeds one by one.")
        for i in range(len(chosen_seeds)):
            print("CHOSEN SEED: {}".format(chosen_seeds[i]))
            result = run_all(
                chosen_seed=chosen_seeds[i],
                scenario_config=scenario_config,
                run_config=run_config,
                directory_config=directory_config,
            )
            if result == SUCCESS:
                chosen_seeds.remove(chosen_seeds[i])
            else:
                print("Error in cases with seed {}.".format(chosen_seeds[i]))

    else:
        processes = []
        queue = Queue()
        for chosen_seed in chosen_seeds:
            processes.append(
                Process(
                    target=run_all,
                    kwargs={
                        "chosen_seed": chosen_seed,
                        "scenario_config": scenario_config,
                        "run_config": run_config,
                        "directory_config": directory_config,
                        "queue": queue,
                    },
                )
            )
            processes[-1].start()

        for p in processes:
            p.join()

        errors = []
        while not queue.empty():
            errors.append(queue.get())

        if errors == []:
            chosen_seeds = []
        else:
            for error in errors:
                print(error)

    if chosen_seeds == []:
        return SUCCESS
    else:
        return


def run_all(
    chosen_seed: int,
    scenario_config: ScenarioConfig,
    run_config: RunConfig,
    directory_config: DirectoryConfig,
    queue: Queue = None,
):
    """This function is used to run all steps of a scenario study, using one process for each case diferent scenario,
    determined by the mode and min_sinrs."""

    if not run_config.allrun_solver:
        print(
            f"Started process run_all {current_process().name} {current_process().pid}. (Seed: {chosen_seed})"
        )

    verif_modes = genf.verify_modes(scenario_config.modes)

    # Preparing a row of cases for simulation
    num_modes = len(verif_modes)
    num_minSinrs = len(scenario_config.min_sinrs)
    cases: List[Tuple[SolutionType, int]] = []
    for i in range(num_modes):
        for j in range(num_minSinrs):
            cases.append((verif_modes[i], scenario_config.min_sinrs[j]))

    # Generating amount of users following the Poisson process
    users_t_m = genf.gen_users_t_m(
        chosen_seed,
        lambda_poisson=scenario_config.lambda_poisson_gen_users_t_m,
        num_slices=scenario_config.num_slices,
    )
    ues_per_slice = genf.gen_ue_per_slice(
        chosen_seed, users_t_m, num_slices=scenario_config.num_slices
    )
    max_ues = max(users_t_m)

    print(
        "Number of users over time, mu poisson: ",
        scenario_config.lambda_poisson_gen_users_t_m,
    )
    print(users_t_m)
    print("\nUEs per slice")
    for i in range(len(ues_per_slice)):
        print(ues_per_slice[i])
    print("\n")

    move_filename = genf.gen_movement_filename(
        scenario_config.move_config_name, chosen_seed, snapshot=False
    )
    xml_filename = genf.gen_movement_filename(
        scenario_config.move_config_name, chosen_seed, snapshot=True
    )

    simulation_config=MapSimulationConfig(
        num_slices=scenario_config.num_slices,
        simtime_move=scenario_config.simtime_move,
        slice_time=scenario_config.slice_time,
    )
    size_config=MapSizeConfig(
        size_x=scenario_config.size_x,
        size_y=scenario_config.size_y,
        size_sector=scenario_config.size_sector,
    )
    ues_config=MovementUEsConfig(
        n_macros=scenario_config.n_macros,
        ues_per_slice=ues_per_slice,
        n_ues=max_ues,
    )

    # Semaphore to control the use of the cpu
    with semaphore_cpucount:
        try:
            # Verifying if movement simulation is already done
            done = compare_last_line(xml_filename, "<!--Done-->\n")
            if done:
                print(f"Movement profile already simulated. Results in {xml_filename}.")
            # If not done, do it
            else:
                if run_config.only_solver:
                    print(
                        f"Error: Moviment profile missing (Seed: {chosen_seed}) with only_solver True. Returning."
                    )
                    return
                else:
                    move_ini_path = (
                        directory_config.project_dir
                        + "/"
                        + directory_config.sim_dir
                        + "/"
                        + move_filename
                    )
                    run_movement_simulation(
                        run_config=MovementRunConfig(
                            chosen_seed=chosen_seed,
                            ini_path=move_ini_path,
                            config_name=scenario_config.move_config_name,
                            cpu_num=1,
                        ),
                        simulation_config=simulation_config,
                        size_config=size_config,
                        scenario_config=MapScenarioConfig(),
                        ues_config=ues_config,
                    )

        except Exception:
            if queue is not None:
                queue.put(
                    ErrorPackage(
                        exc_info=sys.exc_info(),
                        pname=current_process().name,
                        pid=current_process().pid,
                        **{"seed": chosen_seed},
                    )
                )
            print(f"Terminated because of exception while running {xml_filename}.")
            return

    # Varying, fixed or both
    kwargs = {
        "chosen_seed": chosen_seed,
        "size_config": size_config,
        "ues_config": ues_config,
        "simulation_config": simulation_config,
        "min_sinr": None,
        "mode": None,
        "xml_filename": xml_filename,
        "result_dir": directory_config.result_dir,
        "min_dis":  scenario_config.min_dis,
        "first_antenna_region": scenario_config.first_antenna_region,
        "sim_dir": directory_config.sim_dir,
        "num_bands": scenario_config.num_bands,
        "repetitions": scenario_config.repetitions,
        "p_size": scenario_config.p_size,
        "app": scenario_config.app,
        "target_f": scenario_config.target_f,
        "extra_config_name": scenario_config.extra_config_name,
        "multi_carriers": scenario_config.multi_carriers,
        "is_micro": scenario_config.is_micro,
        "cmdenv_config": scenario_config.cmdenv_config,
        "min_time": scenario_config.min_time,
        "micro_power": scenario_config.micro_power,
        "net_dir": directory_config.net_dir,
        "project_dir": directory_config.project_dir,
        "per_slice": scenario_config.per_slice,
        "disaster_percentage": scenario_config.disaster_percentage,
        "allrun_solver": run_config.allrun_solver,
        "interference": scenario_config.interference,
    }

    for param in directory_config.extra_dir:
        kwargs["result_dir"] += "/" + param + f"_{kwargs[param]}"
        kwargs["sim_dir"] += "/" + param + f"_{kwargs[param]}"
        kwargs["net_dir"] += "/" + param + f"_{kwargs[param]}"
        directory_config.csv_dir += "/" + param + f"_{kwargs[param]}"

    Path(kwargs["result_dir"]).mkdir(parents=True, exist_ok=True)
    Path(directory_config.project_dir + "/" + kwargs["sim_dir"]).mkdir(parents=True, exist_ok=True)
    Path(directory_config.project_dir + "/" + kwargs["net_dir"]).mkdir(parents=True, exist_ok=True)
    Path(directory_config.project_dir + "/" + directory_config.csv_dir).mkdir(parents=True, exist_ok=True)

    print(f"Starting computations on {cpu_count()} cores.")

    failed_modes = []
    processes = []
    mode_queues = {}
    """
    if allrun_solver:
        # BUG: The option in this case is not correctly implemented, so better not allow using it.
        # It is necessary to deal with simultaneous large memory and CPU usage.   
        # TODO: REMOVE this block.
        with parallel_backend('loky', n_jobs= num_cases_simultaneously):
            result = Parallel()(delayed(process_func)(chosen_seed, size_x, size_y, size_sector, n_macros, n_ues, ues_per_slice, min_sinr, mode, xml_filename, min_dis,
                                                      first_antenna_region, project_dir, sim_dir, net_dir, num_bands, repetitions, p_size, app,
                                                      target_f, result_dir, slice_time, multi_carriers, is_micro,extra_config_name, cmdenv_config,
                                                      min_time, micro_power, num_slices, per_slice, disaster_percentage, allrun_solver)
                                                      for mode, min_sinr in cases)
                                                                                            
        for i in range(len(result)):
            if result[i] != SUCCESS:
                mode, min_sinr = cases[i]
                print('Error in case: mode {} and min SINR {}.'.format(mode, min_sinr))
                if mode not in failed_modes: failed_modes.append(mode)
    """

    kwargs["only_solver"] = run_config.only_solver
    kwargs["ues_per_slice"] = ues_per_slice
    kwargs["max_ues"] = max_ues
    for mode in verif_modes:
        mode_queues[mode] = Queue()

    for mode, min_sinr in cases:
        kwargs["queue"] = mode_queues[mode]
        kwargs["mode"] = mode
        kwargs["min_sinr"] = min_sinr
        processes.append(Process(target=process_func, kwargs=kwargs))
        processes[-1].start()

    for p in processes:
        p.join()

    for mode in verif_modes:
        while not mode_queues[mode].empty():
            errors = mode_queues[mode].get()
            print(
                f"Error in process_func of Mode: {mode.capitalize()}, Seed: {chosen_seed}.\n"
            )
            if mode not in failed_modes:
                failed_modes.append(mode)
            queue.put(errors)

    if not run_config.only_solver:
        for mode in verif_modes:
            if mode not in failed_modes:
                # Semaphore to control the use of the cpu
                with semaphore_cpucount:
                    print(
                        f"\nExporting .CSV files (Mode: {mode}, Seed: {chosen_seed}).\n"
                    )
                    get_csv(
                        mode=mode,
                        sim_path=directory_config.project_dir + "/" + kwargs["sim_dir"],
                        results_path=directory_config.project_dir + "/" + directory_config.csv_dir,
                        extra_config_name=scenario_config.extra_config_name,
                        interference=scenario_config.interference,
                    )

    else:
        print(f"\nEnding (Seed {chosen_seed}) with only_solver True.\n")

    if failed_modes == []:
        return SUCCESS
    else:
        return


def process_func(
    chosen_seed: int,
    size_config: MapSizeConfig,
    simulation_config: MapSimulationConfig,
    ues_config: MovementUEsConfig,
    min_sinr: int,
    mode: str,
    xml_filename: str,
    min_dis: int,
    first_antenna_region: int,
    project_dir: str,
    sim_dir: str,
    net_dir: str,
    num_bands: List[int],
    repetitions: int,
    p_size: int,
    app: str,
    target_f: float,
    result_dir: str = ".",
    multi_carriers: bool = False,
    is_micro: bool = True,
    extra_config_name: str = "",
    cmdenv_config: bool = True,
    min_time: int = 2,
    micro_power: int = 30,
    per_slice: bool = True,
    disaster_percentage: int = 0,
    allrun_solver: bool = False,
    queue: Queue = None,
    only_solver: bool = False,
    interference: bool = False,
):
    """This function defines the behaviour of each process, running both the solver and the simulation of a single scenario."""
    if not allrun_solver:
        print(
            f"Started process process_func {current_process().name} {current_process().pid}. (Seed: {chosen_seed}, Mode: {mode}, Min_sinr: {min_sinr})"
        )
        semaphore_cpucount.acquire()

    try:
        print(
            f"\nRunning case {mode} {min_sinr} dB, seed {chosen_seed}, micro power {micro_power}, disaster percentage {disaster_percentage}.\n"
        )

        check_mode(mode=mode)

        file_name = genf.gen_file_name(mode=mode, min_sinr=min_sinr)
        sim_path = project_dir + "/" + sim_dir

        # Verifying if solver is already done
        done = compare_last_line(
            genf.gen_solver_result_filename(result_dir, mode, min_sinr),
            "--- Done ---\n",
        )

        # Initiating scenario with no user equipment (UE).
        scen = geo.MapChess(
            size_config=size_config,
            chosen_seed=chosen_seed,
            scenario_config=MapScenarioConfig(
                scenario="URBAN_MICROCELL" if is_micro else "URBAN_MACROCELL",
                enb_tx_power=micro_power if is_micro else 46,
                h_enbs=18,
                gain_ue=-1,
                enb_noise_figure=9,
            ),
            simulation_config=simulation_config,
        )
        scen.placeUEs(type="Random", n_macros=ues_config.n_macros, n_ues_macro=0)

        if done:
            print(f"Solver {file_name} already computed. (Seed: {chosen_seed})")

        else:
            # Running solver
            gen_ilp_info(
                scen=scen,
                ues_per_slice=ues_config.ues_per_slice,
                xml_filename=xml_filename,
                min_sinr=min_sinr,
                result_dir=result_dir,
                mode=mode,
                min_dis=min_dis,
                first_antenna_region=first_antenna_region,
                min_time=min_time,
                disaster_percentage=disaster_percentage,
            )

        if not only_solver:
            # Generating config and network files
            print(
                "Generating configuration files - Min Snr: {} - {} (Seed: {})".format(
                    min_sinr, mode.capitalize(), chosen_seed
                )
            )

            ini_path_sliced = (
                sim_path + "/" + f"{file_name}{'_inter' if interference else ''}.ini"
            )
            network_name = f"ILP{mode.capitalize()}Net{str(min_sinr)}"

            if per_slice:
                config_name_sliced_list, num_enbs_time = ilp_sliced_ini_per_slice(
                    scen,
                    ini_path_sliced,
                    n_macros=ues_config.n_macros,
                    ues_per_slice=ues_config.ues_per_slice,
                    max_ues=ues_config.max_ues,
                    repetitions=repetitions,
                    min_sinr=min_sinr,
                    num_bands=num_bands,
                    multi_carriers=multi_carriers,
                    is_micro=is_micro,
                    p_size=p_size,
                    app=app,
                    extra_config_name=extra_config_name,
                    target_f=target_f,
                    result_dir=result_dir,
                    mode=mode,
                    network_name=network_name,
                    cmdenv_config=cmdenv_config,
                    net_dir=net_dir,
                    xml_filename=xml_filename,
                    interference=interference,
                )

                if config_name_sliced_list is None and num_enbs_time is None:
                    # There was a not feasible solution
                    raise errors.SolutionNotFeasible(
                        "The case seed {}, mode {}, min sinr {} dB, {}%% disaster is not feasible.".format(
                            chosen_seed, mode, min_sinr, disaster_percentage
                        )
                    )
                    # print("The case seed {}, mode {}, min sinr {} dB, {}%% disaster is not feasible.".format(chosen_seed, mode, min_sinr, disaster_percentage))
                    # return None

                for slice in range(len(num_enbs_time)):
                    network_name = (
                        f"ILP{mode.capitalize()}Net{str(min_sinr)}Slice{str(slice)}"
                    )
                    ilp_ned(
                        network=network_name,
                        n_enbs=num_enbs_time[slice],
                        size_x=size_config.size_x,
                        size_y=size_config.size_y,
                        net_dir=net_dir,
                        project_dir=project_dir,
                    )

            else:
                config_name_sliced, enbs_sliced_num = ilp_sliced_ini(
                    scen,
                    ini_path_sliced,
                    n_macros=ues_config.n_macros,
                    ues_per_slice=ues_config.ues_per_slice,
                    max_ues=ues_config.max_ues,
                    repetitions=repetitions,
                    min_sinr=min_sinr,
                    num_bands=num_bands,
                    multi_carriers=multi_carriers,
                    is_micro=is_micro,
                    p_size=p_size,
                    app=app,
                    extra_config_name=extra_config_name,
                    target_f=target_f,
                    result_dir=result_dir,
                    mode=mode,
                    network_name=network_name,
                    cmdenv_config=cmdenv_config,
                    net_dir=net_dir,
                    xml_filename=xml_filename,
                    interference=interference,
                )

                ilp_ned(
                    network=network_name,
                    n_enbs=enbs_sliced_num,
                    size_x=size_config.size_x,
                    size_y=size_config.size_y,
                    net_dir=net_dir,
                    project_dir=project_dir,
                )

            if interference:
                extra_out_name = "inter"
            else:
                extra_out_name = ""
            # Running the simulation
            run_numbers = get_missing_simulations(
                mode=mode,
                num_bands=num_bands,
                repetitions=repetitions,
                sim_path=sim_path,
                min_sinr=min_sinr,
                num_slices=simulation_config.num_slices,
                multi_carriers=multi_carriers,
                extra_config_name=extra_config_name,
                extra_out_name=extra_out_name,
            )
            if run_numbers == []:
                print(
                    "All simulations are already computed. Min Snr: {} - {} (Seed: {})".format(
                        min_sinr, mode.capitalize(), chosen_seed
                    )
                )
            else:
                print(
                    "Executing Simulations - Min Snr: {} - {} (Seed: {})".format(
                        min_sinr, mode.capitalize(), chosen_seed
                    )
                )
                if per_slice:
                    run_simulation_per_slice(
                        ini_path=ini_path_sliced,
                        repetitions=repetitions,
                        config_name_list=config_name_sliced_list,
                        cpu_num=cpu_count() if allrun_solver else 1,
                        run_numbers=run_numbers,
                    )
                else:
                    run_simulation_all_slices(
                        ini_path=ini_path_sliced,
                        config_name=config_name_sliced,
                        cpu_num=cpu_count() if allrun_solver else 1,
                        run_numbers=run_numbers,
                    )

    except Exception:
        if queue is not None:
            queue.put(
                ErrorPackage(
                    exc_info="".join(traceback.format_exception(*sys.exc_info())),
                    pname=current_process().name,
                    pid=current_process().pid,
                    **{"seed": chosen_seed, "mode": mode, "min_sinr": min_sinr},
                )
            )
        return

    finally:
        if not allrun_solver:
            semaphore_cpucount.release()

    return SUCCESS


def get_csv(
    mode: str,
    sim_path: str,
    results_path: str,
    extra_config_name: str = "",
    interference: bool = False,
):
    """This function call a scavetool command to create the necessary .csv files"""

    check_mode(mode=mode)

    csv_path, sca_vec_dir = genf.gen_csv_path(
        mode, sim_path, results_path, extra_config_name, interference
    )

    print(f"Making {csv_path}.")

    if not interference:
        code = subprocess.run(
            f'scavetool x -o {csv_path} -f "module(**.cellularNic.channelModel[*]) OR module(**.app[*])" {sca_vec_dir}/*-*-.sca {sca_vec_dir}/*-*-.vec',
            shell=True,
        )
    else:
        code = subprocess.run(
            f'scavetool x -o {csv_path} -f "module(**.cellularNic.channelModel[*]) OR module(**.app[*])" {sca_vec_dir}/*-*-inter.sca {sca_vec_dir}/*-*-inter.vec',
            shell=True,
        )

    code.check_returncode()


def compare_last_line(filename: str, line: str) -> bool:
    """This function compare the last line of a file with the informed string."""

    last_line = ""
    count = 0
    try:
        with open(filename, "r") as f:
            for _l in f:
                last_line = _l
                count += 1

        if count <= 1:
            return False

    except FileNotFoundError:
        return False
    else:
        return last_line == line


def get_missing_simulations(
    mode: str,
    num_bands: List[int],
    repetitions: int,
    sim_path: str,
    min_sinr: int,
    num_slices: int,
    multi_carriers: bool,
    extra_config_name: str,
    extra_out_name: str,
):
    """This function returns the simulation runs that were not executed yet"""

    sim_resultdir = f"{sim_path}/results"
    counter = 0
    missing = []
    config_pattern = genf.gen_sliced_config_pattern(
        min_sinr=min_sinr,
        mode=mode,
        multi_carriers=multi_carriers,
        extra_config_name=extra_config_name,
    )
    for band in num_bands:
        for slice in range(num_slices):
            for repetition in range(repetitions):
                filename = f"{sim_resultdir}/{config_pattern}-cmdout/{min_sinr}-{band}-{repetition}-{slice}{('-' + extra_out_name) if extra_out_name != '' else '-'}.out"
                done = compare_last_line(filename, "[INFO]\tClear all sockets\n")
                if not done:
                    missing.append(counter)

                counter += 1

    return missing


if __name__ == "__main__":
    main()
