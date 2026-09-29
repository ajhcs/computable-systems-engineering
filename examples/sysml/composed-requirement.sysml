package ComposedAck {
    private import SharedAck::*;

    doc cseClock /*
    CSE-CLOCK/2.0
    period 1 second
    */

    part controller : Controller;

    requirement <R_COMPOSED> TimelyAcknowledgment {
        doc cseSource /* CSE-SOURCE/2.0
        SYN-03 */
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
