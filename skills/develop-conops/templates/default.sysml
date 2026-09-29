package ToolLibraryConops {
    doc /* Synthetic CONOPS: staffed and unstaffed operating modes are candidates. */

    part def ToolLibrary;
    part system : ToolLibrary;
    part def Borrower;
    part borrower : Borrower;

    use case <UC_BORROW> BorrowTool {
        subject unit = system;
        actor user = borrower;
        objective {
            doc /* The borrower receives an allocated tool and return instructions. */
        }
    }
}
