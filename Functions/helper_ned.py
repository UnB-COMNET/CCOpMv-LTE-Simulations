#from geometry import MapHexagonal, Macrocell
from typing import List
import numpy as np
from dataclasses import dataclass
from coordinates import Coordinate

separation = "###############"

@dataclass
class Parameter:
  type: str
  name: str
  value: str = None

@dataclass
class Submodule:
  name: str
  type: str
  size: str
  image: str = None

def writeX2Connections(f, object_names : List[str], quantities : List[int], initial_values : List[int] = None):

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

def writeNodeConnections(f, object_name, number: int):
  for i in range(number):
    f.write("\t\tpgw.pppg++ <--> Eth10G <--> {}{}.ppp;\n".format(object_name, i))
  

def writeSeparation(f, name):
  f.write('\n\t\t//' + separation + ' ' + name + ' ' + separation + '\n')

def writeComment(f, text):
  f.write("\n\t\t//# {}\n".format(text))

def writeBaseImports(f, is5g: bool= False, snapshot: bool= False):

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
import {prefix}.nodes.PgwStandard;'''.format(package = "_5G" if is5g else "LTE", prefix = "simu5g" if is5g else "lte"))

  if is5g: f.write("import simu5g.common.carrierAggregation.CarrierAggregation;")

  if snapshot: f.write("import _5G.models.Snapshotter;")

  f.write("\n\n")

def writeNet(f, net_name: str):
  f.write("network {}\n{\n".format(net_name))

def writeParams(f, bg_x: float, bg_y: float, bg_image: str, params: List[Parameter] = [Parameter("int", "numUe", "1")]):
  f.write("\tparameters:\n")
  for p in params:
    f.write("\t\t{} {}".format(p.type, p.name))
    if (p.value is not None):
      f.write("= default({});\n".format(p.value))
    else: f.write(";\n")
  #Background dimensions/image
  f.write('\t\t@display("bgd={x},{y};bgi={image}");\n'.format(x= bg_x, y= bg_y, image = bg_image))
  f.write("\tsubmodules:\n")

def writeBaseSubmodules(f, is5g: bool = False):
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
    f.write('\t\tcarrierAggregation: CarrierAggregation {\n\t\t\t\@display("p=50.993748,258.7;is=s");\n\t\t}\n')
  f.write('''\t\tserver: StandardHost {
\t\t\t@display("p=243.96501,94.07125;is=l;i=device/server");
\t\t}
\t\trouter: Router {
\t\t\t@display("p=397.99374,86.835;i=device/smallrouter");
\t\t}
\t\tpgw: PgwStandard { //TODO: entender o modulo
\t\t\t@display("p=529.28,130.2525;is=l");
\t\t}''')

def writeSubmodule(f, submodule: Submodule):
  f.write('''\t\t{name}: U{type} {
\t\t\t@display(is={size}''').format(name = submodule.name, type= submodule.type, size= submodule.size)
  if submodule.image is not None:
    f.write(", i={image}".format(image = submodule.image))
  f.write(");\n\t\t}\n")

def writeSnapshotter(f, submodule_size):
  f.write('''\t\tsnapshotter: Snapshotter {
\t\t\tparameters:
\t\t\t\tnumUE = numUe;
\t\t\t\t@display("is={}");
\t\t\t}\n'''.format(submodule_size))
