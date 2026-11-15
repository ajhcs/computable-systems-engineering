package ToolLibraryConcept {
    private import ScalarValues::Boolean;

    doc /* Synthetic system concept: improve access to shared tools. */

    part def ToolLibrary {
        doc /* System boundary: request intake, allocation, and return tracking. */
        in attribute requestReceived : Boolean;
        out attribute allocationRecorded : Boolean;
    }

    concern <N_ACCESS> AccessibleTools {
        doc /* Stakeholders need a dependable way to obtain shared tools. */
    }

    action def AllocateTool {
        doc /* Candidate function: allocate an available tool to a request. */
    }

    part candidateWeb : ToolLibrary {
        doc /* Proposed web-assisted concept; feasibility remains unassessed. */
    }
    part candidateKiosk : ToolLibrary {
        doc /* Proposed kiosk concept; feasibility remains unassessed. */
    }
}
