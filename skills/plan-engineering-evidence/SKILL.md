---
name: plan-engineering-evidence
description: Plan verification against specified requirements or validation against intended use, including method selection, early testability and feedback from intermediate products. Use for evidence planning; execution uses the existing CSE checks and selected tools.
---

Help the engineer answer a specific evidence question at the current design stage.
A focused plan or review of an intermediate product can be the complete task.
Reuse the authoritative model, stable IDs and revision; do not require a complete
CONOPS or turn qualitative intent into an executable requirement.

For engineering claims and implementation, use [meaning and context](../../docs/meaning-context.md)
before drafting and when reviewing the actual output.

Identify the claim, its target and source, applicable conditions, and the decision
the evidence should inform. Distinguish verification of specified requirements
from validation of stakeholder needs in intended use. A requirement check alone
cannot establish suitability for use. Preserve accepted obligations and the
engineer's authority over applicability, thresholds and validation judgments.
Keep missing intent, data and authority explicit; propose consequential changes.

Select inspection, test, analysis/simulation or demonstration using the relevant
section of [method selection](references/methods.md). Combine methods only when
they answer distinct parts of the question. Before committing to an architecture
or implementation, read [testability and feedback](references/testability.md) to
identify observation points, fixtures, equipment and manual effort. When a
measurement is needed, use [define-engineering-measures](../define-engineering-measures/SKILL.md)
for its meaning and conditions before selecting instruments or thresholds.

For recorded work, use the existing `cseWorkflow` evidence entries and linked
questions/decisions described in the [workflow record contract](../../docs/concept-review.md#authoritative-sysml-documentary-record).
Retain target, purpose, method, environment, basis and limitations there; keep
plans at `mode: plan`, `result: not_run`. Put observation definitions, equipment
and fixture dependencies, definition IDs/revisions and evidence locations in the
existing documentary fields or linked artifacts. Do not add a competing generic
evidence schema. Keep project models, raw sources and run reports in the selected
project's private workspace, outside an installed plugin.

When an independently retained concept scope already exists, derive the next
investigation from a fresh review:

```text
python3 <skills-dir>/develop-system-concept/scripts/cse.py concept-review next-evidence MODEL.sysml --scope SCOPE.json --scope-sha256 RETAINED_DIGEST --source ID=SOURCE_PATH
```

Repeat `--source` and supply model dependencies as the existing contract requires.
Do not create concept obligations just to plan scenario evidence. This sibling
launcher resolves the complete CSE pack from any working directory; a copied
evidence skill alone supplies guidance, not an installed runtime.

Execute only authorized investigations using the selected tool's contract.
Reuse [existing analysis and finite checks](../../docs/engineering-analysis.md),
`testgen` for synthetic variable-influence examples, or
[prototype-review](../../docs/prototype-evaluation.md) for captured prototype
observations. Generated examples and unexecuted plans are not observed evidence.
For aligned measurements, select the applicable [observation computation](../../docs/observation-validation.md).
For a queue or explicit failure model, use [queue analysis](../analyze-queues/SKILL.md)
or [failure analysis](../analyze-system-failures/SKILL.md) only when it answers the claim.
Use actual program findings for deterministic verdicts; missing, unsupported,
incomplete or errored checks cannot satisfy a required review.

For generated calculations, diagrams or documents, use [artifact freshness](../../docs/artifact-freshness.md) to retain the file scope and reject stale outputs. For interacting mathematical models, use [coupled calculations](../../docs/coupled-calculations.md).

Return the plan or observed finding, affected IDs/revision, material limits and
next decision. Feed findings into the affected intermediate product; use
[change review](../../docs/engineering-change-review.md) when repairs cross
dependencies. Preserve failed findings and rerun applicable checks after repair.
An assessment label or hash authenticates no observation or engineer acceptance.
