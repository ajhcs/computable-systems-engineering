# Early testability and feedback

Before a consequential design choice, ask how its relevant properties will be
observed and judged at the next useful stage. Review the available intermediate
product now: need statement, requirement, allocation, interface, analysis model,
prototype or implementation increment. State the question it can answer at its
present fidelity and the conclusion it cannot yet support.

For the selected evidence question, identify:

- Observation points and their meaning: input/decision state, internal state,
  committed state or returned output; distinguish these from inferred state.
- Fixtures, access, equipment, reference data, calibration and environmental
  dependencies; retain unavailable resources as limitations or linked questions.
- Setup, reset, capture and interpretation effort, including repeated manual
  work and observer independence where it affects credibility.
- The earliest discriminating check, its expected evidence and a finding that
  would prompt reconsideration of the design assumption or chosen method.

Propose observability, fixture or interface changes when they materially improve
testability. Explain their cost and affected obligations; do not silently change
accepted design intent to simplify a test. A rough prototype may answer one
uncertainty without becoming an implementation baseline.

After each investigation, distinguish a model/implementation defect from wrong
or missing observations, stale sources, an unsuitable method and an unsupported
checker. Multiple causes may coexist. Follow the reported IDs and counterexample
before changing unrelated content. Correct an artifact or capture procedure
within scope, retain the failed evidence, and rerun the relevant check. A relaxed
requirement, narrowed condition or new acceptance criterion remains a proposal.

Stop an unsuccessful repair loop at a proportionate stated effort limit. Return
the unresolved cause, next discriminating evidence and the engineer decision it
needs. Reuse existing evidence, question and decision records. Link the decision
to the information available at that revision; later findings can justify
reconsideration without rewriting what was known earlier.

This method is informed by Buede and Miller, 4th edition, Chapters 6 and 13;
its concrete record and tool choices are CSE project conventions.
