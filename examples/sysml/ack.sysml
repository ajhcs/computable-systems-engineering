package AckExample {
    private import ScalarValues::Boolean;

    doc cseClock /*
    CSE-CLOCK/2.0
    period 1 second
    */

    part def Controller {
        in attribute request : Boolean;
        out attribute acknowledged : Boolean;
    }
    part controller : Controller;

    requirement <R_ACK> TimelyAcknowledgment {
        doc cseSource /*
        CSE-SOURCE/2.0
        SYN-01
        */
        subject unit = controller;
        require constraint responseTime {
            doc cse /*
            CSE-REQ/2.0
            Upon unit.request = true, unit shall within 2 seconds
            satisfy unit.acknowledged = true.
            */
        }
    }
}
