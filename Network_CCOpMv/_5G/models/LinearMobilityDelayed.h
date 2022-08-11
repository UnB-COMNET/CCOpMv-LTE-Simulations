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

#ifndef __INET_LINEARMOBILITYDELAYED_H
#define __INET_LINEARMOBILITYDELAYED_H

#include "inet/common/INETDefs.h"
#include "inet/mobility/base/MovingMobilityBase.h"
#include <inet/common/INETMath.h>
#include <omnetpp.h>

namespace omnetpp {

/**
 *
 *
 *
 */
class LinearMobilityDelayed : public inet::MovingMobilityBase
{
  protected:
    double speed;
    double startTime;

  protected:
    virtual int numInitStages() const override { return inet::NUM_INIT_STAGES; }

    /** @brief Initializes mobility model parameters.*/
    virtual void initialize(int stage) override;

    /** @brief Move the host*/
    virtual void move() override;

  public:
    virtual double getMaxSpeed() const override { return speed; }
    LinearMobilityDelayed();
};

Define_Module(LinearMobilityDelayed);

} // namespace inet

#endif // ifndef __INET_LINEARMOBILITYDELAYED_H

