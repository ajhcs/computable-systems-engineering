package SharedToolLibrary {
    private import ScalarValues::Boolean;

    doc /* Synthetic shared concept and operational scenario. All timing here
           is illustrative; no real engineer's threshold is represented. */
    doc cseClock /* CSE-CLOCK/2.0
    period 1 second */

    part def ToolLibrary {
        doc /* System boundary: request intake, availability assessment,
               allocation recording, and return tracking. */
        in attribute requestReceived : Boolean;
        out attribute allocationRecorded : Boolean;
    }
    part system : ToolLibrary;
    part def Borrower;
    part borrower : Borrower;

    concern <N_ACCESS> AccessibleTools {
        doc /* Borrowers need dependable access to shared tools.
               Availability and staffing remain open concept questions. */
    }
    action def AllocateTool {
        doc /* Candidate function: allocate an available tool to a request.
               No allocation algorithm has been selected. */
    }
    use case <UC_BORROW> BorrowTool {
        subject unit = system;
        actor user = borrower;
        doc /* Scenario trigger: a borrower requests a tool.
               1. The borrower submits the request.
               2. The system assesses availability.
               3. If a tool is available, the system records its allocation
                  and provides return instructions.
               Tool unavailability is an unresolved alternate outcome.
               These steps are narrative; no executable guards or effects
               are inferred from them. */
    }
    requirement <R_RECORD> RecordAllocation {
        doc cseSource /* CSE-SOURCE/2.0
        SYN-JOINT-01 */
        subject unit = system;
        require constraint responseTime {
            doc cse /* CSE-REQ/2.0
            Upon unit.requestReceived = true, unit shall within 2 seconds
            satisfy unit.allocationRecorded = true. */
        }
    }
}
