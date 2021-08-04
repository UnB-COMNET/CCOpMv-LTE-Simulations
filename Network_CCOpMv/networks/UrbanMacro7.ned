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

network UrbanMacro7
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
            @display("p=500,500;is=vl");
        }
        eNB1: eNodeB {
            @display("p=1366.0254037844388,1000;is=vl");
        }
        eNB2: eNodeB {
            @display("p=500,1500;is=vl");
        }
        eNB3: eNodeB {
            @display("p=704.18,587.73;is=vl");
        }
        eNB4: eNodeB {
            @display("p=305.51,606.91;is=vl");
        }
        eNB5: eNodeB {
            @display("p=200.02,442.51;is=vl");
        }
        eNB6: eNodeB {
            @display("p=745.28,349.35;is=vl");
        }
        ue0[numUe]: Ue {
            @display("p=757.61,469.91");
        }
        ue1[numUe]: Ue {
            @display("p=442.51,617.87");
        }
        ue2[numUe]: Ue {
            @display("p=404.15,498.68");
        }
        ue3[numUe]: Ue {
            @display("p=575.4,523.34");
        }
        ue4[numUe]: Ue {
            @display("p=60.28,308.25");
        }
        ue5[numUe]: Ue {
            @display("p=220.57,238.38");
        }
        ue6[numUe]: Ue {
            @display("p=110.97,376.75");
        }
        microCell0: eNodeB {
            @display("p=360.31,308.25");
        }
        microCell1: eNodeB {
            @display("p=658.97003,442.51");
        }
        microCell2: eNodeB {
            @display("p=623.35,300.03");
        }
        microCell3: eNodeB {
            @display("p=268.52,376.75");
        }
        microCell4: eNodeB {
            @display("p=305.51,430.18");
        }
        microCell5: eNodeB {
            @display("p=293.18,254.82");
        }
        microCell6: eNodeB {
            @display("p=442.51,335.65");
        }
    connections:
        server.pppg++ <--> Eth10G <--> router.pppg++; //TODO: entender Eth10G e as ligações
        router.pppg++ <--> Eth10G <--> pgw.filterGate;
        pgw.pppg++ <--> Eth10G <--> eNB0.ppp;
        pgw.pppg++ <--> Eth10G <--> eNB1.ppp;
        pgw.pppg++ <--> Eth10G <--> eNB2.ppp;
        pgw.pppg++ <--> Eth10G <--> eNB3.ppp;
        pgw.pppg++ <--> Eth10G <--> eNB4.ppp;
        pgw.pppg++ <--> Eth10G <--> eNB5.ppp;
        pgw.pppg++ <--> Eth10G <--> eNB6.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell0.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell1.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell2.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell3.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell4.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell5.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell6.ppp;
}
