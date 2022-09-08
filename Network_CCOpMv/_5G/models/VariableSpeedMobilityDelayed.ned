//package inet.mobility.single;
package _5G.models;

import inet.mobility.base.MovingMobilityBase;

simple VariableSpeedMobilityDelayed extends MovingMobilityBase
{
    parameters:
        double initialX @unit(m) = default(uniform(constraintAreaMinX, constraintAreaMaxX));
        double initialY @unit(m) = default(uniform(constraintAreaMinY, constraintAreaMaxY));
        double initialZ @unit(m) = default(nanToZero(uniform(constraintAreaMinZ, constraintAreaMaxZ)));
        double initialMovementHeading @unit(deg) = default(uniform(0deg, 360deg)); // initial heading
        double initialMovementElevation @unit(deg) = default(0deg); // initial elevation
        //volatile double initialSpeed @unit(mps);
        //volatile double initialSpeedY @unit(mps);
        double startTime @unit(s) = default(0s);					// movement start time
        double endTime @unit(s) = default(99999s); // movement end time
        bool initFromDisplayString = default(true); // enables one time initialization from the subject module's display string
        volatile double changeInterval @unit(s); // frequency of changing speed
        volatile double meanSpeed @unit(mps); // speed is normally distributed
        volatile double standardDeviation; // standard deviation of the normal distribution
        @class(VariableSpeedMobilityDelayed);
}