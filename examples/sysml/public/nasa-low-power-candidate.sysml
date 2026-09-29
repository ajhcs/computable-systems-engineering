package NASALowPowerCandidate {
    private import ScalarValues::Boolean;

    doc /* Candidate partial interpretation of Love and Hill, 2015, page 9.
           The source describes low-power configuration until docking/power
           after trans-lunar injection. This clause does not model docking,
           causal power transfer, or the whole mission sequence. */
    doc cseClock /* CSE-CLOCK/2.0
    period 1 minute */

    part def ComanifestedElement {
        in attribute transLunarInjectionComplete : Boolean;
        in attribute supplementaryPowerAvailable : Boolean;
        out attribute lowPowerConfiguration : Boolean;
    }
    part element : ComanifestedElement;

    requirement <R_NASA_LOW> CandidateLowPowerHold {
        doc cseSource /* CSE-SOURCE/2.0
        NASA_LOVE_HILL_P9 */
        subject unit = element;
        require constraint holdUntilPower {
            doc cse /* CSE-REQ/2.0
            Upon unit.transLunarInjectionComplete = true, unit shall until
            unit.supplementaryPowerAvailable = true satisfy
            unit.lowPowerConfiguration = true. */
        }
    }
}
