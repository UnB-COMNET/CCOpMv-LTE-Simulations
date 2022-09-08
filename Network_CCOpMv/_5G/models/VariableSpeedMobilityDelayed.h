// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License
// as published by the Free Software Foundation; either version 2
// of the License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, see <http://www.gnu.org/licenses/>.

#ifndef __NETWORK_CCOPMV_VARIABLESPEEDMOBILITYDELAYED_H
#define __NETWORK_CCOPMV_VARIABLESPEEDMOBILITYDELAYED_H

#include <inet/common/INETDefs.h>
#include <inet/mobility/base/LineSegmentsMobilityBase.h>
#include <inet/common/INETMath.h>
#include <omnetpp.h>

namespace omnetpp {

class VariableSpeedMobilityDelayed : public inet::LineSegmentsMobilityBase
{
    protected:
        inet::cPar *changeIntervalParameter = nullptr;
        inet::cPar *meanSpeedParameter = nullptr;
        inet::cPar *standardDeviationParameter = nullptr;
        inet::Coord initialSpeedFirstSlice;
        inet::Coord initialSpeedLastSlice;

        inet::Quaternion quaternion;
        simtime_t previousChange;
        inet::Coord sourcePosition;
        double startTime;
        double endTime;

    protected:
        virtual int numInitStages() const { return inet::NUM_INIT_STAGES; }
        virtual void initialize(int stage);
        virtual void move();
        virtual void setTargetPosition();

    public:
        VariableSpeedMobilityDelayed();
};

Define_Module(VariableSpeedMobilityDelayed);

}

#endif  //
