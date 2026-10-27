package DummyRehearsal {
 private import ScalarValues::Boolean;
 doc /*Bounded verification harness for an optional local dummy prototype. The harness evaluates supplied observations and does not execute the application or native workflow.*/
 doc cseClock /*CSE-CLOCK/2.0
 period 1 second
 */
 part def WorksheetProbe {
  in attribute stockMismatch : Boolean;
  in attribute adjustmentAuthorized : Boolean;
  in attribute revocationEffective : Boolean;
  in attribute holdActive : Boolean;
  in attribute retentionBasisKnown : Boolean;
  in attribute dispositionAuthorityKnown : Boolean;
  in attribute readAuthorized : Boolean;
  in attribute issueAuthorized : Boolean;
  out attribute issueCommitted : Boolean;
  out attribute adjustmentCommitted : Boolean;
  out attribute adjustmentAuditRecorded : Boolean;
  out attribute readServed : Boolean;
  out attribute dispositionCommitted : Boolean;
  out attribute dispositionAuditRecorded : Boolean;
  out attribute copiesAccounted : Boolean;
 }
 part probe : WorksheetProbe;
 requirement <R_D_STOCK> Check1 {
  doc /*Stock discrepancy blocks issue. Proposed test obligation only.*/
  doc cseSource /*CSE-SOURCE/2.0
 DUMMY-REPAIR-1
 */
  subject unit = probe;
  require constraint sampleRule {
   doc cse /*CSE-REQ/2.0
   Whenever unit.stockMismatch = true, unit shall always satisfy unit.issueCommitted = false.
   */
  }
 }
 requirement <R_D_ADJUST_AUTH> Check2 {
  doc /*Unapproved stock adjustment is blocked. Proposed test obligation only.*/
  doc cseSource /*CSE-SOURCE/2.0
 DUMMY-REPAIR-1
 */
  subject unit = probe;
  require constraint sampleRule {
   doc cse /*CSE-REQ/2.0
   Whenever unit.adjustmentAuthorized = false, unit shall always satisfy unit.adjustmentCommitted = false.
   */
  }
 }
 requirement <R_D_ADJUST_AUDIT> Check3 {
  doc /*Committed stock adjustment is recorded. Proposed test obligation only.*/
  doc cseSource /*CSE-SOURCE/2.0
 DUMMY-REPAIR-1
 */
  subject unit = probe;
  require constraint sampleRule {
   doc cse /*CSE-REQ/2.0
   Whenever unit.adjustmentCommitted = true, unit shall always satisfy unit.adjustmentAuditRecorded = true.
   */
  }
 }
 requirement <R_D_REVOKE> Check4 {
  doc /*Effective revocation blocks a served read. Proposed test obligation only.*/
  doc cseSource /*CSE-SOURCE/2.0
 DUMMY-REPAIR-1
 */
  subject unit = probe;
  require constraint sampleRule {
   doc cse /*CSE-REQ/2.0
   Whenever unit.revocationEffective = true, unit shall always satisfy unit.readServed = false.
   */
  }
 }
 requirement <R_D_HOLD> Check5 {
  doc /*Active retention hold blocks disposition. Proposed test obligation only.*/
  doc cseSource /*CSE-SOURCE/2.0
 DUMMY-REPAIR-1
 */
  subject unit = probe;
  require constraint sampleRule {
   doc cse /*CSE-REQ/2.0
   Whenever unit.holdActive = true, unit shall always satisfy unit.dispositionCommitted = false.
   */
  }
 }
 requirement <R_D_BASIS> Check6 {
  doc /*Unknown retention basis blocks disposition. Proposed test obligation only.*/
  doc cseSource /*CSE-SOURCE/2.0
 DUMMY-REPAIR-1
 */
  subject unit = probe;
  require constraint sampleRule {
   doc cse /*CSE-REQ/2.0
   Whenever unit.retentionBasisKnown = false, unit shall always satisfy unit.dispositionCommitted = false.
   */
  }
 }
 requirement <R_D_AUTH> Check7 {
  doc /*Unknown disposition authority blocks disposition. Proposed test obligation only.*/
  doc cseSource /*CSE-SOURCE/2.0
 DUMMY-REPAIR-1
 */
  subject unit = probe;
  require constraint sampleRule {
   doc cse /*CSE-REQ/2.0
   Whenever unit.dispositionAuthorityKnown = false, unit shall always satisfy unit.dispositionCommitted = false.
   */
  }
 }
 requirement <R_D_AUDIT> Check8 {
  doc /*Committed disposition has an audit record. Proposed test obligation only.*/
  doc cseSource /*CSE-SOURCE/2.0
 DUMMY-REPAIR-1
 */
  subject unit = probe;
  require constraint sampleRule {
   doc cse /*CSE-REQ/2.0
   Whenever unit.dispositionCommitted = true, unit shall always satisfy unit.dispositionAuditRecorded = true.
   */
  }
 }
 requirement <R_D_COPIES> Check9 {
  doc /*Committed disposition has declared copy accounting. Proposed test obligation only.*/
  doc cseSource /*CSE-SOURCE/2.0
 DUMMY-REPAIR-1
 */
  subject unit = probe;
  require constraint sampleRule {
   doc cse /*CSE-REQ/2.0
   Whenever unit.dispositionCommitted = true, unit shall always satisfy unit.copiesAccounted = true.
   */
  }
 }
}
