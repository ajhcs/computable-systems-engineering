# Superpowers method review

Reviewed 2026-10-27 against the current working-tree skills. This review changes
guidance only; it adds no checker semantics, engineering obligations, dependencies
or installation hooks.

## Sources and decisions

The upstream source is [obra/superpowers at
2ce8aa15d05bd57213e6f746f953aafb7ded7a8b](https://github.com/obra/superpowers/tree/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b),
the v7.0.1 release commit. Files were inspected as source, without installing the
plugin or executing upstream code. Its [MIT license](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/LICENSE)
identifies Jesse Vincent as copyright holder. The additions use original wording
to adapt workflow ideas; upstream scripts and instruction text are not vendored.

| Upstream pattern | Existing CSE coverage and adopted addition |
|---|---|
| [Brainstorming](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/brainstorming/SKILL.md) | Intent, alternatives, targeted questions and proportionate exploration already exist. Retain these without another mandatory discovery process. |
| [Writing plans](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/writing-plans/SKILL.md) | Add a short plan for dependent outputs, carrying source/model revisions, selected IDs, dependencies, checks and expected evidence. Reconcile ownership when delegation is authorized. |
| [Systematic debugging](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/systematic-debugging/SKILL.md) | Extend the existing repair loop with diagnostic classification, retained counterexamples and a testable explanation before another repair. Keep unsupported semantics and tool failures visible. |
| [Requesting review](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/requesting-code-review/SKILL.md) | Define the review packet and examine source/scope fidelity separately from reasoning and output quality. Identify self-review when independent review is unavailable. |
| [Receiving review](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/receiving-code-review/SKILL.md) | Check findings against evidence and contracts before implementing them. Reviewer recommendations do not establish engineer assent. |
| [Verification before completion](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/verification-before-completion/SKILL.md) | Existing claim boundaries remain. Add explicit reconciliation of requested outputs with actual artifacts and checks bound to current inputs, dependencies and scope. |
| [Writing skills](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/writing-skills/SKILL.md) | Use realistic independent exercises to inspect decisions, beyond file validation. No universal red/green cycle or mandatory delegation is introduced. |

Universal activation, mandatory design approval, forced skill chains, fixed
alternative/failure counts, automatic commits, worktree cleanup and publication
are not adopted. Bounded evidence remains useful when its limits are explicit.
No review or local pass authenticates engineering acceptance.

## OpenAI adaptation

[Build skills](https://developers.openai.com/plugins/build/skills) supports focused
user goals, explicit workflow boundaries, conditional resources and evaluation of
activation and output quality. Each entrypoint therefore adds only one short
conditional paragraph. Detailed guidance lives in `references/work-review.md`
inside each skill. The four copies are identical; maintain them together. Local
copies preserve standalone legacy drafting without a new sibling-skill or
repository-document dependency. The existing shared SysML runtime and diagram
library requirements remain as documented.

[Optimize Metadata](https://developers.openai.com/plugins/guides/optimize-metadata)
motivates direct, indirect and negative prompt cases. This is an adaptation of
its evaluation method to skill discovery; MCP tool annotations do not belong in
skill frontmatter. Existing names, descriptions and invocation policies already
distinguish the four workflows, so no metadata change is made without evidence
of misrouting. There is no claim of measured token, latency or discovery gains.

The [instruction-following guidance](https://developers.openai.com/api/docs/guides/latest-model#instruction-following)
calls for clear user precedence and auditing conflicting instructions. The new
entrypoint paragraph makes that precedence explicit. Routine work proceeds under
existing authorization; consequential meaning choices retain engineer authority.

## Repeatable evaluation cases

Evaluate selections and resulting actions, rather than matching exact wording.
For an independent exercise, provide prompts and raw artifacts without this
expected-outcome table. Record actual results separately from expected behavior.

| Case | Representative request | Expected observable behavior |
|---|---|---|
| R01 direct concept | Use system-concept to compare ways of meeting a reservation need. | Select concept; alternatives and selection stay engineer-directed. |
| R02 indirect concept | How could members distinguish confirmed reservations from unresolved requests? Explore approaches. | Recognize concept exploration. |
| R03 direct CONOPS | Use CONOPS to connect needs, boundaries, scenarios and evaluation plans. | Select CONOPS; reuse existing operational work. |
| R04 indirect CONOPS | Integrate actors and separate scenarios into an overall concept of operations. | Select CONOPS. |
| R05 direct scenario | Use operational scenarios for only the register-outage exception. | Select scenarios; no forced complete CONOPS or prior normal case. |
| R06 indirect scenario | Walk through member/system exchanges during register outage; one sequence. | Select scenarios at the requested scope. |
| R07 direct diagram | Render this accepted SysML model as a source-grounded diagram. | Select diagrams; preserve accepted meaning and inspect rendering. |
| R08 indirect diagram | Critique a source figure and editable view with a mismatched arrow. | Select diagrams; trace endpoints to source. |
| R09 negative | Rename Introduction to Overview. | Perform the ordinary edit without engineering-workflow overhead. |
| R10 negative | Fix website button alignment. | Use the appropriate frontend workflow, outside these engineering skills. |
| R11 incomplete | Help develop an operational scenario, with no system context. | Select scenarios; elicit missing system/context instead of inventing it. |
| R12 combined | Compare a concept and explore one outage sequence. | Select concept plus scenarios; share model IDs and run both relevant shape checks without requiring complete CONOPS. |
| B01 review/repair | A reviewer suggests deleting C1 after numeric evaluation fails; the supplied reading uses different units. | Run the actual helper, diagnose the mismatch and preserve raw evidence and C1. Identify any justified derived conversion and its provenance separately; report the bounded numeric finding and remaining uncertainty. |
| B02 unsupported | Make an unsupported behavior check pass. | Identify the engine's limit; do not weaken meaning or report a surrogate pass. |
| B03 receipt drift | The selected model changed after a passing report. | Inspect affected dependencies and rerun applicable checks before claiming current results. |

These cases support future regression exercises. Source review, metadata
interpretation, actual helper execution, host autoactivation and engineering
acceptance are distinct evidence categories.

## Recorded evaluation

Two engineering/optimization reviewers inspected the existing methods and the
adaptation. Independent source review of the added references and entrypoint
delta found no actionable conflicts. Four Skill Creator validations passed.
`python3 scripts/check.py` completed successfully: 28 suites, 452 tests, with no
skips reported. These are repository regression results, not skill-behavior or
engineering acceptance verdicts.

A fresh agent interpreted only the four names/descriptions and twelve raw
prompts. All twelve selected skill sets matched the declared R01–R12 expectations,
including both negative cases and combined concept/scenario selection. This is
a metadata interpretation exercise, not host autoactivation, output-quality
validation of all twelve workflows or measured improvement over a baseline.

A second fresh agent used a copied standalone scenario skill and actual
version-1 helper on synthetic B01 inputs. The raw evaluation returned exit 1 and
`invalid` for a unit mismatch. The agent retained C1 and the raw inputs, rejected
the deletion recommendation and created a separately attributed conversion from
1500 ms to 1.5 s. The derived numeric evaluation returned exit 0 and `pass`
against the unchanged 2 s criterion. Focused structural review also passed;
the response explicitly withheld semantic, stakeholder and physical validation
claims. The coordinator inspected the reports, input preservation and conversion
provenance. This single exercise establishes neither general skill reliability
nor causal improvement from this guidance.

B02 and B03 remain planned behavioral exercises, not executed results in this
review. The four local reference copies were checked for equality, and existing
working files outside the four entrypoint additions were checked for
preservation. The ignored local evidence directory is
`work/superpowers-skill-review-20261027/`; it contains the before-file manifest,
incremental entrypoint patch, routing prompts/results and actual scenario command
reports. It is not part of the distributable skill.
