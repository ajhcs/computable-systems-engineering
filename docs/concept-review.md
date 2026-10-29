# Project-tailored concept coverage

The system-concept skill now includes an explicit scenario/function/support review
in its normal recorded drafting loop. Each project selects its relevant needs,
functions, means, interfaces and evaluation preparations. The separate scope
preserves what the review must retain even if an entire item is cleanly removed
from the candidate. Small questions and incomplete drafts remain useful.

The method connects lifecycle enabling systems, operational/functional analysis,
allocated architecture and early qualification planning described in Buede and
Miller, *The Engineering Design of Systems: Models and Methods*, fourth edition,
notably pp. 44, 134, 162–163, 193, 213 and 243. This is a bounded CSE adaptation,
not a claim to implement the complete book or a universal allocation rule.
No private annotations or course documents are included in the shared examples.

## Runtime and claims

Use the complete repository/plugin through `skills/develop-system-concept/scripts/cse.py`.
The three drafting launchers share this command; independent scenario or CONOPS
work does not automatically require a concept scope. The concept skill handles
files and commands for the engineer.

`verifier/workflow.py` and `verifier/foundation.py` reuse existing candidate source
from `c27f52a121a00e97900880e95011ff9c9479e634`; the workflow adapter now also extracts
the explicitly selected human-task/ownership documents from its captured snapshot. Their native adapter is the existing
pinned SysML parser. `verifier/concept_review.py` adds strict project-scope input,
scope/source freshness and expected-item comparison, then calls those adapters.
The separately documented `question` route handles conditional capacity and mean-flow inquiry; broader historical workflow commands are not registered by this integration. No new dependency, simulator or concept engine
is added.

Coverage means the selected documentary expectations are present, natively bound
and structurally admitted. It does not establish the sufficiency of the scope,
source truth, native connectors, executable behavior, feasibility, staffing,
observed validation or acceptance. Hashes identify bytes, not decisions. The
scope can be maintained locally; no protected runner is a universal prerequisite.

## Project scope versions

Version 1.0 remains supported unchanged. Version 1.1 adds selected
[human-task expectations](human-task-review.md). Version 1.2 adds tailored
[ownership/interface expectations](ownership-review.md); new scope initialization uses
1.2. Rows, roles and fact fields are project-selected, with no universal checklist.
Version 1.3 is an explicit opt-in for bounded documentary view composition,
described below. Existing scopes and initializers are not silently upgraded.

Supply one separate UTF-8 JSON scope, at most 1 MB. Unknown fields/versions,
duplicate JSON keys, nonfinite values, symlinks and malformed bounds are refused.
Maps use distinct ASCII IDs, up to 64 characters. Sources/topics are capped at
64 entries and expectations at 512. A new scope is deliberately incomplete.

| Field | Contract |
|---|---|
| `version` | `concept-review-1.0`, `concept-review-1.1`, `concept-review-1.2` or explicit `concept-review-1.3` |
| `project` | `{id,name,question,boundary,basis}`; basis names a scope source or is null while drafting. |
| `sources` | Source ID → expected SHA-256 of the explicitly supplied source. No paths are opened from model or scope text. |
| `topics` | Project topic ID → `{applicability,rationale}`. Applicability is included/excluded/unresolved. Topics are project-defined; there is no required catalog. Explain exclusions. |
| `expectations` | Expectation ID → one of the objects below. Each names its topic. An excluded topic cannot retain active expectations and silently disable them. |
| `allocation_bounds` | `{functions,resources}`: each is an ID → `{min,max}` map. Both empty means no count check selected. Otherwise both identify the exact selected scope with integer bounds `0 <= min <= max <= 512`. No default minima. |

Expectation objects:

```json
{"topic":"support","kind":"element","element":"R_PROVIDER","element_kind":"element","native_name":"Project::provider"}
{"topic":"support","kind":"relation","relation_kind":"allocated_to","from":"F_MAINTAIN","to":"R_PROVIDER"}
{"topic":"evaluation","kind":"evidence_plan","evidence":"E_READY","target":"F_READY","purpose":"qualification"}
{"topic":"operation","kind":"walk","scenario":"S_NORMAL","functions":["F_CHECK","F_ISSUE"]}
```

An element expectation retains its kind and parsed qualified identity; readable
labels may change. Relations are documentary and retain typed endpoints. An
`interfaces_with` association is nondirectional, so swapped endpoint order alone
is not an omission. An evidence-plan expectation retains its target, purpose and
plan/not_run stage. Replacing it with an assessment requires an explicit review
stage/scope change; a self-declared supported assessment is not computed evidence.
A walk checks the named scenario/functions exist and presents the expected walk;
it does not verify narrative order, guards, deadlines or real-world correspondence.

