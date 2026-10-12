package LibraryDeadline {
    private import ScalarValues::Boolean;
    doc /* Original synthetic teaching threshold, not an accepted real-system requirement. */
    doc cseClock /* CSE-CLOCK/2.0
    period 1 second */
    part def ToolLibrary {
        in attribute request : Boolean;
        out attribute recorded : Boolean;
    }
    part system : ToolLibrary;
    requirement <R_RECORD> TimelyRecord {
        doc cseSource /* CSE-SOURCE/2.0
        SYN-DIAGRAM-01 */
        subject unit = system;
        require constraint responseTime {
            doc cse /* CSE-REQ/2.0
            Upon unit.request = true, unit shall within 2 seconds
            satisfy unit.recorded = true. */
        }
    }
}
