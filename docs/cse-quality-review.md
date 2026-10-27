# CSE delivery-chain review

Current follow-up and independent review: 2026-10-27. Scope: concept-development methods, selected
model/evidence contracts, prototype capture/observation, bounded view composition,
trace batching, standalone copies and regression/task-path evidence. This is a
source and software review, not an exhaustive upstream audit, intended-use
validation or standards conformity assessment. Earlier findings and failed
attempts remain in the private evidence history.

## Highest-priority remaining work

| Priority | Remaining issue | Current treatment / next evidence |
|---|---|---|
| High before real operations | Actual stakeholder need, eligibility/release obligations, part/supplier suitability, funds, competence, authority and retention obligations are unestablished. | Keep project findings UNKNOWN. `concept-review next-evidence` derives existing unresolved questions and linked plans from a fresh scoped review. The engineer selects investigations and responsible people; a dummy policy or textbook note supplies no real decision. |
| High before relying on the example's recovery behavior | Residual-copy recovery and missing-audit recovery are unsupported in the reference application. | [Synthetic regressions](../examples/prototype-evaluation/walkthrough/README.md) preserve copy/audit violations across no-change retries. [Named holds](../examples/prototype-evaluation/independent-holds.md) now preserve unrelated notices in the bounded local prototype; actual issuer authority and complete notice applicability remain unknown. These tests are not operational acceptance. |
| Medium during documentary review | Nonempty criteria or evaluation prose can pass coverage without being adequate. | Native synthetic tests retain a coverage pass for weak wording while a missing selected fact fails. Engineering review of criteria, handoffs and evidence sufficiency remains necessary; no automatic semantic-adequacy verdict is implemented. |
| Medium when stronger behavior claims are needed | General native workflow execution, per-work-order reservation ownership, production identity/cache revocation, external backup/restore, scale and physical erasure are outside the selected monitor/application. | Reuse the [behavior correspondence](behavior-review.md) and [prototype workflow](prototype-evaluation.md) for supported narrower questions. Select a concrete requirement/observation boundary before another extension; a native parse or sampled pass cannot substitute for these behaviors. |
| Medium for an ISO conformity claim | Complete applicable normative clause coverage has not been assessed. | The [standards/evidence map](engineering-terminology.md) distinguishes current alignment from missing normative text, applicability, tailoring and objective evidence. Do not invent clauses or treat grammar as requirement sufficiency. |
| Low if projects exceed supported composition | The composed profile is still bounded: 256 elements, 2048 relations, 16 views with at most 64 members each, one native file. | Larger/imported bundles need a separately supported contract. The legacy 64-element format remains unchanged; view composition does not provide general execution or architecture-description conformity. |
| Low | Standalone distribution still requires copies; private evidence includes historical artifacts. | One maintained copy inventory checks equality. Keep source authority and indexes; review any future generation/archive work. No historical artifact was deleted or reclassified as accepted. |

The repair/reuse example retains 92 checked documentary expectations, overall
UNKNOWN and nine full evaluation plans not_run. The separately saved 76-element
refinement is a proposal, retaining earlier intent, sources and unknowns. Its
128 selected expectations are checked; clean removal of revocation detail fails.
No supplier, competence, real retention period or authority was fabricated.

## Corrections completed

| Finding | Correction and bounded evidence |
|---|---|
| Authored Boolean traces supplied no executed-application evidence. | Optional SQLite dummy application, committed capture and a separate observer; authored fixtures remain synthetic. |
| Original nine obligations missed unauthorized non-revoked reads and unpermitted stock issues. | Actual faulty implementations reproduce both holes. A separate two-obligation supplement detects them, preserving the original nine meanings/manifest. |
| An observer could repeat the application's faulty permission decision. | Separate source recomputes permission from raw session/grant/epoch state; a substituted faulty application decision is detected. |
| Raw transaction snapshots retained content after logical disposition. | Current application captures presence/outcome facts instead of payloads; direct tests and an independent SQL/export inspection confirm capture minimization. Adapter v2 does not reinterpret old captures. Secure erasure remains unassessed. |
| Transaction order could be mistaken for physical sample time. | Explicit decision/committed/returned phases. Prototype projection admits row-local always clauses and refuses temporal/event claims. |
| Read-only regrant restored unrelated duties; count lacked read authorization. | Grants are replaced by the selected read scope; count requires stock-read permission. Targeted regression covers both. |
| Future eligibility could mask the deliberate hold defect. | Hold test runs after fixture eligibility; separate coverage retains early-eligibility refusal. No real period adopted. |
| Source artifacts and observer meaning could drift. | Each run freezes implementation/observer/driver bytes, checks stability and binds explicit artifacts/adapter revision. Hashes identify bytes, not authenticated authority. |
| Analysis harnesses were routed through concept draft-shape checks. | Narrow guidance correction applies the requested artifact's checks without inventing concept content; independent task-path follow-up verifies the correction. |
| Readiness/validated wording and old counts overstated qualification. | Historical counts are scoped; CLI/templates say parsing/structural or parser-checked. Verification, validation, architecture description and conformity have explicit terminology. |
| The 64-element format forced coarse grouping. | Explicit workflow 1.1 / scope 1.3 [view composition](concept-review.md) preserves global bindings/references/cycles and separately retained view membership. A 70-element native fixture and 76-element proposed case exercise cross-view omissions. Legacy bounds remain unchanged. |
| Repeated parsing added overhead to multi-trace studies. | Bounded process-local batch reuses parser extraction only; each case still runs the existing compiler/monitor. Input/checker/bridge/parser/library content drift invalidates the entire batch. Nine retained actual traces use one parse/eight reuses and retain all eight fault verdicts. No persistent cache or universal speedup claim. |
| Helper-copy maintenance and bespoke wrappers caused avoidable errors. | One standalone-copy inventory is checked by the regression gate, preserving independent skills. Existing prototype/concept-review routes handle common work; source/failed-attempt indexes remain explicit. |

