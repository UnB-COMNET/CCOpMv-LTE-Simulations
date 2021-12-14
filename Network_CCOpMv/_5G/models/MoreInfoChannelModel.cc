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

bool MoreInfoChannelModel::isError(LteAirFrame *frame, UserControlInfo* lteInfo)
{
    bool is_error;

    RbMap rbmap = lteInfo->getGrantedBlocks();

    is_error = LteRealisticChannelModel::isError(frame, lteInfo);

    Direction dir = (Direction) lteInfo->getDirection();

    MacNodeId ueId = 0;

    RbMap::iterator it;
    std::map<Band, unsigned int>::iterator jt;

    int usedRBs = 0;

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
       }
    }

    if (dir == UL && usedRBs > 0 && (lteInfo->getFrameType() != FEEDBACKPKT)){
            ueId = lteInfo->getSourceId() - UE_MIN_ID;
            emit(idRcvdSinr_, ueId);
    }

    return is_error;
}
