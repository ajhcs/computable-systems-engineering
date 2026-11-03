# Measure definition record

Use one `measure-definitions-1.0` JSON record per stable measure identity. The
contract and runnable synthetic examples are in
[measurement definitions](../../../docs/measurement-definitions.md). Use that
contract when creating a record or interpreting a diagnostic; do not add fields
that the checker silently ignores. A record can be incomplete during drafting.

The helper works from another current directory when invoked by absolute path:

```sh
python3 /absolute/checkout/skills/define-engineering-measures/scripts/measures.py check /absolute/work/measure.json --format text
```

Retain the JSON result when a deterministic check is required. Compact text is
for reading. The helper reports the input byte hash, record digest, meaning digest,
checker version, limits and findings. These identify inputs and selected checks;
they do not authenticate an engineer decision. No protected runner is claimed.

Reuse the existing calculations AST: `ref`, exact `number` with `unit`, or a
bounded `op` tree. For a ratio, the two `div` arguments explicitly identify the
numerator and denominator. Declare what each input counts or measures, its scale
and unit. State denominator-zero handling in the definition's conditions and
exclusions; the definition checker does not evaluate a dataset or prove that
denominators stay nonzero. Preserve aggregation order, weighting and inclusion
rules in `aggregation.basis`; the helper compares those words exactly, without
executing them.

Use `null` for an unknown field and an `unknowns` entry for the unresolved
question. An empty conditions/exclusions list declares none; it does not mean
unknown. A source basis can identify an explicit synthetic or engineering
proposal. Source presence is checked, while source contents and authority are
not verified. Keep calibration status and uncertainty explicit; never invent
an uncertainty estimate or numerical target to make the record complete.
