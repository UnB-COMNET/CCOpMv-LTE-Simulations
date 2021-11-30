#from geometry import MapHexagonal, Macrocell
from os import name
from typing import List
import numpy as np
from dataclasses import dataclass
from coordinates import Coordinate

separation = "###############"

@dataclass
class Parameter:
  """
  This dataclass contains the type, name and value of a network parameter.
  """
  type: str
  name: str
  value: str = None

def writeX2Connections(f, object_names : List[str], quantities : List[int], initial_values : List[int] = None):
  """
  This funtion writes the informed X2 conections in a .ned file, based in the objects and their quantities informed.
  """
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

def writeSeparation(f, name: str):
  """
  This function writes the string 'name' as a comment separation in the .ned file.
  """
  f.write('\n\t\t//' + separation + ' ' + name + ' ' + separation + '\n')

def writeComment(f, text):
  """
  This function writes the string 'text' as a comment in the .ned file.
  """
  f.write("\n\t\t//# {}\n".format(text))

def writeBaseImports(f, is5g: bool= False, snapshot: bool= False):
  """
  This function writes the default imports used in a .ned file from INET and SimuLTE or Simu5G. 
  
  Keyword arguments:
  is5g -- if true uses Simu5G else SimuLTE (default False)
  snapshot -- if true import our own snapshotter module else don't (default False)
  """

  f.write('''//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Lesser General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
// 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Lesser General Public License for more details.
// 
// You should have received a copy of the GNU Lesser General Public License
// along with this program.  If not, see http://www.gnu.org/licenses/.
//
package {package}.networks;

import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;
import inet.networklayer.ipv4.RoutingTableRecorder;
import inet.node.ethernet.Eth10G;
import inet.node.ethernet.Eth10M;
import inet.node.inet.Router;
import inet.node.inet.StandardHost;
import {prefix}.common.binder.Binder;
import {prefix}.nodes.Ue;
import {prefix}.nodes.eNodeB;
import {prefix}.world.radio.LteChannelControl;
import {prefix}.nodes.PgwStandard;\n'''.format(package = "_5G" if is5g else "LTE", prefix = "simu5g" if is5g else "lte"))

  if is5g: f.write("import simu5g.common.carrierAggregation.CarrierAggregation;\n")

  if snapshot: f.write("import _5G.models.Snapshotter;\n")

  f.write("\n")

def writeNet(f, net_name: str):
  """
  This function writes the first three lines of a network definition in a .ned file.
  """
  f.write("network {}\n{{\n".format(net_name))

def writeEndNet(f):
  """
  This function writes the last line of a network definition in a .ned file.
  """
  f.write("}\n")

def writeParams(f, bg_x: float, bg_y: float, bg_image: str = None, params: List[Parameter] = [Parameter("int", "numUe", "1")]):
  """
  This function writes the background information and the informed parameters in a .ned file.
  """
  f.write("\tparameters:\n")
  for p in params:
    f.write("\t\t{} {}".format(p.type, p.name))
    if (p.value is not None):
      f.write("= default({});\n".format(p.value))
    else: f.write(";\n")
  #Background dimensions/image
  f.write('\t\t@display("bgd={x},{y}{image}");\n'.format(x= bg_x, y= bg_y, image = ";bgi={image}".format(bg_image) if bg_image is not None else ""))
  f.write("\tsubmodules:\n")

def writeBaseSubmodules(f, is5g: bool = False):
  """
  This function writes the base necessary submodules of a SimuLTE or Simu5G network in a .ned file.
  
  Keyword arguments:
  is5g -- if true add the Simu5G exclusive modules else don't (default False)
  """
  f.write('''\t\tchannelControl: LteChannelControl {
\t\t\t@display("p=101,76;is=s");
\t\t}
\t\troutingRecorder: RoutingTableRecorder {
\t\t\t@display("p=102,31;is=s");
\t\t}
\t\tconfigurator: Ipv4NetworkConfigurator {
\t\t\t@display("p=29,76;is=s");
\t\t}
\t\tbinder: Binder {
\t\t\t@display("p=29,31;is=s");
\t\t}\n''')
  if is5g:
    f.write('\t\tcarrierAggregation: CarrierAggregation {\n\t\t\t@display("p=50.993748,258.7;is=s");\n\t\t}\n')
  f.write('''\t\tserver: StandardHost {
\t\t\t@display("p=243.96501,94.07125;is=l;i=device/server");
\t\t}
\t\trouter: Router {
\t\t\t@display("p=397.99374,86.835;i=device/smallrouter");
\t\t}
\t\tpgw: PgwStandard {
\t\t\t@display("p=529.28,130.2525;is=l");
\t\t}\n''')

def writeSubmodule(f, name: str, type: str, size: str, image: str = None):
  """
  This function writes a submodule in a .ned file.
  """
  f.write('''\t\t{name}: {type} {{
\t\t\t@display("is={size}'''.format(name = name, type= type, size= size))
  if image is not None:
    f.write(', i={image}'.format(image = image))
  f.write('");\n\t\t}\n')

def writeSnapshotter(f, submodule_size):
  """
  This function writes the snapshotter submodule in a .ned file assuming a 'numUe' parameter.
  """
  f.write('''\t\tsnapshotter: Snapshotter {{
\t\t\tparameters:
\t\t\t\tnumUE = numUe;
\t\t\t\t@display("is={}");
\t\t}}\n'''.format(submodule_size))

def writeMultiNode(f, object_name: str = "eNB", type: str = "eNodeB", size: str = "l", image: str = None, quantity: int = 1):
  """
  This function writes nodes as submodules in the informed quantity in a .ned file.
  """
  for i in range(quantity):
    writeSubmodule(f, name= object_name+str(i), type= type, size= size, image= image)

def writeConnections(f, port1: str = None, port2: str = None, base = True):
  """
  This function writes the connection informed and possibly the base conections of a SimuLTE or Simu5G network in a .ned file.

  Keyword arguments:
  base -- if true add the SimuLTE and Simu5G base connections else don't (default True)
  """
  if base:
    f.write("\tconnections:\n")
    f.write("\t\tserver.pppg++ <--> Eth10G <--> router.pppg++;\n\t\trouter.pppg++ <--> Eth10G <--> pgw.filterGate;\n")

  if port1 is not None and port2 is not None:
    f.write("\t\t{} <--> Eth10G <--> {};\n".format(port1, port2))
    

def writeMultiNodeConnections(f, object_name: str = "eNB", quantity: int = 1, port2: str = "pgw.pppg++"):
  """
  This function writes the necessary connections of the informed quantity nodes in a .ned file.
  """
  for i in range(quantity):
    writeConnections(f, port1= object_name+str(i)+".ppp", port2= port2, base= False)