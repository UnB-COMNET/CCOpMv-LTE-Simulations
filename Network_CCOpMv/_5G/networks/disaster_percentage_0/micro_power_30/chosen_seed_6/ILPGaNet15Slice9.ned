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
package _5G.networks.disaster_percentage_0.micro_power_30.chosen_seed_6;

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

network ILPGaNet15Slice9
{
	parameters:
		int numUe= default(1);
		@display("bgd=4000,4000");
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
		pgw: PgwStandard {
			@display("p=529.28,130.2525;is=l");
		}
		eNB0: eNodeB {
			@display("is=l");
		}
		eNB1: eNodeB {
			@display("is=l");
		}
		eNB2: eNodeB {
			@display("is=l");
		}
		eNB3: eNodeB {
			@display("is=l");
		}
		eNB4: eNodeB {
			@display("is=l");
		}
		eNB5: eNodeB {
			@display("is=l");
		}
		eNB6: eNodeB {
			@display("is=l");
		}
		eNB7: eNodeB {
			@display("is=l");
		}
		eNB8: eNodeB {
			@display("is=l");
		}
		eNB9: eNodeB {
			@display("is=l");
		}
		eNB10: eNodeB {
			@display("is=l");
		}
		eNB11: eNodeB {
			@display("is=l");
		}
		eNB12: eNodeB {
			@display("is=l");
		}
		eNB13: eNodeB {
			@display("is=l");
		}
		eNB14: eNodeB {
			@display("is=l");
		}
		eNB15: eNodeB {
			@display("is=l");
		}
		eNB16: eNodeB {
			@display("is=l");
		}
		eNB17: eNodeB {
			@display("is=l");
		}
		eNB18: eNodeB {
			@display("is=l");
		}
		eNB19: eNodeB {
			@display("is=l");
		}
		eNB20: eNodeB {
			@display("is=l");
		}
		eNB21: eNodeB {
			@display("is=l");
		}
		eNB22: eNodeB {
			@display("is=l");
		}
		eNB23: eNodeB {
			@display("is=l");
		}
		eNB24: eNodeB {
			@display("is=l");
		}
		eNB25: eNodeB {
			@display("is=l");
		}
		eNB26: eNodeB {
			@display("is=l");
		}
		eNB27: eNodeB {
			@display("is=l");
		}
		eNB28: eNodeB {
			@display("is=l");
		}
		eNB29: eNodeB {
			@display("is=l");
		}
		eNB30: eNodeB {
			@display("is=l");
		}
		eNB31: eNodeB {
			@display("is=l");
		}
		eNB32: eNodeB {
			@display("is=l");
		}
		ue[numUe]: Ue {
			@display("is=s");
		}
		snapshotter: Snapshotter {
			parameters:
				numUE = numUe;
				@display("is=s");
		}
	connections:
		server.pppg++ <--> Eth10G <--> router.pppg++;
		router.pppg++ <--> Eth10G <--> pgw.filterGate;
		eNB0.ppp <--> Eth10G <--> pgw.pppg++;
		eNB1.ppp <--> Eth10G <--> pgw.pppg++;
		eNB2.ppp <--> Eth10G <--> pgw.pppg++;
		eNB3.ppp <--> Eth10G <--> pgw.pppg++;
		eNB4.ppp <--> Eth10G <--> pgw.pppg++;
		eNB5.ppp <--> Eth10G <--> pgw.pppg++;
		eNB6.ppp <--> Eth10G <--> pgw.pppg++;
		eNB7.ppp <--> Eth10G <--> pgw.pppg++;
		eNB8.ppp <--> Eth10G <--> pgw.pppg++;
		eNB9.ppp <--> Eth10G <--> pgw.pppg++;
		eNB10.ppp <--> Eth10G <--> pgw.pppg++;
		eNB11.ppp <--> Eth10G <--> pgw.pppg++;
		eNB12.ppp <--> Eth10G <--> pgw.pppg++;
		eNB13.ppp <--> Eth10G <--> pgw.pppg++;
		eNB14.ppp <--> Eth10G <--> pgw.pppg++;
		eNB15.ppp <--> Eth10G <--> pgw.pppg++;
		eNB16.ppp <--> Eth10G <--> pgw.pppg++;
		eNB17.ppp <--> Eth10G <--> pgw.pppg++;
		eNB18.ppp <--> Eth10G <--> pgw.pppg++;
		eNB19.ppp <--> Eth10G <--> pgw.pppg++;
		eNB20.ppp <--> Eth10G <--> pgw.pppg++;
		eNB21.ppp <--> Eth10G <--> pgw.pppg++;
		eNB22.ppp <--> Eth10G <--> pgw.pppg++;
		eNB23.ppp <--> Eth10G <--> pgw.pppg++;
		eNB24.ppp <--> Eth10G <--> pgw.pppg++;
		eNB25.ppp <--> Eth10G <--> pgw.pppg++;
		eNB26.ppp <--> Eth10G <--> pgw.pppg++;
		eNB27.ppp <--> Eth10G <--> pgw.pppg++;
		eNB28.ppp <--> Eth10G <--> pgw.pppg++;
		eNB29.ppp <--> Eth10G <--> pgw.pppg++;
		eNB30.ppp <--> Eth10G <--> pgw.pppg++;
		eNB31.ppp <--> Eth10G <--> pgw.pppg++;
		eNB32.ppp <--> Eth10G <--> pgw.pppg++;

		//############### X2 Connections ###############
		eNB0.x2++ <--> Eth10G <--> eNB1.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB2.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB3.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB4.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB5.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB6.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB7.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB8.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB9.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB10.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB11.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB12.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB13.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB14.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB15.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB16.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB17.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB18.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB19.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB20.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB21.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB22.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB23.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB24.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB25.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB26.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB0.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB2.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB3.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB4.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB5.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB6.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB7.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB8.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB9.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB10.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB11.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB12.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB13.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB14.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB15.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB16.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB17.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB18.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB19.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB20.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB21.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB22.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB23.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB24.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB25.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB26.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB1.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB3.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB4.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB5.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB6.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB7.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB8.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB9.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB10.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB11.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB12.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB13.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB14.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB15.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB16.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB17.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB18.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB19.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB20.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB21.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB22.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB23.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB24.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB25.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB26.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB2.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB4.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB5.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB6.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB7.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB8.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB9.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB10.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB11.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB12.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB13.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB14.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB15.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB16.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB17.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB18.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB19.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB20.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB21.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB22.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB23.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB24.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB25.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB26.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB3.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB5.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB6.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB7.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB8.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB9.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB10.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB11.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB12.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB13.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB14.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB15.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB16.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB17.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB18.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB19.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB20.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB21.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB22.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB23.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB24.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB25.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB26.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB4.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB6.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB7.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB8.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB9.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB10.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB11.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB12.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB13.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB14.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB15.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB16.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB17.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB18.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB19.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB20.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB21.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB22.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB23.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB24.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB25.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB26.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB5.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB6.x2++ <--> Eth10G <--> eNB7.x2++;
		eNB6.x2++ <--> Eth10G <--> eNB8.x2++;
		eNB6.x2++ <--> Eth10G <--> eNB9.x2++;
		eNB6.x2++ <--> Eth10G <--> eNB10.x2++;
		eNB6.x2++ <--> Eth10G <--> eNB11.x2++;
		eNB6.x2++ <--> Eth10G <--> eNB12.x2++;
		eNB6.x2++ <--> Eth10G <--> eNB13.x2++;
		eNB6.x2++ <--> Eth10G <--> eNB14.x2++;
		eNB6.x2++ <--> Eth10G <--> eNB15.x2++;
		eNB6.x2++ <--> Eth10G <--> eNB16.x2++;
		eNB6.x2++ <--> Eth10G <--> eNB17.x2++;
		eNB6.x2++ <--> Eth10G <--> eNB18.x2++;
		eNB6.x2++ <--> Eth10G <--> eNB19.x2++;
		eNB6.x2++ <--> Eth10G <--> eNB20.x2++;
		eNB6.x2++ <--> Eth10G <--> eNB21.x2++;
		eNB6.x2++ <--> Eth10G <--> eNB22.x2++;
		eNB6.x2++ <--> Eth10G <--> eNB23.x2++;
		eNB6.x2++ <--> Eth10G <--> eNB24.x2++;
		eNB6.x2++ <--> Eth10G <--> eNB25.x2++;
		eNB6.x2++ <--> Eth10G <--> eNB26.x2++;
		eNB6.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB6.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB6.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB6.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB6.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB6.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB7.x2++ <--> Eth10G <--> eNB8.x2++;
		eNB7.x2++ <--> Eth10G <--> eNB9.x2++;
		eNB7.x2++ <--> Eth10G <--> eNB10.x2++;
		eNB7.x2++ <--> Eth10G <--> eNB11.x2++;
		eNB7.x2++ <--> Eth10G <--> eNB12.x2++;
		eNB7.x2++ <--> Eth10G <--> eNB13.x2++;
		eNB7.x2++ <--> Eth10G <--> eNB14.x2++;
		eNB7.x2++ <--> Eth10G <--> eNB15.x2++;
		eNB7.x2++ <--> Eth10G <--> eNB16.x2++;
		eNB7.x2++ <--> Eth10G <--> eNB17.x2++;
		eNB7.x2++ <--> Eth10G <--> eNB18.x2++;
		eNB7.x2++ <--> Eth10G <--> eNB19.x2++;
		eNB7.x2++ <--> Eth10G <--> eNB20.x2++;
		eNB7.x2++ <--> Eth10G <--> eNB21.x2++;
		eNB7.x2++ <--> Eth10G <--> eNB22.x2++;
		eNB7.x2++ <--> Eth10G <--> eNB23.x2++;
		eNB7.x2++ <--> Eth10G <--> eNB24.x2++;
		eNB7.x2++ <--> Eth10G <--> eNB25.x2++;
		eNB7.x2++ <--> Eth10G <--> eNB26.x2++;
		eNB7.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB7.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB7.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB7.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB7.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB7.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB8.x2++ <--> Eth10G <--> eNB9.x2++;
		eNB8.x2++ <--> Eth10G <--> eNB10.x2++;
		eNB8.x2++ <--> Eth10G <--> eNB11.x2++;
		eNB8.x2++ <--> Eth10G <--> eNB12.x2++;
		eNB8.x2++ <--> Eth10G <--> eNB13.x2++;
		eNB8.x2++ <--> Eth10G <--> eNB14.x2++;
		eNB8.x2++ <--> Eth10G <--> eNB15.x2++;
		eNB8.x2++ <--> Eth10G <--> eNB16.x2++;
		eNB8.x2++ <--> Eth10G <--> eNB17.x2++;
		eNB8.x2++ <--> Eth10G <--> eNB18.x2++;
		eNB8.x2++ <--> Eth10G <--> eNB19.x2++;
		eNB8.x2++ <--> Eth10G <--> eNB20.x2++;
		eNB8.x2++ <--> Eth10G <--> eNB21.x2++;
		eNB8.x2++ <--> Eth10G <--> eNB22.x2++;
		eNB8.x2++ <--> Eth10G <--> eNB23.x2++;
		eNB8.x2++ <--> Eth10G <--> eNB24.x2++;
		eNB8.x2++ <--> Eth10G <--> eNB25.x2++;
		eNB8.x2++ <--> Eth10G <--> eNB26.x2++;
		eNB8.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB8.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB8.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB8.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB8.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB8.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB9.x2++ <--> Eth10G <--> eNB10.x2++;
		eNB9.x2++ <--> Eth10G <--> eNB11.x2++;
		eNB9.x2++ <--> Eth10G <--> eNB12.x2++;
		eNB9.x2++ <--> Eth10G <--> eNB13.x2++;
		eNB9.x2++ <--> Eth10G <--> eNB14.x2++;
		eNB9.x2++ <--> Eth10G <--> eNB15.x2++;
		eNB9.x2++ <--> Eth10G <--> eNB16.x2++;
		eNB9.x2++ <--> Eth10G <--> eNB17.x2++;
		eNB9.x2++ <--> Eth10G <--> eNB18.x2++;
		eNB9.x2++ <--> Eth10G <--> eNB19.x2++;
		eNB9.x2++ <--> Eth10G <--> eNB20.x2++;
		eNB9.x2++ <--> Eth10G <--> eNB21.x2++;
		eNB9.x2++ <--> Eth10G <--> eNB22.x2++;
		eNB9.x2++ <--> Eth10G <--> eNB23.x2++;
		eNB9.x2++ <--> Eth10G <--> eNB24.x2++;
		eNB9.x2++ <--> Eth10G <--> eNB25.x2++;
		eNB9.x2++ <--> Eth10G <--> eNB26.x2++;
		eNB9.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB9.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB9.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB9.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB9.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB9.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB10.x2++ <--> Eth10G <--> eNB11.x2++;
		eNB10.x2++ <--> Eth10G <--> eNB12.x2++;
		eNB10.x2++ <--> Eth10G <--> eNB13.x2++;
		eNB10.x2++ <--> Eth10G <--> eNB14.x2++;
		eNB10.x2++ <--> Eth10G <--> eNB15.x2++;
		eNB10.x2++ <--> Eth10G <--> eNB16.x2++;
		eNB10.x2++ <--> Eth10G <--> eNB17.x2++;
		eNB10.x2++ <--> Eth10G <--> eNB18.x2++;
		eNB10.x2++ <--> Eth10G <--> eNB19.x2++;
		eNB10.x2++ <--> Eth10G <--> eNB20.x2++;
		eNB10.x2++ <--> Eth10G <--> eNB21.x2++;
		eNB10.x2++ <--> Eth10G <--> eNB22.x2++;
		eNB10.x2++ <--> Eth10G <--> eNB23.x2++;
		eNB10.x2++ <--> Eth10G <--> eNB24.x2++;
		eNB10.x2++ <--> Eth10G <--> eNB25.x2++;
		eNB10.x2++ <--> Eth10G <--> eNB26.x2++;
		eNB10.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB10.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB10.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB10.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB10.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB10.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB11.x2++ <--> Eth10G <--> eNB12.x2++;
		eNB11.x2++ <--> Eth10G <--> eNB13.x2++;
		eNB11.x2++ <--> Eth10G <--> eNB14.x2++;
		eNB11.x2++ <--> Eth10G <--> eNB15.x2++;
		eNB11.x2++ <--> Eth10G <--> eNB16.x2++;
		eNB11.x2++ <--> Eth10G <--> eNB17.x2++;
		eNB11.x2++ <--> Eth10G <--> eNB18.x2++;
		eNB11.x2++ <--> Eth10G <--> eNB19.x2++;
		eNB11.x2++ <--> Eth10G <--> eNB20.x2++;
		eNB11.x2++ <--> Eth10G <--> eNB21.x2++;
		eNB11.x2++ <--> Eth10G <--> eNB22.x2++;
		eNB11.x2++ <--> Eth10G <--> eNB23.x2++;
		eNB11.x2++ <--> Eth10G <--> eNB24.x2++;
		eNB11.x2++ <--> Eth10G <--> eNB25.x2++;
		eNB11.x2++ <--> Eth10G <--> eNB26.x2++;
		eNB11.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB11.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB11.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB11.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB11.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB11.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB12.x2++ <--> Eth10G <--> eNB13.x2++;
		eNB12.x2++ <--> Eth10G <--> eNB14.x2++;
		eNB12.x2++ <--> Eth10G <--> eNB15.x2++;
		eNB12.x2++ <--> Eth10G <--> eNB16.x2++;
		eNB12.x2++ <--> Eth10G <--> eNB17.x2++;
		eNB12.x2++ <--> Eth10G <--> eNB18.x2++;
		eNB12.x2++ <--> Eth10G <--> eNB19.x2++;
		eNB12.x2++ <--> Eth10G <--> eNB20.x2++;
		eNB12.x2++ <--> Eth10G <--> eNB21.x2++;
		eNB12.x2++ <--> Eth10G <--> eNB22.x2++;
		eNB12.x2++ <--> Eth10G <--> eNB23.x2++;
		eNB12.x2++ <--> Eth10G <--> eNB24.x2++;
		eNB12.x2++ <--> Eth10G <--> eNB25.x2++;
		eNB12.x2++ <--> Eth10G <--> eNB26.x2++;
		eNB12.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB12.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB12.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB12.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB12.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB12.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB13.x2++ <--> Eth10G <--> eNB14.x2++;
		eNB13.x2++ <--> Eth10G <--> eNB15.x2++;
		eNB13.x2++ <--> Eth10G <--> eNB16.x2++;
		eNB13.x2++ <--> Eth10G <--> eNB17.x2++;
		eNB13.x2++ <--> Eth10G <--> eNB18.x2++;
		eNB13.x2++ <--> Eth10G <--> eNB19.x2++;
		eNB13.x2++ <--> Eth10G <--> eNB20.x2++;
		eNB13.x2++ <--> Eth10G <--> eNB21.x2++;
		eNB13.x2++ <--> Eth10G <--> eNB22.x2++;
		eNB13.x2++ <--> Eth10G <--> eNB23.x2++;
		eNB13.x2++ <--> Eth10G <--> eNB24.x2++;
		eNB13.x2++ <--> Eth10G <--> eNB25.x2++;
		eNB13.x2++ <--> Eth10G <--> eNB26.x2++;
		eNB13.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB13.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB13.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB13.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB13.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB13.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB14.x2++ <--> Eth10G <--> eNB15.x2++;
		eNB14.x2++ <--> Eth10G <--> eNB16.x2++;
		eNB14.x2++ <--> Eth10G <--> eNB17.x2++;
		eNB14.x2++ <--> Eth10G <--> eNB18.x2++;
		eNB14.x2++ <--> Eth10G <--> eNB19.x2++;
		eNB14.x2++ <--> Eth10G <--> eNB20.x2++;
		eNB14.x2++ <--> Eth10G <--> eNB21.x2++;
		eNB14.x2++ <--> Eth10G <--> eNB22.x2++;
		eNB14.x2++ <--> Eth10G <--> eNB23.x2++;
		eNB14.x2++ <--> Eth10G <--> eNB24.x2++;
		eNB14.x2++ <--> Eth10G <--> eNB25.x2++;
		eNB14.x2++ <--> Eth10G <--> eNB26.x2++;
		eNB14.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB14.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB14.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB14.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB14.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB14.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB15.x2++ <--> Eth10G <--> eNB16.x2++;
		eNB15.x2++ <--> Eth10G <--> eNB17.x2++;
		eNB15.x2++ <--> Eth10G <--> eNB18.x2++;
		eNB15.x2++ <--> Eth10G <--> eNB19.x2++;
		eNB15.x2++ <--> Eth10G <--> eNB20.x2++;
		eNB15.x2++ <--> Eth10G <--> eNB21.x2++;
		eNB15.x2++ <--> Eth10G <--> eNB22.x2++;
		eNB15.x2++ <--> Eth10G <--> eNB23.x2++;
		eNB15.x2++ <--> Eth10G <--> eNB24.x2++;
		eNB15.x2++ <--> Eth10G <--> eNB25.x2++;
		eNB15.x2++ <--> Eth10G <--> eNB26.x2++;
		eNB15.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB15.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB15.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB15.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB15.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB15.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB16.x2++ <--> Eth10G <--> eNB17.x2++;
		eNB16.x2++ <--> Eth10G <--> eNB18.x2++;
		eNB16.x2++ <--> Eth10G <--> eNB19.x2++;
		eNB16.x2++ <--> Eth10G <--> eNB20.x2++;
		eNB16.x2++ <--> Eth10G <--> eNB21.x2++;
		eNB16.x2++ <--> Eth10G <--> eNB22.x2++;
		eNB16.x2++ <--> Eth10G <--> eNB23.x2++;
		eNB16.x2++ <--> Eth10G <--> eNB24.x2++;
		eNB16.x2++ <--> Eth10G <--> eNB25.x2++;
		eNB16.x2++ <--> Eth10G <--> eNB26.x2++;
		eNB16.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB16.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB16.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB16.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB16.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB16.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB17.x2++ <--> Eth10G <--> eNB18.x2++;
		eNB17.x2++ <--> Eth10G <--> eNB19.x2++;
		eNB17.x2++ <--> Eth10G <--> eNB20.x2++;
		eNB17.x2++ <--> Eth10G <--> eNB21.x2++;
		eNB17.x2++ <--> Eth10G <--> eNB22.x2++;
		eNB17.x2++ <--> Eth10G <--> eNB23.x2++;
		eNB17.x2++ <--> Eth10G <--> eNB24.x2++;
		eNB17.x2++ <--> Eth10G <--> eNB25.x2++;
		eNB17.x2++ <--> Eth10G <--> eNB26.x2++;
		eNB17.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB17.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB17.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB17.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB17.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB17.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB18.x2++ <--> Eth10G <--> eNB19.x2++;
		eNB18.x2++ <--> Eth10G <--> eNB20.x2++;
		eNB18.x2++ <--> Eth10G <--> eNB21.x2++;
		eNB18.x2++ <--> Eth10G <--> eNB22.x2++;
		eNB18.x2++ <--> Eth10G <--> eNB23.x2++;
		eNB18.x2++ <--> Eth10G <--> eNB24.x2++;
		eNB18.x2++ <--> Eth10G <--> eNB25.x2++;
		eNB18.x2++ <--> Eth10G <--> eNB26.x2++;
		eNB18.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB18.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB18.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB18.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB18.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB18.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB19.x2++ <--> Eth10G <--> eNB20.x2++;
		eNB19.x2++ <--> Eth10G <--> eNB21.x2++;
		eNB19.x2++ <--> Eth10G <--> eNB22.x2++;
		eNB19.x2++ <--> Eth10G <--> eNB23.x2++;
		eNB19.x2++ <--> Eth10G <--> eNB24.x2++;
		eNB19.x2++ <--> Eth10G <--> eNB25.x2++;
		eNB19.x2++ <--> Eth10G <--> eNB26.x2++;
		eNB19.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB19.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB19.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB19.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB19.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB19.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB20.x2++ <--> Eth10G <--> eNB21.x2++;
		eNB20.x2++ <--> Eth10G <--> eNB22.x2++;
		eNB20.x2++ <--> Eth10G <--> eNB23.x2++;
		eNB20.x2++ <--> Eth10G <--> eNB24.x2++;
		eNB20.x2++ <--> Eth10G <--> eNB25.x2++;
		eNB20.x2++ <--> Eth10G <--> eNB26.x2++;
		eNB20.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB20.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB20.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB20.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB20.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB20.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB21.x2++ <--> Eth10G <--> eNB22.x2++;
		eNB21.x2++ <--> Eth10G <--> eNB23.x2++;
		eNB21.x2++ <--> Eth10G <--> eNB24.x2++;
		eNB21.x2++ <--> Eth10G <--> eNB25.x2++;
		eNB21.x2++ <--> Eth10G <--> eNB26.x2++;
		eNB21.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB21.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB21.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB21.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB21.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB21.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB22.x2++ <--> Eth10G <--> eNB23.x2++;
		eNB22.x2++ <--> Eth10G <--> eNB24.x2++;
		eNB22.x2++ <--> Eth10G <--> eNB25.x2++;
		eNB22.x2++ <--> Eth10G <--> eNB26.x2++;
		eNB22.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB22.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB22.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB22.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB22.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB22.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB23.x2++ <--> Eth10G <--> eNB24.x2++;
		eNB23.x2++ <--> Eth10G <--> eNB25.x2++;
		eNB23.x2++ <--> Eth10G <--> eNB26.x2++;
		eNB23.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB23.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB23.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB23.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB23.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB23.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB24.x2++ <--> Eth10G <--> eNB25.x2++;
		eNB24.x2++ <--> Eth10G <--> eNB26.x2++;
		eNB24.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB24.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB24.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB24.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB24.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB24.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB25.x2++ <--> Eth10G <--> eNB26.x2++;
		eNB25.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB25.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB25.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB25.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB25.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB25.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB26.x2++ <--> Eth10G <--> eNB27.x2++;
		eNB26.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB26.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB26.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB26.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB26.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB27.x2++ <--> Eth10G <--> eNB28.x2++;
		eNB27.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB27.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB27.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB27.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB28.x2++ <--> Eth10G <--> eNB29.x2++;
		eNB28.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB28.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB28.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB29.x2++ <--> Eth10G <--> eNB30.x2++;
		eNB29.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB29.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB30.x2++ <--> Eth10G <--> eNB31.x2++;
		eNB30.x2++ <--> Eth10G <--> eNB32.x2++;
		eNB31.x2++ <--> Eth10G <--> eNB32.x2++;
}
