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
  fading1 = sc.jakes_fadding(6, 0, 363**-9, 0.7, 1)
  print(fading1)
  fading2 = sc.jakes_fadding(6, 0, 363**-9, 2, 1)
  print(fading2)
  fading3 = sc.jakes_fadding(6, 0, 363**-9, 0.1, 1)
  print(fading3)

if __name__ == "__main__":
  main()
  print("Done")