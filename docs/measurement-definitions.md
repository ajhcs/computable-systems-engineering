# Versioned engineering measure definitions

`scripts/measures.py` checks one `measure-definitions-1.0` record and compares two
revisions. It checks declared structure, supported formula syntax and unit
consistency. It does not evaluate observations, validate sources, interpret prose,
compute statistics or approve engineering acceptance. No dependency is added.
The skill launcher calls the same shared program from any current directory;
it requires this checkout and is not a portable standalone skill bundle.

```sh
python3 scripts/measures.py check examples/measurement-definitions/request-duration-v1.json
python3 scripts/measures.py compare examples/measurement-definitions/request-duration-v1.json examples/measurement-definitions/request-duration-v2.json --format text
```

The second command intentionally fails equivalence because the synthetic
aggregation changed from mean to median. Both records remain available.

## Record contract

All named fields are required; unknown fields are rejected. A record contains:

| Field | Representation |
|---|---|
| `version` | Exactly `measure-definitions-1.0`. Other versions are unsupported. |
| `id`, `revision`, `label` | Stable identifier, explicit revision text and display label. |
| `definition` | Exactly the meaning fields below. |
| `sources` | ID map of `{revision, locator, basis}`. Null source fields or an empty map remain unknown. A locator is documentary text; this command does not open it. |
| `unknowns` | List of `{field, question}`. Any unresolved item prevents success. |
| `links` | List of `{kind, id, revision}`; kind is `question`, `corrective_action` or `follow_up_measure`. These documentary links are not resolved by this checker. |

`definition` has exactly these fields. Any can be `null` to preserve an explicit
unknown; an unknown cannot yield a successful definition/equivalence check.

| Meaning field | Representation |
|---|---|
| `quantity` | Description of the measured quantity. |
| `scale` | `nominal`, `ordinal`, `interval` or `ratio`. |
| `inputs` | Map of formula variables to `{quantity, unit, scale}`. Each member can be null if unresolved. |
| `formula` | Existing calculations AST: `{ref: ID}`, `{number: EXACT_STRING, unit: UNIT_MAP}`, or `{op: OP, args: [...]}`; `pow` also needs `exponent`. See [arithmetic](engineering-analysis.md). No expression string or code is accepted. |
| `unit` | Map of explicit unit symbols to nonzero integer exponents, e.g. `{"second":1}`; `{}` means dimensionless. No unit conversion. |
| `population`, `boundary` | Explicit inclusion population and system/observation boundary. |
| `aggregation` | `{method, basis}`. Method is `identity`, `count`, `sum`, `mean`, `median`, `mode`, `proportion` or `rate`; basis describes order, weighting and inclusion. Unknown basis prevents success. Other methods are unsupported. |
| `exclusions` | Unique text list; empty explicitly means none declared. |
| `window` | Observation window and endpoint/inclusion convention. |
| `sampling` | Sampling method/resolution and conditions, including collection context. |
| `conditions` | Unique text list of applicability/context rules, including undefined-denominator handling where relevant. |
| `uncertainty` | Explicit uncertainty/calibration method or stated limitation. A qualitative limitation is allowed; no precision is inferred. |

A nominal output supports identity/mode aggregation; ordinal also supports median;
interval also supports mean; ratio supports the listed methods. An identity
formula retains its input scale. Arithmetic formulas support ratio inputs and
ratio output only. Counts of nominal categories must declare a ratio count
quantity rather than doing arithmetic on category codes. Affine/interval
arithmetic is unsupported. These are conservative selected checks, not a
measurement-theory proof. Method names and explanatory text are not executable
aggregation logic. This checker does not establish formula-domain validity or
that a denominator remains nonzero; use explicit conditions and a separate
numeric/data check.

## Comparison and limits

`check` returns `pass` only for complete supported definition structure/unit
checks. `compare` requires both checks to pass, the same ID, and exact equality
of every meaning field for successful equivalence. Formula trees, strings and
list ordering are compared exactly; object-key order is ignored. Algebraic or
synonym equivalence is not inferred. All changed meaning fields are listed when
both records are structurally readable, including changes in incomplete records.
Label, sources and links are listed separately as metadata changes. Changed
content with a reused revision fails. Changing only a revision is allowed.

The `definition_sha256` hashes only `definition`; `record_sha256` hashes the whole
record. CLI `inputs` hashes actual file bytes. Hashes identify content and do not
authenticate acceptance. Metadata-only changes may retain definition equality
while requiring provenance review. Unknown/unsupported/error checks never become
a successful comparison. Equal definitions leave observed-data comparability,
source truth, natural-language meaning and acceptance `not_evaluated`.

Inputs are regular, non-symlink UTF-8 JSON files up to 262,144 bytes. Duplicate
keys, nonfinite numbers and malformed JSON are errors. Records are bounded to
4,096 value nodes, depth 24, 2,048 characters per string/key, 64 entries per group
and 32 input variables. IDs use the existing ASCII engineering identifier rule
(letter first, at most 64 characters; letters, digits, underscore or hyphen).
At most 64 findings are retained; hitting the diagnostic cap adds an incomplete
finding and cannot pass. Text displays at most 12 top-level findings; JSON retains
the bounded details and, for comparisons, both definition check reports.

Formula parsing reuses `verifier.calculations`: at most 128 nodes per formula,
depth 16, exact numeric strings of at most 80 characters, exponent magnitude at
most 8, and at most 16 unit symbols with exponents from -16 to 16 excluding zero.
No formula execution, symbolic worker, new numerical library or model-provided
code is used. The existing arithmetic cap failures retain their explicit
unsupported/error status. Exit code 0 means the scoped check passed; 1 means
fail/unknown/unsupported; 2 means malformed input or another error.
