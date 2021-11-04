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

package LTE.networks;

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
import inet.common.scenario.ScenarioManager;

network UrbanMacro7_4
{
    parameters:
        int numUe = default(1);
        @display("bgb=822,681;bgi=background/streetmap");
    submodules:
        scenarioManager: ScenarioManager{
            @display("p=100;is=s");
        }
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
            @display("p=757.61,469.91;is=s");
        }
        ue1[numUe]: Ue {
            @display("p=442.51,617.87;is=s");
        }
        ue2[numUe]: Ue {
            @display("p=404.15,498.68;is=s");
        }
        ue3[numUe]: Ue {
            @display("p=575.4,523.34;is=s");
        }
        ue4[numUe]: Ue {
            @display("p=60.28,308.25;is=s");
        }
        ue5[numUe]: Ue {
            @display("p=220.57,238.38;is=s");
        }
        ue6[numUe]: Ue {
            @display("p=110.97,376.75;is=s");
        }
        microCell0: eNodeB {
            @display("p=442.51,335.65");
        }
        microCell1: eNodeB {
            @display("p=442.51,335.65");
        }
        microCell2: eNodeB {
            @display("p=442.51,335.65");
        }
        microCell3: eNodeB {
            @display("p=442.51,335.65");
        }
        microCell4: eNodeB {
            @display("p=442.51,335.65");
        }
        microCell5: eNodeB {
            @display("p=442.51,335.65");
        }
        microCell6: eNodeB {
            @display("p=442.51,335.65");
        }
        microCell7: eNodeB {
            @display("p=442.51,335.65");
        }
        microCell8: eNodeB {
            @display("p=442.51,335.65");
        }
        microCell9: eNodeB {
            @display("p=442.51,335.65");
        }
        microCell10: eNodeB {
            @display("p=442.51,335.65");
        }
        microCell11: eNodeB {
            @display("p=442.51,335.65");
        }
        microCell12: eNodeB {
            @display("p=442.51,335.65");
        }
        microCell13: eNodeB {
            @display("p=442.51,335.65");
        }
        microCell14: eNodeB {
            @display("p=442.51,335.65");
        }
        microCell15: eNodeB {
            @display("p=442.51,335.65");
        }
        microCell16: eNodeB {
            @display("p=442.51,335.65");
        }
        microCell17: eNodeB {
            @display("p=442.51,335.65");
        }
        microCell18: eNodeB {
            @display("p=442.51,335.65");
        }
        microCell19: eNodeB {
            @display("p=442.51,335.65");
        }
        microCell20: eNodeB {
            @display("p=442.51,335.65");
        }
        microCell21: eNodeB {
            @display("p=442.51,335.65");
        }
        microCell22: eNodeB {
            @display("p=442.51,335.65");
        }
        microCell23: eNodeB {
            @display("p=442.51,335.65");
        }
        microCell24: eNodeB {
            @display("p=305.51,254.82");
        }
        microCell25: eNodeB {
            @display("p=435.66,457.58002");
        }
        microCell26: eNodeB {
            @display("p=619.24,335.65");
        }
        microCell27: eNodeB {
            @display("p=369.9,361.68");
        }

    connections:
        server.pppg++ <--> Eth10G <--> router.pppg++;
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
        pgw.pppg++ <--> Eth10G <--> microCell7.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell8.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell9.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell10.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell11.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell12.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell13.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell14.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell15.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell16.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell17.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell18.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell19.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell20.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell21.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell22.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell23.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell24.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell25.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell26.ppp;
        pgw.pppg++ <--> Eth10G <--> microCell27.ppp;

		//############### X2 Connections ###############

        //# Hotspot0
        microCell0.x2++ <--> Eth10G <--> microCell1.x2++;
        microCell0.x2++ <--> Eth10G <--> microCell2.x2++;
        microCell0.x2++ <--> Eth10G <--> microCell3.x2++;
        microCell1.x2++ <--> Eth10G <--> microCell2.x2++;
        microCell1.x2++ <--> Eth10G <--> microCell3.x2++;
        microCell2.x2++ <--> Eth10G <--> microCell3.x2++;

        //# Hotspot1
        microCell4.x2++ <--> Eth10G <--> microCell5.x2++;
        microCell4.x2++ <--> Eth10G <--> microCell6.x2++;
        microCell4.x2++ <--> Eth10G <--> microCell7.x2++;
        microCell5.x2++ <--> Eth10G <--> microCell6.x2++;
        microCell5.x2++ <--> Eth10G <--> microCell7.x2++;
        microCell6.x2++ <--> Eth10G <--> microCell7.x2++;

        //# Hotspot2
        microCell8.x2++ <--> Eth10G <--> microCell9.x2++;
        microCell8.x2++ <--> Eth10G <--> microCell10.x2++;
        microCell8.x2++ <--> Eth10G <--> microCell11.x2++;
        microCell9.x2++ <--> Eth10G <--> microCell10.x2++;
        microCell9.x2++ <--> Eth10G <--> microCell11.x2++;
        microCell10.x2++ <--> Eth10G <--> microCell11.x2++;

        //# Hotspot3
        microCell12.x2++ <--> Eth10G <--> microCell13.x2++;
        microCell12.x2++ <--> Eth10G <--> microCell14.x2++;
        microCell12.x2++ <--> Eth10G <--> microCell15.x2++;
        microCell13.x2++ <--> Eth10G <--> microCell14.x2++;
        microCell13.x2++ <--> Eth10G <--> microCell15.x2++;
        microCell14.x2++ <--> Eth10G <--> microCell15.x2++;

        //# Hotspot4
        microCell16.x2++ <--> Eth10G <--> microCell17.x2++;
        microCell16.x2++ <--> Eth10G <--> microCell18.x2++;
        microCell16.x2++ <--> Eth10G <--> microCell19.x2++;
        microCell17.x2++ <--> Eth10G <--> microCell18.x2++;
        microCell17.x2++ <--> Eth10G <--> microCell19.x2++;
        microCell18.x2++ <--> Eth10G <--> microCell19.x2++;

        //# Hotspot5
        microCell20.x2++ <--> Eth10G <--> microCell21.x2++;
        microCell20.x2++ <--> Eth10G <--> microCell22.x2++;
        microCell20.x2++ <--> Eth10G <--> microCell23.x2++;
        microCell21.x2++ <--> Eth10G <--> microCell22.x2++;
        microCell21.x2++ <--> Eth10G <--> microCell23.x2++;
        microCell22.x2++ <--> Eth10G <--> microCell23.x2++;

        //# Hotspot6
        microCell24.x2++ <--> Eth10G <--> microCell25.x2++;
        microCell24.x2++ <--> Eth10G <--> microCell26.x2++;
        microCell24.x2++ <--> Eth10G <--> microCell27.x2++;
        microCell25.x2++ <--> Eth10G <--> microCell26.x2++;
        microCell25.x2++ <--> Eth10G <--> microCell27.x2++;
        microCell26.x2++ <--> Eth10G <--> microCell27.x2++;
}
