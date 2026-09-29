# Alpha review before the engineer's material trial

**Date:** 2026-09-29. **Release:** 0.2.0-alpha.1.
**Disposition:** ready for a repository-scoped drafting trial with the limits
below. This is not acceptance of any real system or its requirements.

## Alignment with the intended workflow

The engineer can request the system-concept, CONOPS, or operational-scenarios
skills by their natural names. A combined request shares a SysML v2 model or
explicitly imported bundle, runs each requested draft-shape check, and returns
readable engineering views. The assistant handles model files and commands.
Raw material is read in place; private models and reports stay under ignored
`work/` paths on `/workspace`. No user-wide skill installation is required.

SysML supplies the model structure and reference validation. Explicit CSE
controlled clauses supply the bounded computable meaning. Ordinary narrative
retains its engineering value without receiving an executable verdict.
Consequential interpretations, thresholds, and accepted obligations remain
engineer decisions.

## Gaps repaired for this trial

- Registered all three skills in the repository's `.agents/skills/` directory
  and added launchers that locate their shared runtime from another working
  directory.
- Made combined concept and scenario work use shared definitions and both
  relevant checks, without requiring a complete CONOPS.
- Made plain reports distinguish model compilation from supplied behavior
  evaluation and show actual parser diagnostics and counterexamples.
- Blocked computational success when native constraints, relevant inherited
  properties, specialized declarations, or native values are not computed.
  Valid SysML syntax remains separately checkable.
- Required the pinned SysML parser in CI so integration tests cannot disappear
  behind a missing dependency. CI selects Java 21 explicitly, and the installer
  checks for Java and javac 21+ before downloading or compiling the parser.

## Evidence

`python3 scripts/check.py --require-sysml` passed all **174 tests** across 13
suites on Linux. These include the legacy skill helpers, finite JSON verifier,
controlled grammar/types/units, independent short-trace oracle comparisons,
missing scope/evidence and analysis limits, correlated deadlines, synthetic
variable influence, SysML binding and unsupported-feature gates, public-source
candidate slices, views/diffs, shared skill launchers, and an unsupported-Java
prerequisite diagnostic. The launcher/prerequisite suite contains five tests.
All three skills also passed the skill metadata validator.

A local Codex `skills/list` query reported all three engineering skills as
enabled with `scope: repo`, and no discovery errors. The shared synthetic
concept/scenario example passed both shape checks and exported witness pairs
for its two referenced variables. Public-source examples are attributed,
proposed interpretations with synthetic observations, not source-authorized
requirements or measured behavior.

The tests verify deterministic tools and their invocation paths. They do not
measure the quality of a fresh LLM drafting session on the engineer's material.
That is the purpose of the next trial. Windows has not been exercised.

## Limits that affect interpretation

General SysML behavior execution, arbitrary native constraint computation,
inherited-property computation, complete FRET semantics, and formal FLIP
coverage remain unimplemented. Synthetic variable-influence pairs are local
clause witnesses; they are not evidence that a deployed system behaves
correctly. The separate finite JSON engine does not silently execute SysML or
prose scenarios. Jev and protected acceptance are also future work. Hashes and
ignored directories do not enforce an independent trusted boundary.

Use [the end-user guide](end-user-test.md) for the trial and
[the current computational profile](sysml-v2-profile.md) for exact semantics.
