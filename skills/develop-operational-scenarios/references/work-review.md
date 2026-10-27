# Planning, diagnosis and review

Read the relevant section for a change with several dependent outputs, a difficult
check failure, or a review handoff. A discussion or small edit can proceed
directly. The user's explicit instructions take precedence over this guidance;
use existing authorization and preserve the engineer's decision authority.

## Plan a connected change

Keep a short plan in the conversation or existing private work record. Identify
the current question, source/model revisions and selected IDs, intended outputs,
dependencies, applicable checks and the evidence expected from each. Distinguish
a proposed check from an executed one. Reuse the current model and review scope;
the plan is a work aid, not a second engineering model or a new obligation set.

Choose work units with inspectable outcomes, such as revising a selected scenario
and its derived view together. Identify unresolved inputs that affect those
outcomes. Continue independent authorized work while consequential decisions are
pending. Revise the plan when evidence changes the approach, preserving deferred
work and the reason. Do not require a design document or repeat an approval
already given for routine drafting and repair.

When delegation is authorized and available, give each worker explicit files/IDs,
input revisions, output responsibilities and dependency boundaries. Reconcile
shared definitions and overlapping writers before edits. Integrate against the
same source revision and inspect actual changes and evidence; an agent's success
message is insufficient. Otherwise carry out the work in the current session.

## Diagnose a failed check

Retain the actual command, input revision, selected scope and diagnostic or
counterexample. Trace the finding to affected source/model IDs. Distinguish a
model defect from missing or stale evidence, unsupported semantics, analysis
limits, and tool/environment failure. Compare a relevant working example when
useful. State a testable explanation, make the smallest justified correction and
rerun the affected check and dependent checks whose inputs changed.

Preserve accepted thresholds, obligations, applicability and source meaning.
Changing these, changing the checker, or deleting a failing item is a separate
proposal rather than a routine model repair. Unsupported analysis remains
unsupported; a different check must be named with its own limits. Set a
proportionate effort bound for repeated repair. If further attempts produce no
useful evidence, stop that loop and report the unresolved cause and next evidence
or decision needed. Other independent drafting may continue.

## Review a candidate and handle findings

For requested or consequential review, supply the question, relevant source and
baseline revisions, selected IDs, candidate/diff, actual check reports and known
limits. Use an independent reviewer when authorized and available; otherwise
identify the review as self-review. Ask separately whether source meaning and
requested scope were preserved, and whether the reasoning, model and delivered
views are sound and usable. A checker pass cannot answer both questions.

Check each review finding against sources, contracts and the actual candidate
before editing. Correct supported defects within scope; explain disagreement
with evidence and keep unresolved findings visible. A reviewer's recommendation
does not establish an engineer decision. Escalate only the consequential meaning
choice, while continuing unrelated authorized corrections.

## Close the requested work

Reconcile requested outputs and selected scope with delivered artifacts and any
omitted or deferred work. Bind reported checks to the actual input/dependency
revisions, scope, tool/rules version and applicable limits. Reuse a receipt only
when those bindings still match; rerun affected checks after changes. Read exit
status and findings, including missing required checks, rather than trusting a
summary label. State what passed, failed, remained unknown or unsupported, or was
not run. Keep documentary, synthetic, observed and acceptance claims distinct.
