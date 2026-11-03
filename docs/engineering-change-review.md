# Bounded engineering change review

Use this workflow when a revision may affect other requirements, evidence or
delivered views. Reuse the authoritative model and existing question, decision
and evidence records. Preserve the prior revision and selected scope before
editing; retain all explicitly supplied dependency files and source versions.

## Find the change and its possible consequences

For native SysML, run the existing deterministic diff from any working directory:

```text
python3 <skills-dir>/develop-system-concept/scripts/cse.py diff --before OLD.sysml --after NEW.sysml
python3 <skills-dir>/develop-system-concept/scripts/cse.py view NEW.sysml --id AFFECTED_ID
```

Repeat `--before` and `--after` for model bundles. The diff identifies structural
and documentary changes and conservative **direct** impact. The separate
[impact helper](impact-analysis.md) now propagates changes through explicit
dependency graphs from both revisions and proposes a retained check selection.
Its native/workflow snapshots expose unresolved coverage and conservatively
select all retained checks. Complete native semantic propagation and automatic
execution of selected regressions remain unimplemented.
A successful diff operation is not a successful engineering review.

For existing version-1 operational records, the legacy
`conops.py diff OLD.json NEW.json` reports transitively affected dependents
within that declared record graph. Its `view` and selected `check --scenario ID`
are available; this does not confer native SysML dependency semantics.

Use the program's changed IDs and typed relations to inspect potentially affected
requirements, allocations, interfaces, scenarios, decisions, evidence and views.
Trace reverse dependencies where their semantics are explicitly declared; retain
each reason for including an affected item. Inspect imports and external evidence
dependencies too. Mark missing/unmodeled dependencies unknown. Human/LLM review
can identify candidates but cannot certify a complete transitive closure or
supply a complete native impact verdict beyond the supported graph. Broaden checks when
the current impact information cannot justify a narrower selection.

## Retain the decision context and recheck

Describe the proposed change, retained obligations and any intended change to
scope or meaning. Use existing decision fields to link the information available
at the decision revision, relevant uncertainty, reasons for the choice, affected
IDs and reconsideration trigger. Preserve the prior rationale when new evidence
changes the choice. A model's decision status or digest authenticates no assent.

Select rechecks by the dependency and claim affected: parser/draft shape for model
edits; compilation/finite checks for supported logical conditions; concept or
configuration review for selected documentary/structural obligations; calculation
for changed quantities/assumptions; prototype observation review or a new run for
changed implementation, fixture or observer. Read each existing contract and
retain its independent scope or manifest; never regenerate an accepted scope
from the revised candidate to hide a missing obligation.

Run the selected checks and relevant global checks; report both selection reasons
and unresolved coverage. A focused result says nothing about omitted obligations.
Mark changed-input evidence stale pending the appropriate fresh check/run. Do not
rewrite an old observation to fit a new model or erase the original failure.
Regenerate affected delivered views and reconcile their source IDs/revision.

Return changed IDs, possible impacts with reasons, actual check outcomes,
unexamined dependencies and the next engineer decision. Distinguish an ordinary
artifact repair from a proposal to relax requirements or change accepted intent.
Incomplete, unsupported or failed required checks remain unresolved.

This workflow distills dependency/change and rationale ideas from Delligatti,
*SysML Distilled*, Chapter 3, and Buede and Miller, 4th edition, Chapters 9 and 13.
The separate impact contract defines the new bounded propagation and selection
rules. This workflow adds no automatic regression execution or approval service.
