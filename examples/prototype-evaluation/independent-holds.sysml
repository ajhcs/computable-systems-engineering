package PrototypeIndependentHolds {
 private import DummyRehearsal::*;
 requirement <R_D_HOLD_PRESERVE> PreserveUnrelatedHolds {
  doc /*Bounded local fixture obligation: adding or releasing one identified hold preserves every other captured hold on that record. This is not proof of issuer authority or real notice completeness.*/
  doc cseSource /*CSE-SOURCE/2.0
  DUMMY-HOLDS-1
  */
  subject unit = DummyRehearsal::probe;
  require constraint sampleRule {
   doc cse /*CSE-REQ/2.0
   Whenever unit.holdChangeAttempted = true, unit shall always satisfy unit.unrelatedHoldsPreserved = true.
   */
  }
 }
}
