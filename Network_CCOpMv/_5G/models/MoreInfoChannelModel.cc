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
    std::vector<double> snrVector;

    RbMap rbmap = lteInfo->getGrantedBlocks();

    snrVector = LteRealisticChannelModel::getSINR(frame, lteInfo);

    Direction dir = (Direction) lteInfo->getDirection();

    MacNodeId ueId = 0;

    if (dir == UL){
            ueId = lteInfo->getSourceId() - UE_MIN_ID;
            emit(idRcvdSinr_, ueId);
    }

    return snrVector;
}
