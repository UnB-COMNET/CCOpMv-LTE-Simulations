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

package _5G.networks;

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

network CelulasMultiplas
{
    parameters:
        int numeroUe = default(1);
        @display("i=block/network2;bgb=1000,1000;bgi=background/terrain");
    submodules:
        // E se mudar o nome "channelContro"?
        channelControl: LteChannelControl {
            @display("p=150.59999,46.184;is=n");
        }

        routingRecorder: RoutingTableRecorder {
            @display("p=726.896,48.191998;is=s");
        }
        configurator: Ipv4NetworkConfigurator {
            @display("p=451.8,48.191998");
        }
        binder: Binder {
            @display("p=911.63196,48.191998;is=s");
        }
        servidor: StandardHost {
            @display("p=726.896,188.752;i=device/server");
        }
        roteador1: Router {
            @display("p=726.896,323.288");
        }
        //roteador2: Router {
        //    @display("p=518.06396,506.016");
       	//}
        pgw: PgwStandard {
            @display("p=542.16,279.112;is=l");
        }
        eNB1: eNodeB {
            @display("p=150.59999,279.112;is=vl");
        }
        eNB2: eNodeB {
            @display("p=867.456,534.128;is=vl");
        }
        smartphone[numeroUe]: Ue {
            @display("p=204.816,506.016;is=n");
        }
    connections:
        servidor.pppg++ <--> Eth10G <--> roteador1.pppg++;
        roteador1.pppg++ <--> Eth10G <--> pgw.filterGate;
        pgw.pppg++ <--> Eth10G <--> eNB1.ppp;
        pgw.pppg++ <--> Eth10G <--> eNB2.ppp;
        eNB1.x2++ <--> Eth10G <--> eNB2.x2++;
        //eNB1.x2++ <--> Eth10G <--> roteador2.pppg++;
        //eNB2.x2++ <--> Eth10G <--> roteador2.pppg++;
        //eNB2.x2++ <--> Eth10G <--> roteador1.pppg++;
}
