# Carry defined meaning into generated work

Use the project's existing meanings when drafting or reviewing engineering
explanations, designs and implementation. Start with the current question and
the relevant model slice. A focused question does not require a complete CONOPS,
a new vocabulary or an executable representation of every sentence.

## Prepare the context

Inspect the relevant existing definitions and native model before drafting.
Retain concept IDs, namespaces, revisions, definitions, engineering kinds and
native bindings. Preserve explicit roles when one native entity has several
roles. Matching labels do not establish identity or synonymy.

Carry the relationships and conditions that govern the question into the work.
Keep direction, endpoints, applicability, units, exclusions and evidence status
where the supplied records express them. A nearby element is not necessarily a
defining dependency. Expand the view when a condition or mapping is missing.

Keep unrepresented meaning explicit. Foundation terms do not have generic
applicability or evidence fields. Conditions and source basis may instead occur
in native documents or linked workflow records. Preserve that text and its
origin; do not infer an executable predicate from prose. Missing information
remains a question or proposal. Useful qualitative work can continue with those
limits.

Reuse the admitted kinds and relationship semantics. The distinctions in
[concept roles and intent](../skills/check-engineering-language/references/concept-roles-and-intent.md)
do not add foundation kinds for goal, constraint, obligation or performer.
An allocation need not imply exclusive ownership. An available checker executor
does not establish an engineered system's operational capability.

## Retrieve an assembled view

The existing `view` route can assemble definitions and context from explicitly
supplied files. Resolve the installed runtime or checkout path before running
from another project. Model and profile paths remain project inputs.

```sh
python3 scripts/sysml_view.py examples/terminology/shared-pump.sysml --profile examples/terminology/shared-pump.english.json --element R_PUMP
```

The same route is available through each concept, CONOPS and scenario launcher:

```sh
python3 skills/develop-system-concept/scripts/cse.py view MODEL.sysml --context --profile MODEL.english.json --element ELEMENT_ID
```

Select one existing short ID with `--id`, a profile/workflow element ID with
`--element`, or an exact qualified native identity with `--native-name`.
`--context` selects assembly explicitly; profile and extended selector options
also select assembly. The legacy `--id` invocation alone keeps its parsed-view
behavior. Supply every model file needed by the selected native context.

Use `foundation:ID` or `workflow:ID` with `--element` when the catalogs reuse an
ID for different native identities. Equal native identities in explicitly
different roles remain separate bindings. The selector does not infer roles
from labels.

`--workflow` selects an existing documentary workflow, defaulting to `concept`.
Its other admitted values are `scenarios`, `requirements`, `architecture` and
`trade-study`. Supply source evidence explicitly with repeatable `--source
ID=PATH` arguments. No path or executable is opened from a model's text.

Use `--limit` to bound the returned elements. The default is 32 and the maximum
is 512. Inspect omissions and unresolved mappings before relying on the slice.
A successful lookup is not a claim that the context includes every dependency.
Increasing a limit does not resolve missing model semantics.

Expansion follows explicit English-use bindings, allocation scope members,
selected trade alternatives and criteria, and supported linked native references.
A recorded zero allocation bound remains an exclusion. Native endpoint paths
retain undirected adjacency; they do not prove a configuration or executed flow.
Package clock documents remain visible as authored timing context.

Parsing uses private snapshots of the captured model bytes. Original input
changes invalidate the result. The eight-megabyte output cap includes JSON
indentation, Unicode escaping and the final newline used by the CLI.

The `assembled-context-1.0` response separates `retrieval_status`,
`profile_check` and `workflow_check`. Its `coverage` identifies returned and
omitted elements, unresolved mappings and inclusion reasons. `coverage.complete`
describes known supported dependencies of the selected records, not general
semantic completeness. Inspect these fields alongside overall `status`.
`semantic_review` remains `not_run`; `required_review` and `acceptance` remain
`not_evaluated`.

Unresolved joins appear in `coverage.unresolved`. Recorded project questions
remain in `workflow_context.questions`; a successful retrieval does not resolve
them. An unrelated workflow focus leaves applicability unresolved, and its
conditions are not attached to the selected concept.

The assembled view reuses the foundation and English contracts and the native
`cseWorkflow` record. It presents existing definitions, bindings, typed links,
allocations and applicable documentary context together. The source and profile
revisions identify the supplied bytes. They do not authenticate an engineering
decision or prove source truth.

Keep native declarations, documentary relationships, proposed or recorded
decisions and evidence results distinguishable. An evidence plan remains
`not_run`. A reported assessment remains a report. Retrieval and the selected
record checks do not execute a scenario or review arbitrary generated meaning.
Stale inputs, ambiguous selected mappings and incomplete required checks cannot
become a successful complete review.

The view is a derived presentation, not an independently editable model or a
replacement verification input. Pass the complete selected model and retained
obligation scope to the applicable checker. Retrieval limits must not reduce
that scope. Use the [concept-review contract](concept-review.md) for retained
documentary expectations and [behavior correspondence](behavior-review.md) for
the existing executable check boundaries.

## Review the actual output

After drafting, read the delivered text, code or view against the same source
meaning. Check its claims and behavior, not only the vocabulary or an earlier
draft. Preserve who acts, what changes, under which conditions and what evidence
supports the claim.

For a material discrepancy, retain the actual sentence or code location, the
relevant concept and relationship IDs, the conflicting meaning and its source.
Record the method used and the result or unresolved assessment. Keep this
evidence proportionate to the question; a small correction need not create
another report schema.

| Property | Existing method | Coverage |
|---|---|---|
| Selected terminology | Foundation/English checks. | Declared identities, forms and bindings; unrestricted meaning remains unevaluated. |
| Controlled-clause revision | Language-repair comparison. | Supported actor, condition, comparison, timing and unit semantics. |
| Modeled/observed behavior | Finite, sampled/event or prototype checks. | Authored semantics, retained obligations and supplied evidence. |
| Unrestricted prose/code | Source-linked review; relevant implementation tests. | Interpretation remains an assessment. Code reading alone does not establish runtime behavior. |

Run the selected deterministic checks and repair ordinary draft defects within
accepted meaning. Preserve their actual statuses and claim limits. A lexical
pass cannot settle a disputed completion rule. Unsupported semantics, missing
evidence and unsuccessful required checks remain unresolved. Do not replace a
computed finding with an LLM's favorable assessment.

Changes to accepted intent, modality, applicability, units or obligations remain
proposals with their reason. A mismatch between code and an accepted obligation
does not authorize changing the obligation to match the code.

## Synthetic handoff example

Suppose a project defines handoff completion as receiving an acknowledgement
from the receiving clinic. Sending the referral alone does not establish that
completion event. Preserve the distinction in the explanation and implementation.

An implementation test can observe sending with no acknowledgement and inspect
the completion state. A separate case can supply the defined acknowledgement.
Identity matching needs the project's explicit handoff and receiver contract.
Waiting without an acknowledgement does not itself supply a deadline or prove
failure. A description of that event does not create executable semantics.

## Evaluate the workflow

Use the [synthetic adversarial corpus](../examples/meaning-context/README.md) to
exercise identities, relationships, conditions, evidence stages and the handoff
distinction. Keep mechanically checked cases separate from interpretation cases.
Expected prose assessments do not become program verdicts.

For a generation study, compare the current workflow, shared guidance alone,
assembled context, and context with output review on the same tasks. Retain the
actual outputs, model revisions, checker obligations and unresolved findings.
Use repeated trials and independent assessment of interpretation cases. Measure
meaning errors and unsupported claims before claiming reliability gains.
Token counts and latency describe the trial; they do not establish correctness.
