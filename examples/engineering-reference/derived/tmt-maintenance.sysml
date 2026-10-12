package TMTMaintenanceDerived {
  doc /* Derived 2026-10-01 from TMT.mdzip 87832a1657ccab023a90a6acfd0dff02d60e2b46, SysML 1.4. New SysML v2 transcription of selected Figure 2 scope, not the engineers' original model. Source code/actions remain opaque; this pack does not execute this lifecycle. Caltech COPYRIGHT and repository license retained in notices/. */
  item def InitComplete;
  item def Finished;
  item def MaintenanceAlignmentSignal;
  item def Abort;
  state def PEASMaintenance {
    doc /* Source StateMachine _17_0_2_3_41e01aa_1383540424302_365385_58121. Selected lifecycle scope only. */
    entry; then Initializing;
    state Initializing {
      doc /* Source _18_0_4_baa02e2_1432924809533_220506_153469. */
      do action InitializePEAS;
    }
    state StandBy {
      doc /* Source _17_0_2_3_41e01aa_1383541688252_643738_65387. */
    }
    state 'Maintenance Alignment' {
      doc /* Source _18_0_4_baa02e2_1437066409415_379651_152422. Composite Abort applies to this state, not only to its final substate. */
      entry action initTimer; then 'Correcting Rigid Body and Segment Figure';
      state 'Correcting Rigid Body and Segment Figure' {
        doc /* Source _18_0_4_baa02e2_1437066502649_816302_152451. */
        do action 'Rigid Body and Segment Figure correction';
      }
      state 'Broad Band Phasing 1um' {
        doc /* Source _18_0_4_baa02e2_1437066536103_963725_152466. */
        do action 'Broad Band Phasing 1um';
      }
      state 'Narrow Band Phasing' {
        doc /* Source _18_0_4_baa02e2_1437066564616_958435_152481. */
        do action 'Narrow Band Phasing';
      }
      transition correctionToBroad
        first 'Correcting Rigid Body and Segment Figure' accept Finished
        do action diffTime then 'Broad Band Phasing 1um';
      transition broadToNarrow
        first 'Broad Band Phasing 1um' accept Finished
        do action diffTime then 'Narrow Band Phasing';
    }
    transition initialized first Initializing accept InitComplete
      do action InitCompleteEffect {
        doc /* New identifier for source unnamed effect _18_0_4_baa02e2_1436386754872_461446_172125: initialization-time logging. Original body remains opaque in source fragment; no implementation translated. */
      } then StandBy;
    transition startAlignment first StandBy accept MaintenanceAlignmentSignal then 'Maintenance Alignment';
    transition abortAlignment first 'Maintenance Alignment' accept Abort then StandBy;
    transition completeAlignment first 'Maintenance Alignment'.'Narrow Band Phasing'
      accept Finished do action FinalDiffTime then StandBy;
    transition finishLifecycle first StandBy accept Finished then done;
  }
}
