//
// Author: Emin Ilker Cetinbas (niw3_at_yahoo_d0t_com)
// Copyright (C) 2005 Emin Ilker Cetinbas
//
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

#include "LinearMobilityDelayed.h"

namespace omnetpp {

LinearMobilityDelayed::LinearMobilityDelayed()
{
    speed = 10;
}

void LinearMobilityDelayed::initialize(int stage)
{
    MovingMobilityBase::initialize(stage);

    EV_TRACE << "initializing LinearMobility stage " << stage << endl;
    if (stage == inet::INITSTAGE_LOCAL) {
        speed = par("speed");
        startTime = par("startTime");
        endTime = par("endTime");
        stationary = (speed == 0);
        inet::rad heading = inet::deg(par("initialMovementHeading"));
        inet::rad elevation = inet::deg(par("initialMovementElevation"));
        inet::Coord direction = inet::Quaternion(inet::EulerAngles(heading, -elevation, inet::rad(0))).rotate(inet::Coord::X_AXIS);

        lastVelocity = direction * speed;
    }
}

void LinearMobilityDelayed::move()
{
    if(simTime() >= startTime && simTime() <= endTime){
        double elapsedTime = (simTime() - lastUpdate).dbl();
        lastPosition += lastVelocity * elapsedTime;

        // do something if we reach the wall
        inet::Coord dummyCoord;
        handleIfOutside(REFLECT, dummyCoord, lastVelocity);
    }
}

}

