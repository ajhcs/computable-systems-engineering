# Synthetic variable-influence tests (alpha)

`scripts/sysml_testgen.py` generates a small, inspectable test pair for each
referenced property of a supported `CSE-REQ/2.0` sampled requirement. A pair
has the same complete sampled trace except for **one property value at one
sample**. The selected requirement passes one trace and fails the other. This
demonstrates that the property can affect that requirement's verdict under the
declared finite sampled semantics. The generated values are hypothetical tests,
not measurements of a system.

```text
python3 scripts/sysml_testgen.py examples/sysml/ack.sysml \
  --manifest examples/sysml/ack-manifest.json \
  --output .tmp/ack-synthetic-tests.json
python3 scripts/sysml_testgen.py examples/sysml/ack.sysml --json
```

The JSON report identifies the model hash, clause ID and source, local-to-SysML
property bindings, clock, search limits, variable roles, changed sample, and
both traces and verdicts. It can be inspected or exported without supplying
behavior evidence. A `pass` in this report means that every **referenced
property of each supported sampled clause** has a witness pair. It is not a
system pass or required engineering review. A generated report cannot be used
as the `--evidence` input to `scripts/sysml.py --review`. Review needs separately
supplied evidence and an independent obligation manifest.

The underlying generator derives representative values from declared Boolean,
enum, and bounded integer domains, including comparison boundaries. The current
SysML adapter binds Booleans and annotated bounded quantities, not SysML enums.
The generator never changes
independent roles of a repeated property as if they were separate variables.
It tries timing-specific witness sketches and, for tiny spaces, a bounded
exhaustive short-trace search. Every candidate is replayed by the deterministic
monitor, and only an actual pass/fail pair is reported as a witness. There are
explicit row and evaluation caps. `not_found_within_search` means **no witness
was found under these strategies and limits**; it does not prove the variable
redundant or authorize deleting it. Long deadlines and correlated-event clauses
may remain uncovered or unsupported. Each pair is local to one requirement;
it need not satisfy other requirements or represent feasible system behavior.

The idea is inspired by NASA FRET's
[FLIP-based test generation](https://github.com/NASA-SW-VnV/fret/blob/master/fret-electron/docs/_media/exports/testgenManual.md),
which transforms temporal-logic requirements into formal test obligations for
atomic propositions and uses model checking. This alpha does **not** implement
that FLIP criterion, FRETish semantics, temporal-logic translation, or a model
checker. Its narrower criterion is a concrete single-property effect on a
selected finite-trace verdict. Future adapters may add formal FLIP obligations
and system-level feasibility without changing the authoritative SysML model.
