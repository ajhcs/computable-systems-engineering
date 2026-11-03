# Failure analysis record: failure-analysis-1.0

This record is a separate authored analysis view. It does not extract native SysML
semantics, establish source truth or replace the engineer's authoritative model.
Retain the relevant source revision and interpretation in `revision` and `basis`.
Keep actual project records in the project's private workspace. The repository's
[examples](../../../examples/failure-analysis/) are synthetic.

The top-level fields are exactly `version`, `id`, `revision`, `basis`, `events`,
`gates`, `top_event`, `probability`, and `fmea`. `version` is
`failure-analysis-1.0`; `revision` is nonempty authored text. `basis` is nonempty
source/assumption text or `null` for unknown. Text is bounded to 2048 characters.
IDs match `[A-Za-z][A-Za-z0-9_-]{0,63}`. Event, gate and FMEA row IDs are unique
across the three maps. IDs retain authored meanings; no terminology is inferred.

`events` is a nonempty map of IDs to exactly:

```json
{"description":"Supply unavailable", "basis":"Explicit synthetic assumption", "probability":"1/100"}
```

`description` is nonempty text. `basis` is nonempty text or `null`. `probability`
is `null` or an exact nonnegative integer, decimal or rational **string** of at
most 80 characters in [0,1]. Binary floating point is refused. Probabilities are
for the same explicitly authored mission/condition; the checker does not verify
their empirical basis. Unknown probability data is permitted for a qualitative
analysis. Missing event basis makes a referenced event's check unknown.

`gates` is a map of IDs to exactly `{operator,inputs}`. `operator` is `and` or
`or`; `inputs` is a list of 1..32 event or gate IDs. A gate may have one input.
Repeated references are allowed: A AND A and A OR A both equal A. Named gates may
have multiple parents. The full declared graph, including disconnected content,
must have valid references, supported operators and no cycles. `top_event` names
one declared basic event or gate. Declared unused nodes are reported separately.
NOT, voting, dynamic sequencing, repairs, rates, distributions, uncertainty and
arbitrary expressions are unsupported. No code in a model is executed.

The checker exhausts Boolean assignments over unique reachable basic-event IDs.
An event has one Boolean value in each assignment everywhere it occurs. A minimal
cut is a set of failed events sufficient to make the top event true when all
other basic events are false, with no sufficient proper subset. The validated
AND/OR grammar is monotone: testing each immediate subset establishes minimality.
Cuts are sorted by size and then ID sequence; no probability or severity ranking
is implied. Shared causes must be explicitly authored as shared event IDs or
logic. The checker neither infers common causes nor assumes redundant components
are statistically independent.

`probability` is `null` when no quantitative check is requested, or exactly:

```json
{"assumption":"mutually_independent", "basis":"Explicit engineering assumption", "mission":"One specified mission under stated conditions"}
```

`basis` and `mission` may be `null` for unknown, which prevents quantitative
success. Every referenced event needs an exact probability and basis. The helper
sums the probabilities of disjoint complete assignments using exact fractions.
This handles repeated events and overlapping cuts without treating cuts as
independent. The result is conditional on **mutual** independence of the basic
events and the declared mission; pairwise independence is insufficient and
unsupported. A shared cause represented as one basic event remains one variable.
If remaining basic events are dependent, this probability model is inapplicable.
The helper does not decide applicability or derive probability from an FMEA.

`fmea` is a map of row IDs to exactly:

```json
{"component":"Pump", "failure_mode":"Does not start", "event":"PumpUnavailable",
 "local_effect":"No pump flow", "system_effect":"One supply path is unavailable",
 "detection":"Explicit flow observation", "basis":"Synthetic analysis"}
```

`component` is an authored ID; existence in a source model is not checked.
`event` must reference a basic event. The other fields are nonempty text or
`null` for unknown. A nonempty, complete set of rows is needed for FMEA success.
Duplicate `(component,failure_mode)` pairs fail this format's consistency check:
retain one row and describe its effects there. Unknown failure-mode labels do
not constitute a confirmed duplicate. Effects, detection effectiveness, source
truth, completeness of the failure inventory and risk priority are not checked.
Severity, occurrence and detection scores are absent from this format.

## Scope, bounds and reports

`analyze(record, required_checks=None)` checks the fault tree, plus probability
when its assumption object is supplied, plus FMEA when rows are supplied.
Pass a nonempty distinct list selected from `fault_tree`, `probability`, `fmea`
to retain independently selected expected checks. Supplied analyses still run;
the selection cannot hide their failure. Required probability without assumptions
and required FMEA without rows fail. An empty selection is an error. Required
scope comes from the caller and is not authenticated by this local helper.

The hard bounds are 128 events, 128 gates, gate depth 64, 32 inputs per gate,
12 reachable basic events, 4096 complete assignments, 256 minimal cut sets,
2048 output literals, 128 FMEA rows and 4096 bits per exact rational result.
The enumeration and antichain/output limits return `unknown`, with no partial
cut list presented as complete. Declaration/depth/operator limits are
`unsupported`; malformed input is `error`, and broken references/cycles or
missing required content are `fail`. Missing basis or probability data is
`unknown`. Every non-pass analysis prevents overall success. Unknown or errored
checks do not count as completed checks, even when some Boolean evidence exists.
This is a bounded local helper, without a protected execution boundary.

Reports identify record ID/revision, canonical artifact digest, caller scope
digest, expected/completed checks, limits, stable findings, cut completeness,
unique events, unused nodes, assignment count and exact conditional probability.
Hashes identify inputs and scope; they authenticate no engineer decision.
Applicability and stakeholder acceptance remain `not_evaluated`.

The CLI rejects duplicate JSON keys, nonfinite numbers, changed input files and
inputs over 1 MB. Exit 0 is a passing selected analysis, 1 is a non-pass report,
and 2 is a parsing/I/O/operation error. It emits deterministic JSON, adds raw
input SHA-256 and absolute path, and works from another working directory.
