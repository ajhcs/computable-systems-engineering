# Function and operational view quality

Use rigor appropriate to the question, model maturity, and requested deliverable.
Identify the task brief's requested views, levels, scope, timing, and completeness
before drafting; carry these into an explicit task profile when computable. No
universal breadth, depth, number of functions, or timing requirement is implied.
Do not substitute an academic rubric for a general engineering rule.

Functions describe actions or transformations. Prefer verb-object names such as
`CaptureSample`, with context, inputs, and outputs where useful. Parts/components
and actors name the entities that perform or participate in actions; a component
list is not a function decomposition. A dictionary of verbs or a naming regex
cannot determine whether a function has engineering meaning. The engineer must
assess that meaning, relevance, abstraction, coverage, and any naming exceptions.

A **function tree** shows decomposition: one explicit level-0/root function,
numbered decomposition levels, and parent-child traceability. It does not specify
execution order. An **activity diagram** shows actions and control/object flow,
including decisions, concurrency, and loops as appropriate. A **sequence diagram**
shows participants and meaningful exchanges in order; it does not establish a
function hierarchy. Do not claim that a tree or an ordered narrative is an
executable activity/interaction model. Permitted behavior loops are distinct from
invalid cycles in a function decomposition.

When a hierarchy is requested, record its root, each node's level, and its parent;
check requested levels and scope, including skipped levels, orphans, cycles, and
duplicate IDs. Establish breadth/depth/count constraints only from the actual task
or an engineer-directed profile. A shallow exploration may be sufficient. When
sequences are requested, establish the participants and ordered exchanges with
clear purpose and content. Include timing ranges when required by the brief or
rubric, or when useful and supported: numeric nonnegative min <= max, duration
units, and a timing reference/basis. Preserve unresolved timing instead of inventing
numbers. Review meaning and completeness with the engineer; machine structure
checks cannot settle either.

## Opt-in documentary checks in the authoritative SysML model

The existing three skill entry points support the same command:

```sh
python3 skills/develop-system-concept/scripts/cse.py check \
  examples/sysml/views/sample-handling.sysml --syntax-only \
  --view-profile examples/sysml/views/task-profile.json --json
```

Use the actual skill/runtime path from another directory. `--kind` can still be
added for the requested skill's ordinary draft-shape check. Existing models with
no `cseViews` annotation and no profile retain their earlier checks. Legacy
version-1 JSON helpers keep their existing semantics; do not retrofit their prose
with executable logic or claim they perform these new checks.

One package-owned `doc cseViews` block across the explicitly supplied model files
contains a `CSE-VIEWS/1.0` header followed by a JSON object with a `views` list.
Duplicate JSON keys, unknown fields in supported records, and malformed values
are errors. This is **documentary metadata**, not native SysML decomposition,
ownership, allocation, flow, or timing constraints. It stays within the model,
and binds uniquely by exact qualified name to extracted native elements. The
checker never manufactures missing elements or changes native model semantics.
Unsupported bindings require explicit modeling support rather than proxies.

The [synthetic example](../examples/sysml/views/sample-handling.sysml) and
[task profile](../examples/sysml/views/task-profile.json) demonstrate both kinds:

| Record | Fields and interpretation |
| --- | --- |
| Function tree | `id`, `kind: "function_tree"`, `nodes` list. Each node has `id`, `element` (native action definition or usage qualified name), `level` (nonnegative integer), and `parent` (node ID or null for root). One explicit level-0 root; each child is exactly one level below its parent. Native action bindings and IDs must be unique within this view. |
| Sequence | `id`, `kind: "sequence"`, `participants`, `exchanges`. Participants have `id` and `element` (native part **usage** qualified name). Participant bindings must be unique in the view. Exchanges are in list order, each with `id`, `from`, `to`, and nonempty `message`. Self exchanges are permitted. |
| Exchange timing | Optional `timing: {min, max, unit, basis}`. Both bounds are finite, nonnegative JSON numbers, min <= max. Units: singular/plural millisecond, second, minute, hour. `basis` states what elapsed interval is described. No conversion, timing execution, or cross-exchange arithmetic is performed. |

View IDs are unique across the block. Node IDs are unique within a tree.
Participant and exchange IDs share a unique namespace within each sequence.
The same native element may appear in different views; refer to it by qualified
name rather than assuming identical local IDs imply a cross-view trace.
The current parser extracts only part usages outside part definitions for
participant binding. Other native structures remain outside this bounded checker.
An empty tree or sequence fails. An unrecognized kind, including `activity`, is
`unsupported`; existing activity models without this annotation remain unaffected.

