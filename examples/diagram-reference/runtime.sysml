package PackRuntime {
    doc /* Repository-grounded structural abstraction at baseline b01ef016.
           Containment represents runtime grouping; calls are documented dependencies,
           not SysML item flows, physical connections, or production deployment. */
    part def SkillLauncher;
    part def CLI;
    part def Adapter;
    part def PilotParser;
    part def BoundedChecker;
    part def Runtime {
        part launcher : SkillLauncher;
        part cli : CLI;
        part adapter : Adapter;
        part pilot : PilotParser;
        part checker : BoundedChecker;
    }
    part runtime : Runtime;
    concern <N_TRUTH> HonestVerdicts {
        doc /* Distinguish parser acceptance, bounded computation, and engineer acceptance. */
    }
    doc architecture /*
    launcher resolves the shared runtime and invokes the CLI.
    CLI calls the adapter.
    adapter invokes the Java pilot through the bridge for parsing and reference validation.
    adapter compiles supported CSE documentation and invokes the bounded language checker.
    Parser acceptance does not establish behavior correctness or engineer acceptance.
    */
}
