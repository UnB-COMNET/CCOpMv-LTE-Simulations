import LTE_Scenarios.hetnet_base as hetb
import _5G_Scenarios.ILP_fixed as ilpf

def main():

  chosen_seed = 123
  d_height = 4000
  d_width = 4000
  d_region = 400
  n_macros = 1
  ini_path = '../Network_CCOpMv/_5G/simulations/ilp_fixed.ini'
  enbs = [45]
  min_sinr = 10
  num_bands = [6, 100]
  multi_carriers = True

  # Scenario only changes with num_ues, center and micro_per_small
  #hetb.hetnet_base(filename, directions, center_x, center_y, num_ues, sites, micro_per_small, small_per_site, seed, with_stop= True)
  #hetb.hetnet_mov('../Network_CCOpMv/LTE/simulations/hetnet_mov.ini', directions, center_x, center_y, num_ues, sites, micro_per_small, small_per_site, seed)
  #ilpf.ilp_fixed_info('../Network_CCOpMv/_5G/simulations/ilp_fixed_info.ini', seed)
  #ilpf.ilp_fixed_users('../Network_CCOpMv/_5G/simulations/ilp_fixed_users.ini', chosen_seed, d_height= d_height, d_width= d_width, d_region= d_region, n_macros= n_macros)
  ilpf.ilp_fixed_ini(ini_path, chosen_seed, d_height= d_height, d_width= d_width, d_region= d_region, n_macros= n_macros, antennas_regions= enbs, repetitions= 5,
                     min_sinr= min_sinr, num_bands= num_bands, multi_carriers= multi_carriers)
  ilpf.ilp_fixed_ned(n_enbs= len(enbs))
  
if __name__ == "__main__":
  main()
  print("Done")