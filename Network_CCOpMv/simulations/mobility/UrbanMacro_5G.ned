//
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

package simulations.mobility;

import simulations.mobility.MobileHost;
import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;
import inet.common.scenario.ScenarioManager;
import inet.networklayer.ipv4.RoutingTableRecorder;
import inet.node.ethernet.Eth10G;
import inet.node.ethernet.Eth10M;
import inet.node.inet.Router;
import inet.node.inet.StandardHost;
import simu5g.common.binder.Binder;
import simu5g.common.carrierAggregation.CarrierAggregation;
import simu5g.nodes.Ue;
import simu5g.nodes.eNodeB;
import simu5g.world.radio.LteChannelControl;
import simu5g.nodes.PgwStandard;

network UrbanMacro5G
{
    parameters:
        int numUe = default(1);
        @display("bgb=822,681;bgi=background/streetmap");
    submodules:
        scenarioManager: ScenarioManager {
            @display("p=49.32,209.61;is=s");
        }
        channelControl: LteChannelControl {
            @display("p=101,76;is=s");
        }
        routingRecorder: RoutingTableRecorder {
            @display("p=102,31;is=s");
        }
        configurator: Ipv4NetworkConfigurator {
            @display("p=50,125");
            //config = xmldoc("config.xml");
        }
        binder: Binder {
            @display("p=29,31;is=s");
        }
        carrierAggregation: CarrierAggregation {
            @display("p=50.993748,258.7;is=s");
        }
        server: StandardHost {
            @display("p=243.96501,94.07125;is=l;i=device/server");
        }
        router: Router {
            @display("p=397.99374,86.835;i=device/smallrouter");
        }
        pgw: PgwStandard { //TODO: entender o modulo           
            @display("p=529.28,130.2525;is=l");
        }
        eNB: eNodeB {
            @display("p=500,500;is=vl");
        }
        ue[numUe]: MobileHost {
            @display("p=200.02,308.25");
        }
        microCell: eNodeB {
            @display("p=360.31,308.25");
        }
    connections:
        server.pppg++ <--> Eth10G <--> router.pppg++; //TODO: entender Eth10G e as ligações
        router.pppg++ <--> Eth10G <--> pgw.filterGate;
        pgw.pppg++ <--> Eth10G <--> eNB.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell.ppp;
}
