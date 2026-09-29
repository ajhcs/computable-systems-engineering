package ToolLibraryScenario {
    doc /* Synthetic operational scenario: normal borrowing flow. */

    part def ToolLibrary;
    part system : ToolLibrary;
    part def Borrower;
    part borrower : Borrower;

    use case <UC_REQUEST> BorrowTool {
        subject unit = system;
        actor user = borrower;
        doc /* Borrower requests a tool; the system assesses availability and records an allocation.
               This narrative does not define executable guards or effects. */
    }
}
