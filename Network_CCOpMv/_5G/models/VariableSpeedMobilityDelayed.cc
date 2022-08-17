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
//

#include "VariableSpeedMobilityDelayed.h"

namespace omnetpp {

VariableSpeedMobilityDelayed::VariableSpeedMobilityDelayed() {
}

void VariableSpeedMobilityDelayed::initialize(int stage) {
    LineSegmentsMobilityBase::initialize(stage);
    if (stage == inet::INITSTAGE_LOCAL) {
        inet::rad heading = inet::deg(par("initialMovementHeading"));
        inet::rad elevation = inet::deg(par("initialMovementElevation"));
        startTime = par("startTime");
        endTime = par("endTime");
        changeIntervalParameter = &par("changeInterval");
        meanSpeedParameter = &par("meanSpeed");
        standardDeviationParameter = &par("standardDeviation");
        quaternion = inet::Quaternion(inet::EulerAngles(heading, -elevation, inet::rad(0)));
        WATCH(lastVelocity);
    }
}

void VariableSpeedMobilityDelayed::move(){
    simtime_t now = simTime();
    inet::rad dummyAngle;

    if (now == nextChange) {
        lastPosition = targetPosition;
        handleIfOutside(REFLECT, targetPosition, lastVelocity, dummyAngle, dummyAngle, quaternion);
        EV_INFO << "reached current target position = " << lastPosition << endl;
        setTargetPosition();
        EV_INFO << "new target position = " << targetPosition << ", next change = " << nextChange << endl;
        lastVelocity = (targetPosition - lastPosition) / (nextChange - simTime()).dbl();
        EV << "last velocity = " << lastVelocity << endl;
        handleIfOutside(REFLECT, targetPosition, lastVelocity, dummyAngle, dummyAngle, quaternion);
    }
    else if (now > lastUpdate) {
        ASSERT(nextChange == -1 || now < nextChange);
        double alpha = (now - previousChange) / (nextChange - previousChange);
        lastPosition = sourcePosition * (1 - alpha) + targetPosition * alpha;
        handleIfOutside(REFLECT, targetPosition, lastVelocity, dummyAngle, dummyAngle, quaternion);
    }
}

//Uses second rng
void VariableSpeedMobilityDelayed::setTargetPosition(){
    quaternion.normalize();
    inet::Coord direction = quaternion.rotate(inet::Coord::X_AXIS);
    float speed = normal(*meanSpeedParameter,standardDeviationParameter->doubleValue(), 1);

    simtime_t nextChangeInterval = *changeIntervalParameter;
    EV_DEBUG << "interval: " << nextChangeInterval << endl;
    sourcePosition = lastPosition;
    if (simTime() >= startTime && simTime() <= endTime){
        targetPosition = lastPosition + direction * speed * nextChangeInterval.dbl();
    }
    else{
        targetPosition = lastPosition;
    }
    previousChange = simTime();
    nextChange = previousChange + nextChangeInterval;
}

}
