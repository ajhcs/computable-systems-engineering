package EventExample {
    private import ScalarValues::String;

    doc cseClock /*
    CSE-CLOCK/2.0
    period 1 millisecond
    */

    part def Controller {
        in event occurrence requestReceived {
            attribute correlationId : String;
        }
        out event occurrence ackSent {
            attribute correlationId : String;
        }
    }
    part controller : Controller;

    requirement <R_EVENT> AcknowledgeEachRequest {
        doc cseSource /*
        CSE-SOURCE/2.0
        SYN-02
        */
        subject unit = controller;
        require constraint responseTime {
            doc cse /*
            CSE-EVENT/2.0
            Each unit.requestReceived shall within 2 seconds have
            unit.ackSent with matching correlationId.
            */
        }
    }
}
