from distutils.command.config import config
import _5G_Scenarios.ILP_configs as ilpc
import subprocess

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

  for i in range(len(min_sinrs)):
    for varying in varyings:

      print("Generating configuration files - Min Snr: {} - {}".format(min_sinrs[i], "Varying" if varying else "Fixed"))

      ini_path_sliced = dir_path + f'ilp_{"varying" if varying else "fixed"}_sliced.ini'
      config_name_sliced, enbs_sliced_num = ilpc.ilp_sliced_ini(ini_path_sliced, chosen_seed, size_y= size_y, size_x= size_x, size_sector= size_sector, n_macros= n_macros, repetitions= repetitions,
                                                                min_sinr= min_sinrs[i], num_bands= num_bands, multi_carriers= multi_carriers, is_micro= is_micro, p_size= p_size, app= app,
                                                                extra_config_name= extra_config_name, time= 1, target_f= target_f, result_dir= result_dir, varying = varying)
      
      #ilpc.ilp_ned(network = "ILPFixedNet", n_enbs= enbs_hando_num, size_x= size_x, size_y= size_y) 
      ilpc.ilp_ned(network = f"ILP{'Varying' if varying else 'Fixed'}Net", n_enbs= enbs_sliced_num, size_x= size_x, size_y= size_y)  

      print("Running simulations - Min Snr: {}".format(min_sinrs[i]))
      #run_simulation(ini_path= ini_path, config_name= config_name)
      run_simulation(ini_path= ini_path_sliced, config_name= config_name_sliced)

    #Handover cases
    #ini_path = dir_path + 'ilp_fixed.ini'
    #config_name, enbs_hando_num = ilpc.ilp_fixed_ini(ini_path, chosen_seed, size_y= size_y, size_x= size_x, size_sector= size_sector, n_macros= n_macros, repetitions= repetitions, antennas_regions= [],
    #                                                 min_sinr= min_sinrs[i], num_bands= num_bands, multi_carriers= multi_carriers, is_micro= is_micro, p_size= p_size, app= app, extra_config_name= "VIDEO",
    #                                                 target_f= target_f, result_dir= result_dir)
    #ilpc.ilp_ned(network = "ILPFixedNet", n_enbs= enbs_hando_num, size_x= size_x, size_y= size_y)
    #run_simulation(ini_path= ini_path, config_name= config_name)

def run_simulation(ini_path: str, config_name: str):
  
  #Running Omnet++
  subprocess.call(('cd ../Network_CCOpMv\n'
                   r'opp_makemake -f --deep -O out -KINET4_PROJ=../../inet4 -KSIMU5G_1_1_0_PROJ=../../Simu5G-1.1.0 -DINET_IMPORT -I. -I$\(INET4_PROJ\)/src -I$\(SIMU5G_1_1_0_PROJ\)/src -L$\(INET4_PROJ\)/src -L$\(SIMU5G_1_1_0_PROJ\)/src -lINET$\(D\) -lsimu5g$\(D\)'
                   '\nmake\n'
                   './Network_CCOpMv ' + ini_path + r' -u Cmdenv -c ' + config_name + r' -n .:../../inet4/src:../../inet4/examples:../../inet4/tutorials:../../inet4/showcases:../../Simu5G-1.1.0/simulations:../../Simu5G-1.1.0/src'), shell= True)

if __name__ == "__main__":
  main()
  print("Done")