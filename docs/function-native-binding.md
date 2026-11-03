# Bind a finite function check to native SysML

Use an explicit native binding when a function/flow check must retain its
connection to the authoritative SysML model. The adapter pins the source revision,
checks selected native identities and supported types, then runs the existing
finite verifier. It does not infer guards, effects or execution order from native
actions, arrows or prose.

```text
python3 skills/develop-system-concept/scripts/cse.py analyze functional-graph examples/function-native/handoff-functions.json --native-model examples/function-native/handoff.sysml --native-bindings examples/function-native/handoff-bindings.json
```

The same `analyze` arguments work through all three drafting launchers and
`scripts/analyze.py`. Both native options are required together; repeat
`--native-model` for an explicit model bundle. The direct Boolean example needs
no invented workflow metadata. The optional
[workflow example](../examples/function-native/handoff-workflow.sysml) and
[binding](../examples/function-native/handoff-workflow-bindings.json) additionally
exercise existing documentary IDs and selected relations. All are synthetic
proposals; none establishes real service behavior or acceptance.

## Explicit correspondence: function-native-1.0

The binding is a separate retained review input. It contains these exact fields:

| Field | Contract |
|---|---|
| `version` | `function-native-1.0`. |
| `native_model_sha256` | Existing CSE native source identity: file byte digest for one model; canonical sorted path/digest inventory for a bundle. |
| `function_flow_sha256` | `verifier.core.digest` of the complete authored function-flow record. This also pins the finite model, step bindings, function contracts and selected policies. |
| `functions` | Every function-flow function ID → native reference with `kind: function`. |
| `parties` | Every finite actor ID → reference with `kind: actor`, `system` or `element`. No resource/actor correspondence is inferred from labels. |
| `scenarios` | Every finite scenario ID → nonempty list of references with `kind: scenario`. Several documentary scenarios may explicitly correspond to one composed finite scenario. This is an authored relationship, not proven behavioral composition. |
| `steps` | Every finite scenario ID → every step ID → reference with `kind: step` or `function`. A function-valued reference must match the native function selected by the authored finite `step_bindings`. A separate native step identity does not prove invocation equivalence. |
| `data`, `properties` | Every corresponding finite ID → `{part: REFERENCE, attribute: QUALIFIED_ATTRIBUTE_NAME}`. The attribute must be directly declared on the selected part usage's type. |
| `relations` | Selected existing `cseWorkflow` relation ID → exact `{kind, from, to, label}`. These retain checked documentary context; they are not compiled into or compared as a complete finite topology. |

A reference is `{kind, native_name}` with optional `element`. Qualified names
must resolve exactly once in the current native inventory. The engineering role
is explicitly authored; the parsed action/part category is checked. If `element`
is supplied, that existing workflow ID must retain the same kind and qualified
native name. Direct native identification does not require a workflow document.
Selected documentary relations require its existing document and admit only
`allocated_to`, same-kind `decomposes`, `precedes` and `information_to`, with the
current endpoint kinds checked. They remain documentary relations, not native
connectors or execution evidence.

Mappings must exactly cover each listed finite group. Missing or extra IDs fail.
Distinct finite identities cannot silently alias the same native function/party,
or the same native attribute within a data/property group. Repeated calls remain
steps bound to the same function rather than invented new function identities.
Existing function-flow/core limits and policies still apply. Each binding map is
capped at 128 entries, each composed-scenario list at 128 references, text at
4096 characters, JSON inputs at 1 MB and the explicit native source set at
128 files/5 MB combined. No path in model text or the binding is opened implicitly.

## Supported type slice and limits

This first slice checks direct `ScalarValues::Boolean` attributes on a single,
explicitly typed part usage, mapped to finite `bool`. A finite property owned by
the environment requires native `in`; a controlled property requires `out`.
Native values, non-typing specialization, inheritance, variation and multiplicity
other than one are unsupported. Quantity units/scales, finite integer ranges,
enumerations, event payloads and port/connector execution are unsupported by this
adapter; their correspondence is not invented. An unsupported required mapping
blocks the linked check.

A native Boolean field's value does not establish whether a data item is
available in the finite scenario. Initial availability, guards, effects and
produced/consumed IDs remain explicitly authored finite semantics. The adapter
does not translate native requirement statements or traces. Native identity/type
agreement does not prove source truth, functional adequacy, native/finite behavior
equivalence, all-scheduler progress or engineer acceptance.

## Review and repair

Reports include both retained revision checks, native file identities, compact
mapping rows and counts, and exact expected/actual differences for changed
bindings. Native inventories are not dumped. Finite failures retain their rule,
IDs and counterexample paths, with related mapped native names for the return to
the concept decision. A native correspondence pass and a finite check failure
remain separate results. The selected source relationship can be reviewed without
mistaking a successful native parse for execution feasibility.

Native files are captured before parsing; parser receipts and final source bytes
are checked against that snapshot. Binding or analysis file drift through the
CLI discards its result. A stale native or function-flow pin blocks finite
execution until the engineer's correspondence is reconciled. Updating a digest
identifies a new candidate; it does not approve changed intent or authenticate a
decision. Keep the prior mapping and compare the reported identities/differences.
The helper supplies no protected acceptance channel.

Run `python3 -B tests/test_function_native.py` for real native/CLI positives and
controls for stale/deleted/renamed/wrong-kind targets, missing mappings, unsupported
type semantics, source drift, optional documentary relations and finite failures.