Selected Zotero method notes informed the refinement and evidence workflow:
Buede–Miller on allocated architecture, cross-view coherence, early qualification
and retained rationale. They guide methods and do not establish this example's
real-world capability. Raw notes and course materials remain outside Git.

## Qualification and limits

The pre-review combined qualification covered **707 tests in 45 suites, no skips**, with
the pinned parser required. That earlier combined tree retained 19 unchanged initial suite passes plus the affected
gallery suite, 23 subsequent passes and two affected/unexecuted prototype suites.
The final remainder captured 400 input files unchanged; historical failures remain
recorded. This is combined qualification, not one uninterrupted clean run. Tests include legacy compatibility,
view deletion/membership drift, cross-view omission/cycles, evidence-plan
preservation, launcher use, stale/malformed inputs, source/runtime drift, analysis
limits, session cleanup and standalone-copy drift.

The batch's pass/fail/unknown/stale reports exactly match existing single-trace
checks, including counterexamples. Parser-call reduction was measured for the
selected study; time, memory, token savings and broader scalability are not
established. The batch does not promote recorded traces to executed evidence.

Earlier increments retain their own receipts: the initial prototype gate passed
491 tests; its capture correction yielded a combined 493-test qualification with
affected suites rerun. Those are historical, distinct from the fresh follow-up
gate. The earlier independent skill trial reproduced normal/fault/missing-data
behavior and the harness/capture corrections. That earlier follow-up had only self-review; the independent corrections below
supersede its software-review disposition. Engineering acceptance remains separate.

The rejected experimental diagram set remains historical. Acceptance of other
references does not transfer to it. This review published or reapproved no diagram.
Contract conformance, source/behavior correctness and usefulness remain separate
judgments; none establishes the other two.

Reproduction: [concept coverage/composition](concept-review.md), [prototype
verification](prototype-evaluation.md), [behavior/batch checks](behavior-review.md)
and `python3 scripts/standalone_copies.py`. Exact configurations, project-private
runs and failed attempts remain in the ignored work area.

## Independent review corrections

The independent contract/source-boundary review found no actionable issues in
its assigned scope. The independent runtime review found that incomplete or
mistyped captured facts could hide actual read, stock and hold faults, despite
correct artifact hashes. It also found malformed mandatory metadata being
accepted. Passing software tests had not covered these adversarial inputs.

That independently reviewed correction used application 1.2 / observer v3 with strict capture
admission before monitoring and typed mandatory metadata. Missing read presence,
integer/string substitutions, contradictory served outcomes, unknown stock values
and malformed hold flags cannot become Boolean false and pass. Original nine/
eleven requirement meanings remain unchanged. Earlier observer captures stay
historical/unsupported; current evidence needs a new execution. New regression
controls use actual faulty executions and coherently rehashed malformed captures,
not just happy-path projection tests. Current exact-head regression and CI
receipts qualify this correction separately from the earlier 707-test increment.

The subsequent named-hold repair uses application 1.3 / schema 2 / observer v4.
It keeps the original eleven requirement meanings and manifest, adds a separate
hold-preservation requirement/manifest, and replaces the Boolean-only example
with typed named rows. Fresh synthetic captures distinguish correct release
from an injected release-all regression. Earlier database/capture versions stay
historical, without implicit migration. This increment's self-review and tests
are separate from the independent review above; no engineering acceptance or
real authority is inferred.

These are software/contract reviews; they do not establish real project policy,
authority, intended-use validation, original-source authenticity, protected
execution, ISO conformity or engineering acceptance.

Audit evidence must match the selected operation action, target and actor in its transaction. Foreign audit rows do not satisfy the audit signal; they remain a monitor failure when the selected operation lacks its audit. Movement/policy/tombstone references and event/decision actor identity must agree with their captured targets. These are bounded reference-adapter correspondence checks, not authenticated real-world authority.
