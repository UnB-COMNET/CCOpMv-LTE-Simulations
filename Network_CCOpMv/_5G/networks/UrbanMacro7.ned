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

network UrbanMacro7
{
    parameters:
        int numUe = default(1);
        @display("bgb=1390.55,1519.33;bgi=background/streetmap");
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
        server: StandardHost {
            @display("p=243.96501,94.07125;is=l;i=device/server");
        }
        router: Router {
            @display("p=404.15,128.78;i=device/smallrouter");
        }
        router0: Router {
            @display("p=412.37,223.31;i=device/smallrouter");
        }
        router1: Router {
            @display("p=667.19,342.5;i=device/smallrouter");
        }
        router2: Router {
            @display("p=850.77,306.88;i=device/smallrouter");
        }
        router3: Router {
            @display("p=180.84,331.54;i=device/smallrouter");
        }
        router4: Router {
            @display("p=390.45,420.59;i=device/smallrouter");
        }
        router5: Router {
            @display("p=305.51,157.55;i=device/smallrouter");
        }
        router6: Router {
            @display("p=778.16003,31.51;i=device/smallrouter");
        }
        pgw: PgwStandard { //TODO: entender o modulo
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
            @display("p=58.91,172.62;is=vl");
        }
        eNB4: eNodeB {
            @display("p=305.51,606.91;is=vl");
        }
        eNB5: eNodeB {
            @display("p=200.02,442.51;is=vl");
        }
        eNB6: eNodeB {
            @display("p=778.16003,158.92;is=vl");
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
            @display("p=404.15,323.32");
        }
        microCell1: eNodeB {
            @display("p=658.97003,442.51");
        }
        microCell2: eNodeB {
            @display("p=928.86,401.41");
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
            @display("p=928.86,224.68001");
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
        eNB0.x2++ <--> Eth10G <--> microCell0.x2++;
        eNB1.x2++ <--> Eth10G <--> microCell1.x2++;
        eNB2.x2++ <--> Eth10G <--> microCell2.x2++;
        eNB3.x2++ <--> Eth10G <--> microCell3.x2++;
        eNB4.x2++ <--> Eth10G <--> microCell4.x2++;
        eNB5.x2++ <--> Eth10G <--> microCell5.x2++;
        eNB6.x2++ <--> Eth10G <--> microCell6.x2++;

        router0.pppg++ <--> Eth10G <--> microCell0.ppp;
        router1.pppg++ <--> Eth10G <--> microCell1.ppp;
        router2.pppg++ <--> Eth10G <--> microCell2.ppp;
        router3.pppg++ <--> Eth10G <--> microCell3.ppp;
        router4.pppg++ <--> Eth10G <--> microCell4.ppp;
        router5.pppg++ <--> Eth10G <--> microCell5.ppp;
        router6.pppg++ <--> Eth10G <--> microCell6.ppp;
        
        pgw.pppg++ <--> Eth10G <--> router0.pppg++;
        pgw.pppg++ <--> Eth10G <--> router1.pppg++;
        pgw.pppg++ <--> Eth10G <--> router2.pppg++;
        pgw.pppg++ <--> Eth10G <--> router3.pppg++;
        pgw.pppg++ <--> Eth10G <--> router4.pppg++;
        pgw.pppg++ <--> Eth10G <--> router5.pppg++;
        pgw.pppg++ <--> Eth10G <--> router6.pppg++;
}
