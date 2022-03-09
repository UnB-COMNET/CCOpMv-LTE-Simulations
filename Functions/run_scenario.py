import LTE_Scenarios.hetnet_base as hetb
import _5G_Scenarios.ILP_fixed as ilpf

def main():

  chosen_seed = 123
  size_y = 4000
  size_x = 4000
  size_sector = 400
  n_macros = 1
  dir_path = '../Network_CCOpMv/_5G/simulations/'
  enbs = [22, 27, 75, 93]
  min_sinr = 5
  num_bands = [6, 100]
  multi_carriers = False
  is_micro = True
  p_size = 1428#40
  app = "video"
  repetitions = 5
  target_f= 10 #Mbps
  result_dir = "Solutions/Results"
  time_slice = 1

  #ilpf.ilp_fixed_info('../Network_CCOpMv/_5G/simulations/ilp_fixed_info.ini', seed)
  #ilpf.ilp_fixed_users('../Network_CCOpMv/_5G/simulations/ilp_fixed_users.ini', chosen_seed, size_y= size_y, size_x= size_x, size_sector= size_sector, n_macros= n_macros)
  ilpf.ilp_fixed_ini(dir_path + 'ilp_fixed.ini', chosen_seed, size_y= size_y, size_x= size_x, size_sector= size_sector, n_macros= n_macros, repetitions= repetitions, antennas_regions= enbs,
                     min_sinr= min_sinr, num_bands= num_bands, multi_carriers= multi_carriers, is_micro= is_micro, p_size= p_size, app= app, extra_config_name= "VIDEO", target_f= target_f)
  ilpf.ilp_fixed_sliced_ini(dir_path + 'ilp_fixed_sliced.ini', chosen_seed, size_y= size_y, size_x= size_x, size_sector= size_sector, n_macros= n_macros, repetitions= repetitions,
                     min_sinr= min_sinr, num_bands= num_bands, multi_carriers= multi_carriers, is_micro= is_micro, p_size= p_size, app= app, extra_config_name= "VIDEO", time= time_slice, target_f= target_f,
                     result_dir= result_dir)
  ilpf.ilp_fixed_ned(n_enbs= len(enbs))
  
if __name__ == "__main__":
  main()
  print("Done")