# General concept development with bounded checks

> This document records a prior local working-tree assessment. A later integration requires fresh checks against its own revision.

The engineer selected this readiness target on 2026-10-27. CSE supports guided
concept development with explicit scope, sources, assumptions and unresolved
work. The local executable checks below have narrower contracts than the
engineering activity they assist. The engineer retains intent, applicability,
thresholds, weights and selection.

## Normal recorded workflow

Reuse the authoritative native SysML model and the relevant drafting skill.
Frame the current question and boundary; inspect the supplied sources; tailor a
separate project scope; connect functions, means, interfaces, scenarios and
selected evidence plans. Add task or ownership detail only when it informs the
current question. Compare alternatives qualitatively or with a supported
calculation whose inputs are justified. Run the selected checks, inspect their
findings, and revise the affected work. Keep incomplete drafts useful.

A draft's unresolved questions do not suppress selected documentary checks.
Missing selected facts can fail even when other facts remain unknown. Invalid
native input retains diagnostics and blocks those downstream checks. Changing
source bytes, identities or retained scope requires explicit reconciliation;
removing an obligation from the candidate does not remove it from the scope.

| Capability | Supported contract and result boundary |
|---|---|
| Concept, CONOPS, operational scenarios | Independently invocable drafting skills; shared native model and relevant minimal shape checks. Qualitative work remains available without a complete CONOPS. |
| Connected concept coverage | [Concept review](concept-review.md), scope versions 1.0–1.2, CSE-WORKFLOW/1.0. Selected identity/relation/evaluation-plan retention and optional count bounds. |
| Human task/function allocation | [Human-task profile](human-task-review.md), human-tasks-1.0. Selected task facts and performer roles, native identity/allocation linkage, source provenance and unresolved evidence. |
| Independent constituents/interfaces | [Ownership profile](ownership-review.md), ownership-1.0. Selected parties, duties, proposed/reported/unknown/withdrawn claims and agreement/change/withdrawal facts. Commitments remain unauthenticated. |
| Conditional capacity and alternatives | [Inquiry](inquiry-profile.md), inquiry-1.0/1.1. Exact supplied-rate calculations, explicit availability/capability/composition/shared-resource assumptions and separate assignment/capacity results. No automatic selection. |
| Conditional mean-flow consistency | Inquiry 1.1 optional flow checks, explicit applicability, boundary/population/averaging, compatible units and tolerance. No staffing inference. |
| Selected behavior questions | [Behavior correspondence](behavior-review.md): existing sampled clauses, correlated item/event deadlines and explicitly authored finite-verifier checks. Each retains its exact semantics, evidence and analysis limits. |
| Diagrams | Independent diagram-generation skill and synthetic source-linked examples. Model meaning, source/view labels and rendered review remain separate from execution claims. |

This work adds no native SysML behavior interpreter, general optimizer, protected
approval service, simulation of human task networks or fatigue model. A finite
completion path does not establish all-schedule progress. A source digest does
not establish truth or assent; a proposed duration does not establish capacity.
The [first-version brief](first-version-brief.md) and individual contracts retain
the trusted-execution and semantic boundaries.

## Qualification and remaining project evidence

The 2026-10-27 local source is ready for this bounded-use target. Qualification
completed 452 tests across 28 suites with no skips, on Linux x86_64, Python 3.12.3
and Java 26.0.2.1 with the pinned 2025-09 / 0.52.0 parser. The initial full run
stopped on an outdated assertion about incomplete drafts; unchanged passing
suites were retained and the affected/unexecuted suites completed under checked
source identities. The failed run and fresh continuation are both preserved.

Qualification is local to the tested Linux/Python/Java/pinned-parser environment
and the exact working source snapshot. Required regressions use
`python3 scripts/check.py --require-sysml`. Public synthetic cases challenge
omissions, identity/source changes, unsupported profiles and incomplete checks.
An independent skill forward-test uses a fresh synthetic project and retains
first outputs, repairs, scope and diagnostic controls. This is a software/task
trial; it does not provide independent engineering acceptance or platform parity.

A real project still needs representative demand and task observations, competence
and recovery evidence, justified automation roles, measured resource availability,
stakeholder preferences, authentic agreements and applicable domain validation.
Selected Zotero notes and historical engineering literature identify methods and
questions; they cannot supply those observations or commitments. Advanced native
concurrency, scheduling/optimization and continuous behavior need separately
scoped support when a project actually requires them.
