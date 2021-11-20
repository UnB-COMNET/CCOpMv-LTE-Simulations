import LTE_Scenarios.hetnet_base as hetb
import _5G_Scenarios.test_ILP as ilpf

def main():

  filename = '../Network_CCOpMv/LTE/simulations/eNB3_60.ini'
  directions = 2
  num_ues = 60
  center_x = 425*7/2
  center_y = 425*7/2
  sites = 7
  micro_per_small = 4
  small_per_site = 1
  seed = 123

  # Scenario only changes with num_ues, center and micro_per_small
  #hetb.hetnet_base(filename, directions, center_x, center_y, num_ues, sites, micro_per_small, small_per_site, seed, with_stop= True)
  #hetb.hetnet_mov('../Network_CCOpMv/LTE/simulations/hetnet_mov.ini', directions, center_x, center_y, num_ues, sites, micro_per_small, small_per_site, seed)
  #ilpf.ilp_fixed_info('../Network_CCOpMv/_5G/simulations/ilp_fixed_info.ini', seed)
  ilpf.ilp_fixed_users('../Network_CCOpMv/_5G/simulations/ilp_fixed_users.ini', seed)
if __name__ == "__main__":
  main()
  print("Done")