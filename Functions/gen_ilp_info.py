import geometry as geo
import sinr_comput as sc
from random import random

def main():
  #Teste linear_to_db
  #print(sc.linear_to_db(1))
  #print(sc.linear_to_db(1/2))
  #print(sc.linear_to_db(20))
  #print(sc.linear_to_db(100))

  #Teste jakes fadding
  #fading1 = sc.jakes_fadding(6, 0, 363**-9, 0.7, 1)
  #print(fading1)
  #fading2 = sc.jakes_fadding(6, 0, 363**-9, 2, 1)
  #print(fading2)
  #fading3 = sc.jakes_fadding(6, 0, 363**-9, 0.1, 1)
  #print(fading3)

  #Teste urban_macro pathloss
  #urban1 = sc.compute_urban_macro(distance = 1000, los = False, carrier_frequency= 0.7)
  #print(urban1)
  #urban2 = sc.compute_urban_macro(distance = 5000, los = False, carrier_frequency= 0.7)
  #print(urban2)
  #urban3 = sc.compute_urban_macro(distance = 1000, los = True, carrier_frequency= 0.7)
  #print(urban3)
  #urban4 = sc.compute_urban_macro(distance = 4999, los = False, carrier_frequency= 0.7)
  #print(urban4)

  #Teste log shadowing urban_macro
  #shad1 = sc.compute_shadowing(distance= 1000, speed= 0, los= False, scenario= "URBAN_MACROCELL", seed= 1)
  #print(shad1)
  #shad2 = sc.compute_shadowing(distance= 1000, speed= 0, los= True, scenario= "URBAN_MACROCELL", seed= 2)
  #print(shad2)
  #shad3 = sc.compute_shadowing(distance= 1000, speed= 0, los= False, scenario= "URBAN_MACROCELL", seed= 3)
  #print(shad3)
  #shad4 = sc.compute_shadowing(distance= 1000, speed= 0, los= False, scenario= "URBAN_MACROCELL", seed= 4)
  #print(shad4)
  count = 0
  count2 = 0
  scen = geo.MapChess(1000, 1000, 100)
  scen.placeTestUEs()
  scen.placeAntennas([0,1])
  sinr_map = scen.getSinrMap(seed = 1)
  with open("sinr.txt", 'w') as f:
    for enb in sinr_map:
      count = 0
      f.write("{}:".format(count2))
      for snr in enb:
        f.write("\t{}- {}\n".format(count, snr))
        count += 1
      count2 += 1



if __name__ == "__main__":
  main()
  print("Done")