import geometry as geo
import sinr_comput as sc

def main():
  #Teste linear_to_db
  print(sc.linear_to_db(1))
  print(sc.linear_to_db(1/2))
  print(sc.linear_to_db(20))
  print(sc.linear_to_db(100))

if __name__ == "__main__":
  main()
  print("Done")