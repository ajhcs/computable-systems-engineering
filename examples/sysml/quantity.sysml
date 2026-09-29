package AckExample {
    private import ScalarValues::Boolean;
    private import ISQBase::DurationValue;

    doc cseClock /*
    CSE-CLOCK/2.0
    period 1 second
    */

    part def Controller {
        in attribute request : Boolean;
        out attribute elapsed : DurationValue {
            doc cseType /*
            CSE-INT/2.0
            range 0 100 scale 1 unit second
            */
        }
    }
    part controller : Controller;

    requirement <R_DURATION> BoundedElapsed {
        doc cseSource /*
        CSE-SOURCE/2.0
        SYN-04
        */
        subject unit = controller;
        require constraint responseTime {
            doc cse /*
            CSE-REQ/2.0
            Upon unit.request = true, unit shall within 2 seconds
            satisfy unit.elapsed <= 2 second.
            */
        }
    }
}
