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

package networks;

import inet.networklayer.ipv4.RoutingTableRecorder;
import inet.node.ethernet.Eth10G;
import inet.node.ethernet.Eth10M;
import inet.node.inet.Router;
import inet.node.inet.StandardHost;
import lte.corenetwork.binder.LteBinder;
import lte.corenetwork.nodes.Ue;
import lte.corenetwork.nodes.eNodeB;
import lte.world.radio.LteChannelControl;
import lte.epc.PgwStandardSimplified;
import lte.common.LteNetworkConfigurator;
//import lte.corenetwork.nodes.ExtCell;

network MultiNet
{
    parameters:
        int numUe = default(1);
        int numeNB = 3;
        @display("bgb=781,505;bgi=background/streetmap");

    submodules:
        channelControl: LteChannelControl {
            @display("p=101,76;is=s");
        }
        routingRecorder: RoutingTableRecorder {
            @display("p=102,31;is=s");
        }
        configurator: LteNetworkConfigurator {
            @display("p=29,76;is=s");
        }
        binder: LteBinder {
            @display("p=29,31;is=s");
        }
        server: StandardHost {
            @display("p=243.96501,94.07125;is=l;i=device/server");
        }
        router: Router {
            @display("p=397.99374,86.835;i=device/smallrouter");
        }
        pgw: PgwStandardSimplified { //TODO: entender o modulo
            nodeType = "PGW";
            @display("p=529.28,130.2525;is=l");
        }
        eNB0: eNodeB {
            @display("p=444,269;is=vl");
        }
        eNB1: eNodeB {
            @display("p=344,240;is=vl");
        }
        ue0[numUe]: Ue {
            @display("p=451,385");
        }
        ue1[numUe]: Ue {
            @display("p=302,359");
        }


    connections:
        server.pppg++ <--> Eth10G <--> router.pppg++;
        router.pppg++ <--> Eth10G <--> pgw.filterGate;
        pgw.pppg++ <--> Eth10G <--> eNB0.ppp;
        pgw.pppg++ <--> Eth10G <--> eNB1.ppp;
        
        //# X2 connections
        eNB0.x2++ <--> Eth10G <--> eNB1.x2++;
}
