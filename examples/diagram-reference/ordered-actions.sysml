package LibraryActions {
    doc /* Original synthetic available-tool path. Unavailability remains outside this selected view.
           Succession specifies ordering, not duration, a data flow, or resource allocation. */
    action def BorrowAvailable {
        first start;
        then action receiveRequest;
        then action assessAvailability;
        then action recordAllocation;
        then done;
    }
    part def ToolLibrary;
    part system : ToolLibrary;
    part def Borrower;
    part borrower : Borrower;
    use case <UC_AVAILABLE> BorrowAvailableTool {
        subject unit = system;
        actor user = borrower;
        doc /* Selected available-tool scenario: receive request, assess availability, record allocation.
               No unavailable branch, timing threshold, or physical allocation is inferred. */
    }
}
