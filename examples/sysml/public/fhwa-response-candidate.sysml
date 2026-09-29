package FHWAResponseCandidate {
    private import ScalarValues::String;

    doc /* Candidate interpretation of FHWA-HOP-13-047 section 3.6.2.
           The source also requires request processing and an appropriate response;
           this slice checks only a proposed per-request timing association.
           requestId and complete event capture are modeling assumptions. */
    doc cseClock /* CSE-CLOCK/2.0
    period 1 millisecond */

    part def OwnerCenter {
        in event occurrence requestLastByte {
            attribute requestId : String;
        }
        out event occurrence responseFirstByte {
            attribute requestId : String;
        }
    }
    part center : OwnerCenter;

    requirement <R_FHWA_TIME> CandidateResponseTiming {
        doc cseSource /* CSE-SOURCE/2.0
        FHWA_3_6_2 */
        subject unit = center;
        require constraint firstByteDeadline {
            doc cse /* CSE-EVENT/2.0
            Each unit.requestLastByte shall within 1 minute have
            unit.responseFirstByte with matching requestId. */
        }
    }
}
