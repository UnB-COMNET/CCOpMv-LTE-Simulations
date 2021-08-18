from os import name
#from geometry import MapHexagonal, Macrocell
import typing as ty
import numpy as np

separation = "###############"

def writeX2Connections(f, object_names : ty.List[str], quantities : ty.List[int], initial_values : ty.List[int] = None):

  if initial_values is None:
    initial_values = np.zeros(len(quantities), dtype= int)

  if len(object_names) > len(quantities):
    print("ERROR: Missing quantities for all objects.")
    return -1

  for i in range(len(object_names)):

    for number in range(initial_values[i], initial_values[i]+quantities[i]):

      for count in range(number+1, initial_values[i]+quantities[i]):
        f.write('\t\t{name}{number}.x2++ <--> Eth10G <--> {name}{count}.x2++;\n'
                .format(name=object_names[i], number=number, count=count))

      for name_index in range(i+1, len(object_names)):
        for number2 in range(initial_values[name_index], initial_values[name_index]+quantities[name_index]):
          f.write('\t\t{name}{number}.x2++ <--> Eth10G <--> {name2}{number2}.x2++;\n'
                .format(name=object_names[i], number=number, name2=object_names[name_index], number2=number2))

  return 0

def writeNode(f, object_name):
  f.write("\t\t{}".format(object_name)+": eNodeB {\n\t\t\t@display(\"p=442.51,335.65\");\n\t\t}\n")

def writeNodes(f, object_name, quantity : int, initial : int = 0):
  for i in range(initial, initial+quantity):
    writeNode(f, object_name+str(i))

def writeSeparation(f, name):
  f.write('\n\t\t//' + separation + ' ' + name + ' ' + separation + '\n')

def writeComment(f, text):
  f.write("\n\t\t//# {}\n".format(text))