## Compatibility with maintained workflow metadata

The unmerged `codex/cse-foundation-20261012` line already provides native role
bindings, acyclic `decomposes` relations, hierarchy parent checks, documentary
step precedence, and a source/geometry-qualified function diagram adapter.
This increment adds task-specific levels/counts/coverage and participant message
timing checks; it does not replace those features or change their renderer.

If a supplied model also contains `cseWorkflow`, the new metadata supplements
that existing hierarchy. The checker reads its exact `CSE-WORKFLOW/1.0` header,
`workflow-1.0` version and identity/relation surface with strict JSON parsing.
Each tree node must use the unique existing **function ID** for its exact native
action binding. Its parent edges must match existing `decomposes` edges in the
selected scope, including any external parent of a nonroot selected node.
A scoped root may retain an outside parent as context. Omitted children outside
the selected scope are listed in `workflow_reconciliation.omitted_children`;
the task profile and engineer determine whether those omissions are appropriate.
Conflicting or ambiguous representations refuse the result. A documentary
`precedes`, information, or control relationship is never converted to hierarchy.

This bounded comparison covers selected identities and decomposition edges; it
is not a full workflow, source, decision, or source-diagram validation. Run the
maintained workflow checks separately when using that runtime. The existing
workflow sequence view represents step precedence; the new participant/exchange
annotation is explicitly a distinct documentary sequence contract. Do not infer
cross-view order or native behavior from either. No unpublished branch dependency
is imported by this increment.

## Task profile and justified tailoring

`--view-profile PATH.json` supplies version 1 and a `views` list. Each entry
requires `id` and `kind`, identifying a required view. The profile is explicit
input, never discovered or derived from the draft to claim independent review.
The report binds it by a content digest. No profile is a protected acceptance
channel; the engineer retains authority over scope and exceptions.

Optional profile fields:

| Field | Meaning |
| --- | --- |
| `required_levels` | Function tree only: unique nonnegative integer levels that must be represented. |
| `level_counts` | Function tree only: map of decimal level strings to `{min, max}` count bounds (either bound may be omitted). Counts include only nodes in this view. |
| `child_counts` | Function tree only: map of parent node IDs to count bounds for direct children. The parent must exist, even for min 0. |
| `required_ids` | Required node IDs for a tree, or participant/exchange IDs for a sequence. This checks declared coverage, not engineering completeness. |
| `require_timing` | Sequence only: Boolean, default false. When true, each exchange needs timing. |
| `exceptions` | List of `{rule, target, rationale}` for actual task-profile gaps. Each rationale must be nonempty. Rules: `required_level`, `level_count`, `child_count`, `required_id`, or sequence `timing`. Targets are level strings, node IDs, or exchange IDs as applicable. |

Counts have no default limits. To tailor a one-level study, request only its
needed levels; do not impose deeper decomposition. To retain a justified gap,
record the actual rationale in the task profile, for example:

```json
{"rule": "timing", "target": "E2", "rationale": "Exploratory archive interface; timing deferred pending measurement."}
```

The report exposes every used exception; unused/duplicate exceptions are errors.
A rationale string does not authenticate engineer approval. Exceptions cannot
waive malformed structure, cycles, orphans, duplicate IDs, wrong native bindings,
or invalid timing values. Revise consequential scope or exceptions as a proposal
for the engineer; do not silently relax them to obtain success.

## What the result means

The nested `view_checks` report has claim scope `documentary_view_structure`.
Malformed contract/input gives `error`, structurally invalid declarations give
`fail`, missing requested views/levels/coverage/timing give `unknown`, and
unimplemented kinds give `unsupported`. These findings propagate into the parent
check status; none can yield an overall successful requested check. A pass with
exceptions means the declared structure and explicitly tailored profile passed.

The report always identifies outstanding human assessments. Nonempty names,
messages, and rationale cannot prove action meaning, exchange usefulness,
adequate decomposition, task completeness, source truth, stakeholder acceptance,
realistic timing, or actual system behavior. Syntax, documentary structure,
controlled-clause compilation, synthetic tests, and supplied behavior evidence
remain separate claims. A local check is not protected execution.
