package LibraryContext {
    doc /* Original synthetic black-box context. No staffing or algorithm selected. */
    item def Request;
    item def Allocation;
    part def Borrower {
        out item request : Request;
        in item assignedTool : Allocation;
    }
    part def ToolLibrary {
        in item request : Request;
        out item assignedTool : Allocation;
    }
    part borrower : Borrower;
    part system : ToolLibrary;
    flow requestFlow of Request from borrower.request to system.request;
    flow allocationFlow of Allocation from system.assignedTool to borrower.assignedTool;
    concern <N_ACCESS> Access {
        doc /* Borrowers need dependable access to shared tools. This is a need, not a measured obligation. */
    }
}