Missing scope context, basis, selected expectations, topic rationale or unresolved
applicability yields unknown. A structurally admitted draft with unresolved questions
still runs its selected documentary checks; their findings do not remove the overall
unknown or failing workflow result. Invalid native syntax and unstable inputs block
those checks and retain diagnostic details. Each included topic needs selected expectations.
There is no global required topic list or one-to-one allocation policy. A function
may have multiple complementary means and a means may support several functions.
Only assignments within the explicitly selected count scope are counted; named
role/dependency links should capture distinctions that counts cannot express.

## Authoritative SysML documentary record

The legacy SysML record contains exactly one `cseWorkflow` documentation block owned
by a parsed concern, starting with `CSE-WORKFLOW/1.0` and JSON `version: workflow-1.0`.
The explicit composed version below retains one block with its matching 1.1 header.
The shared model remains authoritative. Authoring JSON and derived allocation
profiles are temporary inputs/views, not competing saved concept authorities.

The record fields are `version`, `question`, `sources`, `elements`, `relations`,
`workflows`, `decisions`, `questions`, `trade_studies`, `evidence`. Empty maps are
allowed drafts. Use the [synthetic lending model](../examples/concept-review/lending/concept.sysml)
or [software-only model](../examples/concept-review/software/concept.sysml) for exact syntax.

- Question: `{text,basis}`. Sources: ID → `{sha256,excerpt,kind}`; kind is provided,
  assumption, proposal or reported_observation. An excerpt must occur exactly once
  in matching supplied bytes. This checks provenance, not interpretation or truth.
- Elements: ID → `{kind,native_name,label,description,basis,status}`. Status is
  proposed/accepted/deferred/superseded; a recorded label authenticates no assent.
  Need/goal/concept/criterion bind parsed concerns; actor/system/element bind parts;
  element_definition binds part definitions; function/scenario/step bind actions;
  requirement binds parsed requirements. Keep role classifications explicit.
- Relations: ID → `{kind,from,to,basis,label}`. Supported documentary kinds are
  addresses, derives_from, allocated_to, scenario_of, precedes, participates_in,
  decomposes, interfaces_with, information_to and controls. Endpoint kinds are
  checked by the reused workflow adapter; unsupported relations are not converted
  to a generic graph edge. Information/control labels name their payload/meaning.
- `workflows.concept`: `{focus,summary,conditions,outcome,next_decision}`. Focus is
  a list of relevant element IDs. This is a drafting view, not an executable job.
- Evidence: ID → `{target,purpose,mode,method,environment,basis,result,limitations}`.
  Purpose is verification/validation/qualification/analysis; mode plan/assessment;
  result not_run/supported/contradicted/unknown. Plans require not_run. Missing
  methods/environments and unsupported assessments remain non-successful.
- Decisions: ID → `{text,status,by,basis,affects}`. Questions: ID →
  `{text,affects,blocking}`. Preserve uncertainties rather than inventing decisions.
  Trade-study data are not required for a concept coverage slice.

The workflow and concept-review adapters accept a single model path or an explicit
list/tuple of 1–128 model paths, with at most 5 MB combined UTF-8 bytes. Supply all
needed imported definitions; imports do not discover or open files automatically.
Exactly one `cseWorkflow` block on one parsed concern is required across the set.
The legacy record retains its 64-element/512-relation bounds; the opt-in 1.1
workflow/view contract below extends those counts.

The adapter captures every explicitly supplied file before parsing, checks the
private snapshot once, and uses that same inventory for coverage, allocation and
selected human-task/ownership checks. Source diagnostics map back to their original
file and line. Reports retain `model_files` with canonical path labels and byte
digests. For one file, `model_sha256` remains its byte digest. For a bundle it is
the SHA-256 of the canonical, sorted JSON file/digest inventory, matching the native
parser's model identity. Changing a dependency or its canonical path changes that
identity; input mutation during a check is an error. A successful report covers
only this explicit model set and selected documentary scope.

Workflow scratch files use `CSE_SYSML_CACHE/workflow-scratch` outside the installed
package. Set `CSE_SYSML_CACHE` to a private writable directory on the workspace for
installed plugins, consistently with parser setup. Temporary directories are
private and cleaned on completion or failure. The repository default remains its
workspace parser cache. No system temporary-directory fallback is used.

For example, pass `room.sysml equipment.sysml review.sysml` before `--scope` to
`concept-review check` or `next-evidence`. Single-file commands remain supported.
All relevant evidence sources are supplied explicitly as before.

## Drafting loop and commands

1. Reuse or tailor the scope from project intent and sources. Trace selected
   situations through functions, means, support and interfaces. Plan evaluation
   data, responsible people and equipment while considering the concept.
2. Preserve the scope version and retain its fingerprint with the review request.
   Draft against it. Never derive obligations from the reduced candidate just to
   get a pass. The engineer directs consequential meaning and applicability.
3. Run usual native concept/scenario shape checks and then the coverage command.
   Explain unknowns and ordinary repair targets. A draft may continue without a pass.
