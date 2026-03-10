import opp_env
from typing import List
import subprocess
import time
from joblib import Parallel, delayed, parallel_backend
import app.helpers.general_functions as genf


def run_simulation_per_slice(
    ini_path: str,
    repetitions: int,
    config_name_list: List[str],
    cpu_num: int = 1,
    run_numbers: List[int] = [],
):
    """Execute all necessary runs of the Omnet++ configuration of each slice.

    Args:
        ini_path (str): Path to the INI files.
        repetitions (int): Number of repetitions.
        config_name_list (List[str]): List of configuration names.
        cpu_num (int, optional): Number of CPUs to use (default is 1).
        run_numbers (List[int], optional): List of run numbers (default is []).

    Returns:
        None
    """
    runs = ["" for i in range(len(config_name_list))]

    for number in run_numbers:
        if runs[number // repetitions] == "":
            runs[number // repetitions] += " -r "
        runs[number // repetitions] += f"{number % repetitions},"

    with parallel_backend("loky"):
        Parallel(n_jobs=cpu_num)(
            delayed(execute)(cpu_num, ini_path, config_name, runs[i])
            for i, config_name in enumerate(config_name_list)
        )


def run_simulation_all_slices(
    ini_path: str, config_name: str, cpu_num: int = 1, run_numbers: List[int] = []
):
    """Execute all necessary runs of one Omnet++ configuration.

    Args:
        ini_path (str): Path to the INI files.
        config_name (str): Configuration name.
        cpu_num (int, optional): Number of CPUs to use (default is 1).
        run_numbers (List[int], optional): List of run numbers (default is []).

    Returns:
        None
    """
    runs = ""

    if len(run_numbers) > 0:
        runs = " -r "
        for number in run_numbers:
            runs += f"{number},"
        runs = runs[:-1]

    frame_path = genf.get_frameworks_path()

    # Running Omnet++
    code = subprocess.run(
        (
            "cd ../Network_CCOpMv\n"
            f"opp_runall -j{cpu_num} ./Network_CCOpMv -f "
            + ini_path
            + r" -u Cmdenv -c "
            + config_name
            + runs
            + rf" -n .:{frame_path}/inet4/src:{frame_path}/inet4/examples:{frame_path}/inet4/tutorials:{frame_path}/inet4/showcases:{frame_path}/Simu5G-1.1.0/simulations:{frame_path}/Simu5G-1.1.0/src"
        ),
        shell=True,
    )

    code.check_returncode()


def execute(cpu_num, ini_path, config_name, runs):
    """
    Execute a simulation run using Omnet++.

    Args:
        cpu_num (int): Number of CPUs to use.
        ini_path (str): Path to the Omnet++ INI file.
        config_name (str): Name of the Omnet++ configuration.
        runs (str): Run numbers.

    Returns:
        None
    """
    frame_path = genf.get_frameworks_path()
    if runs != "":
        print("runs", runs, config_name)
        arg = (
            "cd ../Network_CCOpMv\n"
            f"opp_runall -j{cpu_num} ./Network_CCOpMv -f "
            + ini_path
            + r" -u Cmdenv -c "
            + config_name
            + runs
            + rf" -n .:{frame_path}/inet4/src:{frame_path}/inet4/examples:{frame_path}/inet4/tutorials:{frame_path}/inet4/showcases:{frame_path}/Simu5G-1.1.0/simulations:{frame_path}/Simu5G-1.1.0/src"
        )

        ini = time.time()
        subprocess.check_output(arg, shell=True)
        end = time.time()

        print("Processing time ({}): ".format(config_name), end - ini)


def run_subprocess_multiprocessing(command: str, shell: bool = True):
    """
    Run a subprocess command using the multiprocessing module.

    Args:
        command (str): Command to be executed.
        shell (bool, optional): Use shell to execute the command (default is True).

    Returns:
        None
    """
    code = subprocess.run(command, shell=shell)
    print("-----------------------------------------------------")

    code.check_returncode()
    print("_____________________________________________________")


def run_make():
    """
    Run the make command to build the Omnet++ simulation.

    Returns:
        None
    """
    venv_python_path = "/home/giordano/CCOpMv/opp-workspace/LTE-Scenarios-Simulation/.venv/bin/python"
    workspace_dir = "/home/giordano/CCOpMv/opp-workspace"
    project_dir = "/home/giordano/CCOpMv/opp-workspace/SimulationsCCOpMv"
    output_file = "proj_make"
    # opp_dir = f"{workspace_dir}/omnetpp-6.3.0"
    # opp_bin_dir = f"{opp_dir}/bin"
    inet_dir = f"{workspace_dir}/inet-4.5.4"
    simu5g_dir = f"{workspace_dir}/simu5g-1.4.1"

    code = subprocess.run(
        (
            f"cd {project_dir}\n"
            rf'{venv_python_path} -m opp_env run -c "opp_makemake -f --deep -o {output_file} -O out -KINET4_PROJ={inet_dir} -KSIMU5G_PROJ={simu5g_dir} -DINET_IMPORT -I. -I$\(INET4_PROJ\)/src -I$\(SIMU5G_PROJ\)/src -L$\(INET4_PROJ\)/src -L$\(SIMU5G_PROJ\)/src -lINET$\(D\) -lsimu5g$\(D\)"'
            f'\n{venv_python_path} -m opp_env run -c "make"\n'
        ),
        shell=True,
    )
    code.check_returncode()
