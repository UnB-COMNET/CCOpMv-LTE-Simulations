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

#include "MoreInfoChannelModel.h"
#include <iostream>

using namespace omnetpp;

simsignal_t MoreInfoChannelModel::idRcvdSinr_ = registerSignal("idRcvdSinr");

std::vector<double> MoreInfoChannelModel::getSINR(LteAirFrame *frame, UserControlInfo* lteInfo)
{
    std::vector<double> snrV;

    RbMap rbmap = lteInfo->getGrantedBlocks();

    snrV = LteRealisticChannelModel::getSINR(frame, lteInfo);

    Direction dir = (Direction) lteInfo->getDirection();

    MacNodeId ueId = 0;
    MacNodeId id = 0;

    bool doEmit = true;

    RbMap::iterator it;
    std::map<Band, unsigned int>::iterator jt;

    int usedRBs = 0;

    //Get txmode
    TxMode txmode = (TxMode) lteInfo->getTxMode();

    if (dir==UL){
        id = lteInfo->getSourceId();
        // If rank is 1 and we used SMUX to transmit we have to corrupt this packet
        if (txmode == CL_SPATIAL_MULTIPLEXING
               || txmode == OL_SPATIAL_MULTIPLEXING)
        {
           //compare lambda min (smaller eingenvalues of channel matrix) with the threshold used to compute the rank
           if (binder_->phyPisaData.getLambda(id, 1) < lambdaMinTh_)
               doEmit = false;
        }

        //for each Remote unit used to transmit the packet
        for (it = rbmap.begin(); it != rbmap.end(); ++it)
        {
           //for each logical band used to transmit the packet
           for (jt = it->second.begin(); jt != it->second.end(); ++jt)
           {
               //this Rb is not allocated
               if (jt->second == 0)
                   continue;

               //check the antenna used in Das
               if ((lteInfo->getTxMode() == CL_SPATIAL_MULTIPLEXING
                       || lteInfo->getTxMode() == OL_SPATIAL_MULTIPLEXING)
                       && rbmap.size() > 1)
                   //we consider only the snr associated to the LB used
                   if (it->first != lteInfo->getCw())
                       continue;

               usedRBs++;
               int snr = snrV[jt->first];//XXX because jt->first is a Band (=unsigned short)
               if (snr < binder_->phyPisaData.minSnr())
                   doEmit = false;
           }
        }

        if (usedRBs > 0 && (lteInfo->getFrameType() != FEEDBACKPKT) && doEmit){
                ueId = lteInfo->getSourceId() - UE_MIN_ID;
                emit(idRcvdSinr_, ueId);
        }
    }

    return snrV;
}