4. For scope changes, keep before/after files and inspect `scope-diff`; deletions,
   exclusions, bounds and basis changes remain visible. Preserve accepted intent.
5. Report actual check scopes separately from feasibility and evaluation evidence.

```text
python3 skills/develop-system-concept/scripts/cse.py concept-review init-scope work/project/scope.json --project PROJECT_ID --name "Project name"
python3 skills/develop-system-concept/scripts/cse.py concept-review fingerprint work/project/scope.json
python3 skills/develop-system-concept/scripts/cse.py concept-review check work/project/concept.sysml --scope work/project/scope.json --scope-sha256 RETAINED_DIGEST --source SOURCE_ID=work/project/brief.md
python3 skills/develop-system-concept/scripts/cse.py concept-review scope-diff work/project/scope-before.json work/project/scope-proposed.json
python3 skills/develop-system-concept/scripts/cse.py concept-review prepare work/project/authoring.json work/project/new.sysml --package ReviewMetadata --base work/project/existing.sysml
```

`init-scope` and `prepare` refuse overwrite. `fingerprint` returns byte identity
only, including for an incomplete scope; it is not a coverage check or approval.
Retain the digest before changing the candidate; automatically replacing it on
an unexpected mismatch would defeat the scope-drift check. No check can determine
that the supplied digest came from an authorized engineer.

`check` emits readable text or `--json`; only coverage pass exits 0. Unknown,
unsupported, failed, errored and unrun selected obligations are non-successful.
Malformed CLI inputs exit 2. A successful draft creation exits 0 while explicitly
reporting incomplete scope as unknown; it does not claim coverage. Reports include
project question/boundary, model/scope/source hashes, upstream findings, selected
walks, optional allocation-count results and explicit unperformed claim boundaries.

## Examples and regression evidence

[Lending](../examples/concept-review/lending/) selects maintenance, procedures,
facilities and evaluation support; [software](../examples/concept-review/software/)
selects export purpose/allocation/evaluation and explains why new physical support
is outside its boundary. The software example uses multiple arbitrarily named
sources and selects no assignment-count test. Neither supplies observed results.

`tests/test_concept_review.py` checks both actual native-backed projects, seven
clean omissions, unknown/unsupported/stale inputs, scope drift, changed inputs,
and launchers from another working directory. The reused foundation/workflow
tests remain separate from these integration cases. `python3 scripts/check.py
--require-sysml` runs the registered regressions. Passing tests establishes the
declared software behavior, not operational or independent engineering acceptance.

## Bounded documentary composition

Opt in with `CSE-WORKFLOW/1.1`, JSON `version: workflow-1.1`, and one additional
`views` field in the same authoritative model record:

```json
"views": {
  "OPERATIONS": {"label":"Operations", "elements":["F_ISSUE","R_STORE"]},
  "DATA": {"label":"Record governance", "elements":["F_ACCESS","R_STORE"]}
}
```

The composed record admits at most 256 elements, 2048 relations and 16 views.
Each nonempty view names at most 64 existing element IDs; every element must be
in at least one view. Overlapping views share the same element identity. Other
record groups, the 1 MB record and 5 MB model caps, and selected allocation-count
bounds are unchanged. These are CSE implementation limits, not ISO requirements.
View membership is documentary grouping, not native ownership, abstraction
semantics or executable composition.

Use explicit scope `concept-review-1.3` and retain an additional `views` map:
view ID → list of expected element IDs. Labels may change. View IDs and membership
must match the independently retained scope. Existing expectations still retain
expected elements, cross-view relations, tasks, ownership and evaluation plans.
All native bindings, references and decomposition cycles are checked globally;
a view cannot hide an invalid endpoint or cycle. Reports list relations crossing
each view boundary. Completeness of the chosen decomposition remains an engineer
judgment. A legacy scope cannot silently admit a composed record as a successful
review. Imported-only bundles and general native behavior remain unsupported.

Use the existing `prepare`, `fingerprint`, `check` and `scope-diff` operations.
The [synthetic composed example](../examples/concept-review/composed/concept.sysml)
contains 70 bound elements and a separately retained view scope. It supplies no
observed performance or actual policy evidence.

## Turn missing evidence into the next investigation

The existing route also offers a derived action view:

```text
python3 skills/develop-system-concept/scripts/cse.py concept-review next-evidence MODEL.sysml --scope SCOPE.json --scope-sha256 RETAINED_DIGEST --source ID=SOURCE_PATH
```

It runs the same fresh scoped review, retains its status/configuration and emits
unresolved findings, affected IDs and linked existing plans. Tool/input repairs
precede evidence questions; this is not an engineering risk ranking. The engineer
selects the next investigation and nominates responsible parties. Known role
allocations do not establish an actual delegated decision-maker. All plans remain
`not_run`; no evidence is acquired, accepted or relabeled by this operation.
A documentary pass can still have unexecuted plans and real-world evidence gaps.
