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

#include <inet/common/INETDefs.h>
#include <inet/mobility/base/LineSegmentsMobilityBase.h>

#ifndef __INET_VARIABLESPEEDMOBILITY_H
#define __INET_VARIABLESPEEDMOBILITY_H

namespace inet {

class INET_API VariableSpeedMobility : public LineSegmentsMobilityBase
{
    protected:
        cPar *changeIntervalParameter = nullptr;
        cPar *meanSpeedParameter = nullptr;
        cPar *standardDeviationParameter = nullptr;

        Quaternion quaternion;
        simtime_t previousChange;
        Coord sourcePosition;

    protected:
        virtual int numInitStages() const override { return NUM_INIT_STAGES; }
        virtual void initialize(int stage) override;
        virtual void move() override;
        virtual void setTargetPosition() override;

    public:
        VariableSpeedMobility();
};

} // namespace inet

#endif  // ifndef __INET_VARIABLESPEEDMOBILITY
