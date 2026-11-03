# Declared dependency impact

Load this reference when changed model/source revisions need transitive reason
paths or a proposal for regression selection. Use the existing change-review
workflow for rationale and engineer decisions.

Read the selected contract in [impact analysis](../../../docs/impact-analysis.md).
Retain baseline and candidate snapshots plus an independent check scope before
editing. Run `scripts/impact.py`; for native workflow files its `native-snapshot`
operation reuses the pinned parser and existing workflow IDs. It retains omitted
native/import meaning as unresolved, so incomplete coverage selects every retained
check. Supply documentary relation directions explicitly; do not infer them from
labels. Preserve historical removed identities and their reason paths.

Run selected checks using their existing independent contracts and keep relevant
global checks. Selection is a proposal and performs no tests. Unknown coverage,
exceeded limits and stale scope pins cannot establish successful review. Report
actual recheck outcomes, unresolved dependencies and the next engineer decision.
