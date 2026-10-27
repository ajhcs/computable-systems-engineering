# Project-tailored concept review

Use this as the normal review loop for recorded SysML concept work. For a small
question, keep the scope small. Discussion alone needs no files. Reuse a project's
model and scope; do not re-elicit settled information or construct a full CONOPS
when only a concept slice is needed. The assistant handles commands and files.

## Tailor before checking

Start from the question, sources, boundary and selected normal, exception or
lifecycle situations. Walk each relevant situation through its functions. For
each transformation ask what means perform it, which need it contributes to,
what it receives/produces, and which support or interface dependencies matter.
Consider technology, people/organizations, infrastructure, procedures and early
evaluation preparations where relevant. Explain exclusions and keep uncertain
applicability visible. Do not turn this prompt list into universal requirements,
fixed counts, staffing numbers or compulsory lifecycle phases.

Record those expected elements, links, walks and evaluation plans in a separate
project scope, using the [contract and examples](../../../docs/concept-review.md).
Base it on the request and source meaning, not whatever remains in the current
candidate. The scope is a proposed or reviewed engineering input; a populated
field or hash does not authenticate engineer acceptance. Keep private notes and
project models under ignored `work/` or another approved private workspace.

## Draft and run the checks

When tasks or human/automation allocation are part of this question, use the
[human-task register and scope extension](../../../docs/human-task-review.md).
Scope version 1.1 adds selected task facts; version 1.0 remains supported.

Keep one authoritative SysML model. Use its `CSE-WORKFLOW/1.0` documentation for
the existing documentary workflow representation; its relations supplement
native definitions and do not assert native execution or connectors. The helper's
`prepare` command can preserve a native base in a new file without overwriting it.
Run the usual concept shape check and, for linked scenario work, its own shape
check. Then run the project coverage review:

```text
python3 <skill-dir>/scripts/cse.py concept-review init-scope SCOPE.json --project PROJECT_ID --name "Project name"
python3 <skill-dir>/scripts/cse.py concept-review fingerprint SCOPE.json
python3 <skill-dir>/scripts/cse.py concept-review check MODEL.sysml --scope SCOPE.json --scope-sha256 RETAINED_DIGEST --source SOURCE_ID=SOURCE_PATH
```

`init-scope` creates an incomplete draft. Tailor it before retaining its digest;
`fingerprint` identifies bytes and does not approve the scope. Retain that digest
with the current review request/baseline and reuse it while editing the candidate.
Supply each source explicitly. Add `--json` for a machine report. Do not refresh
the retained digest merely to get past an unexpected scope change.

Allocation counts run only when the scope declares both the selected function
and resource bounds. No minimum is inferred. A bench or procedure cannot stand
in for a maintainer merely because a generic count passes: name the relevant
responsibility link explicitly. Counts do not establish competence, capacity or
substitutability. Evidence plans retain `not_run` results.

## Respond to findings

Explain the affected work and missing dependency in ordinary language. Repair
draft omissions and rerun affected checks. Use `concept-review scope-diff OLD NEW`
when proposing a scope change; preserve prior versions. Changes to accepted
intent, obligations, applicability, thresholds or selection are engineer decisions.
Do not delete an expectation, exclude its topic or relabel a plan as evidence to
obtain a pass. Incomplete drafts can continue with unknowns; unsupported semantics
need a suitable separately qualified operation.

Return the useful concept view, source/model/scope revisions, omissions and
unresolved questions. Distinguish native syntax/linkage, documentary coverage,
allocation counts and actual evaluation. A coverage pass cannot establish that
the scope is complete, the concept is feasible, staffing is adequate or operations
are validated. Narrative order and correspondence to reality require source and
engineering review. No task-network simulation, fatigue method or protected
acceptance mechanism is required by this procedure.
