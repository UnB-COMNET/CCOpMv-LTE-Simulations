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

#include "Snapshoter.h"

Snapshoter::Snapshoter()
{
    //Constructor.
    //Set pointer to nullptr so the destructor won't crash
    //even if initialize() doesn't get called
    event = nullptr;
}

Snapshoter::~Snapshoter()
{
    //Dispose of dynamically allocated objects
    cancelAndDelete(event);
}

void Snapshoter::initialize()
{
    numUE_ = par("numUE");
    snapshot_ = par("snapshot");
    delay_ = par("delay");

    cModule* cParent = getParentModule();
    //Object used for timing. Just a message.
    event = new cMessage("event");

    if (snapshot_){
        scheduleAt(simTime()+delay_, event);
    }
}

void Snapshoter::handleMessage(cMessage *msg)
{
    if (msg == event) { //msg->isSelfMessage()
        EV << "Taking snapshot\n";
        // register the carrier to the cellInfo module and the binder
        cModule* cParent = getParentModule();
        if (cParent != NULL)   // cInfo is NULL on UEs
        {
            for(int i = 0; i < numUE_; i++){
                snapshot(cParent->getSubmodule("ue", i)->getSubmodule("mobility"));
            }
        }
        //snapshot();
        scheduleAt(simTime()+delay_, event);
    }
    // TODO - Generated method body
}
