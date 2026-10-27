package PrototypeAuthorization {
 private import DummyRehearsal::*;
 requirement <R_D_READ_SCOPE> AuthorizedRead {
  doc cseSource /*CSE-SOURCE/2.0
  DUMMY-REPAIR-1
  */
  subject unit = DummyRehearsal::probe;
  require constraint sampleRule {
   doc cse /*CSE-REQ/2.0
   Whenever unit.readAuthorized = false, unit shall always satisfy unit.readServed = false.
   */
  }
 }
 requirement <R_D_ISSUE_SCOPE> AuthorizedIssue {
  doc cseSource /*CSE-SOURCE/2.0
  DUMMY-REPAIR-1
  */
  subject unit = DummyRehearsal::probe;
  require constraint sampleRule {
   doc cse /*CSE-REQ/2.0
   Whenever unit.issueAuthorized = false, unit shall always satisfy unit.issueCommitted = false.
   */
  }
 }
}
