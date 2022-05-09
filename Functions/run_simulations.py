from typing import List
import _5G_Scenarios.ILP_configs as ilpc
import subprocess
import time
from joblib import Parallel, delayed, parallel_backend
from multiprocessing import Process
import general_functions as genf

def main():
  chosen_seed = 123
  size_y = 4000
  size_x = 4000
  size_sector = 400
  n_macros = 1
  dir_path = '../Network_CCOpMv/_5G/simulations/'
  result_dir = "Solutions/"
  #enbs = []
  min_sinrs = [5, 10, 15] #Must exist result_*.txt file where * is in min_sinrs (for sliced approach)
  num_bands = [100]
  repetitions = 3
  multi_carriers = False
  is_micro = True
  p_size = 1428#40
  app = "video"
  extra_config_name= 'video'
  target_f= 10 #Mbps
  varyings = [True, False]
  move_config_name = 'ilp_move_users'
  xml_filename = genf.gen_movement_filename(move_config_name, chosen_seed, snapshot= True)

  for i in range(len(min_sinrs)):
    for varying in varyings:

      print("Generating configuration files - Min Snr: {} - {}".format(min_sinrs[i], "Varying" if varying else "Fixed"))

      ini_path_sliced = dir_path + f'ilp_{"varying" if varying else "fixed"}_sliced.ini'
      config_name_sliced, enbs_sliced_num = ilpc.ilp_sliced_ini(ini_path_sliced, chosen_seed, size_y= size_y, size_x= size_x, size_sector= size_sector, n_macros= n_macros, repetitions= repetitions,
                                                                min_sinr= min_sinrs[i], num_bands= num_bands, multi_carriers= multi_carriers, is_micro= is_micro, p_size= p_size, app= app,
                                                                extra_config_name= extra_config_name, slice_time= 1, target_f= target_f, result_dir= result_dir, varying = varying, xml_filename= xml_filename)
      
      ilpc.ilp_ned(network = f"ILP{'Varying' if varying else 'Fixed'}Net", n_enbs= enbs_sliced_num, size_x= size_x, size_y= size_y)  

      print("Running simulations - Min Snr: {}".format(min_sinrs[i]))

      run_simulation_all_slices(ini_path= ini_path_sliced, config_name= config_name_sliced)

def run_simulation_per_slice(ini_path: str, repetitions: int, config_name_list: List[str], cpu_num: int = 1, run_numbers: List[int] = []):
  '''Execute all necessary runs of the Omnet++ configuration of each slice.'''
  processes = []
  runs = ['' for i in range(len(config_name_list))]

  for number in run_numbers:
    if runs[number // repetitions] == '':
      runs[number // repetitions] += ' -r '
    runs[number // repetitions] += f'{number % repetitions},'
  
  with parallel_backend("loky"):
    Parallel(n_jobs=cpu_num)(delayed(execute)(cpu_num,ini_path,config_name, runs[i]) for i, config_name in enumerate(config_name_list))
  

def run_simulation_all_slices(ini_path: str, config_name: str, cpu_num: int = 1, run_numbers: List[int] = []):
  '''Execute all necessary runs of one Omnet++ configuration.'''
  runs = ''

  if len(run_numbers) > 0:
    runs = ' -r '
    for number in run_numbers:
      runs += f'{number},'
    runs = runs[:-1]

  frame_path = genf.get_frameworks_path()

  #Running Omnet++
  code = subprocess.run(('cd ../Network_CCOpMv\n'
                          f'opp_runall -j{cpu_num} ./Network_CCOpMv -f ' + ini_path + r' -u Cmdenv -c ' + config_name + runs + rf' -n .:{frame_path}/inet4/src:{frame_path}/inet4/examples:{frame_path}/inet4/tutorials:{frame_path}/inet4/showcases:{frame_path}/Simu5G-1.1.0/simulations:{frame_path}/Simu5G-1.1.0/src'), shell= True)

  code.check_returncode()

def execute(cpu_num, ini_path,config_name, runs):
  frame_path = genf.get_frameworks_path()
  if runs != []:
    print('runs', runs, config_name)
    arg = ('cd ../Network_CCOpMv\n'
          f'opp_runall -j{cpu_num} ./Network_CCOpMv -f ' + ini_path + r' -u Cmdenv -c ' + config_name + runs + rf' -n .:{frame_path}/inet4/src:{frame_path}/inet4/examples:{frame_path}/inet4/tutorials:{frame_path}/inet4/showcases:{frame_path}/Simu5G-1.1.0/simulations:{frame_path}/Simu5G-1.1.0/src')
    
    ini = time.time()
    code = subprocess.check_output(arg, shell=True)
    end = time.time()
      
    print("Processing time ({}): ".format(config_name), end - ini)            
    
def run_subprocess_multiprocessing(command: str, shell: bool = True):
  code = subprocess.run(command, shell= shell)
  print("-----------------------------------------------------")
  #print(code.stderr())
  code.check_returncode()
  print("_____________________________________________________")

def run_make():
  frame_path = genf.get_frameworks_path()
  code = subprocess.run(('cd ../Network_CCOpMv\n'
                          rf'opp_makemake -f --deep -O out -KINET4_PROJ={frame_path}/inet4 -KSIMU5G_1_1_0_PROJ={frame_path}/Simu5G-1.1.0 -DINET_IMPORT -I. -I$\(INET4_PROJ\)/src -I$\(SIMU5G_1_1_0_PROJ\)/src -L$\(INET4_PROJ\)/src -L$\(SIMU5G_1_1_0_PROJ\)/src -lINET$\(D\) -lsimu5g$\(D\)'
                          '\nmake\n'), shell=	True)
  code.check_returncode()

if __name__ == "__main__":
  main()
  print("Done")