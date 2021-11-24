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
import inet.networklayer.ipv4.RoutingTableRecorder;
import inet.node.ethernet.Eth10G;
import inet.node.ethernet.Eth10M;
import inet.node.inet.Router;
import inet.node.inet.StandardHost;
import simu5g.common.binder.Binder;
import simu5g.nodes.Ue;
import simu5g.nodes.eNodeB;
import simu5g.world.radio.LteChannelControl;
import simu5g.nodes.PgwStandard;
import simu5g.common.carrierAggregation.CarrierAggregation;
import _5G.models.Snapshotter;

network SimpleNet
{
    parameters:
        int numUe = default(1);
        @display("bgb=822,681;bgi=background/streetmap");
    submodules:
        channelControl: LteChannelControl {
            @display("p=101,76;is=s");
        }
        routingRecorder: RoutingTableRecorder {
            @display("p=102,31;is=s");
        }
        configurator: Ipv4NetworkConfigurator {
            @display("p=29,76;is=s");
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
        ue[numUe]: Ue {
            @display("p=301.855,236.72876;is=s");
        }
        snapshotter: Snapshotter {
            parameters:
            	numUE = numUe;
            	@display("p=50.69,182.21;is=s");
        }
    connections:
        server.pppg++ <--> Eth10G <--> router.pppg++; //TODO: entender Eth10G e as ligações
        router.pppg++ <--> Eth10G <--> pgw.filterGate;
        pgw.pppg++ <--> Eth10G <--> eNB.ppp;
}

