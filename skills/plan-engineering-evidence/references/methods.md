# Select a method for the claim

Use only the relevant section. Record why the selected method can answer the
question and what remains outside its reach. The same method may contribute to
verification or validation; the target and intended inference determine which.
Criteria come from the engineer's sources or decisions. Unknown criteria remain
unknown rather than becoming convenient pass/fail thresholds.

## Inspection

Use for an observable property of a retained artifact: required content,
configuration, markings, trace structure or accessible construction. Identify
the exact revision, selected features, inspection procedure and reviewer/tool.
State any inaccessible surfaces or reliance on declarations. A parser or document
inspection can establish its supported structural conditions; it cannot establish
operating behavior. Retain discrepancies with the affected IDs and artifact
locations, including ambiguous observations requiring engineering interpretation.

## Test

Use when controlled stimulation and observation can discriminate the selected
claim. Identify the item/configuration, input and expected response, observation
boundary, initial conditions, fixture, equipment, calibration basis where relevant,
and capture procedure. Specify relevant boundary, adverse and recovery cases
without claiming complete coverage from a few examples. Define reset/replay and
how capture failures will be detected. Retain actual run inputs, outputs,
implementation/observer revisions and unmet conditions.

For supported CSE clauses, `testgen` produces synthetic pass/fail pairs, not
implementation observations or complete coverage. `prototype-review` checks its
documented observation/manifest correspondence; use the existing record contract
rather than inventing a generic test adapter. For intended-use validation,
identify representative users, tasks and context, the suitability question and
who can judge the result. A successful local software test does not supply those
judgments or authorization to involve participants.

## Analysis or simulation

Use when an explicit model and its assumptions support a useful inference.
Identify the model-to-system correspondence, inputs, units, domain, assumptions,
solver/checker version and analysis limits. Select an existing CSE finite,
calculation, function/flow or observation check when it expresses the claim.
Retain witnesses/counterexamples and unsupported or incomplete outcomes.
Separate checking the analysis model from evidence that it represents intended
operating conditions. Identify sensitivity or comparison cases that could overturn
the conclusion. A calculation pass proves only its stated mathematical property;
a simulation result does not establish physical fidelity. General stochastic or
physical simulation requires a separately available, qualified tool and method.

## Demonstration

Use when a witnessed operating sequence provides appropriate evidence without
the measurement rigor needed for a quantitative claim. Name the item, setting,
sequence, expected visible behavior, witness/capture and stopping conditions.
Record deviations and what was actually seen. If the claim requires a tolerance,
timing bound or repeatability estimate, plan a suitable measurement/test instead.
For validation, explain why the demonstrated task and context are relevant and
retain stakeholder concerns or disagreement. A polished walkthrough alone is not
evidence of broad suitability, reliability or acceptance.

## Method basis

Original project synthesis informed by Buede and Miller, *The Engineering Design
of Systems: Models and Methods*, 4th edition, Chapters 1, 2, 6 and 13. These are
planning methods, not an implementation of a complete qualification system or a
claim of standards conformity. Private course material and annotations are not
distributed. Specialist FMEA/FMECA, fault-tree, root-cause and wearable V3 methods
remain outside this skill's implemented methods.
