package CSEFoundation {
    doc /* Original bounded self-improvement example. Actors/roles and allocation
       criteria are declared proposals, not authenticated engineer decisions.
       The paired foundation profile checks selected structure only. */
    part def CSE;
    part system : CSE;
    part def Engineer;
    part engineer : Engineer;
    part def Assistant;
    part assistant : Assistant;
    part def Checker;
    part checker : Checker;
    part def Simulator;
    part simulator : Simulator;
    concern <N_TRACE> TraceableImprovement {
        doc /* Keep meanings, source revisions and evidence limits clear. */
    }
    action def ReviewSource;
    action def CheckCandidate;
    action def DraftScenario;
    use case <UC_REVIEW> ReviewChange {
        subject unit = system;
        actor owner = engineer;
        actor drafter = assistant;
        doc /* Engineer requests a source-grounded improvement. Assistant reads
           existing evidence, prepares a candidate and reports missing facts.
           Engineer reviews consequential meanings. No behavior is executed. */
    }
}
