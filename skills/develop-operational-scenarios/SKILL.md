---
name: develop-operational-scenarios
description: Develop or revise a selected operational scenario, including normal operation, exceptions, recovery or lifecycle work. Use for actors, ordered exchanges, conditions and observable outcomes.
---

Make the selected scenario legible to someone who needs to walk through the operation. Reuse the existing boundary, actors and IDs. One scenario or one branch can be the whole task.

- Establish the need, setting, trigger and intended observable outcome. Use supplied observations and link their sources. Where intent is unclear, distinguish reported work, the desired change and possible explanations. Keep proposed steps and unknowns visible.
- Describe the relevant ordered exchanges, with performers, items or information, handoff conditions and normal or recovery outcomes. Start with a simple useful path for new exploration and add complexity that changes the answer. Preserve requested prototype fidelity and keep implementation choices open where undecided.
- Connect findings to any affected concept, function, boundary, assumption or evidence plan. The engineer decides consequential interpretations, obligations and changes to accepted operation.

Use [meaning and context](../../docs/meaning-context.md) to review source correspondence. Load the method that answers the question:

- [Use-case refinement](references/use-case-refinement.md) for required included behavior or conditional extensions.
- [Activity and function review](references/activity-review.md) for enabling, control/object flow, forks, joins and termination. Documentary order and native parsing do not execute include/extend or general concurrent token semantics.
- [Human-task review](../../docs/human-task-review.md) when performer, equipment, competence, concurrency or recovery facts matter. If those facts require a retained concept-review scope, use the same model and that selected scope alongside the scenario check. An assignment or proposed duration does not establish staffing adequacy.
- [Behavior review](../../docs/behavior-review.md) or [bounded analysis](../../docs/engineering-analysis.md) for supported execution or calculations. A path to completion and progress under every schedule are distinct claims.
- [Interaction walkthroughs](../../docs/interaction-walkthroughs.md) for relevant user interactions and handoffs. Use feedback to decide what to expand.

### Recorded scenario

Use the [SysML record guide](references/sysml.md), including its documentary function-tree and sequence contracts, and the [synthetic template](templates/default.sysml) when useful. Run `python3 <skill-dir>/scripts/cse.py check MODEL.sysml --syntax-only --kind scenario` after edits. Apply the selected [English profile](../check-engineering-language/SKILL.md).

For an existing version-1 record, run `python3 <skill-dir>/scripts/conops.py check RECORD.json --scenario ID` using the [legacy contract](references/record.md). For a separately authored finite model with supported guards and effects, use the [finite review route](references/sysml.md#run-the-applicable-checks) and supply the independently retained manifest when available. Keep project inputs and outputs private. See [method provenance](references/notes.md) when explaining the method.

### Review the result

Walk the delivered scenario against its source and stated trigger. Check each exchange's sender, recipient, conditions and effect where known, including the declared recovery endpoint when requested. Return the selected scenario with model IDs, actual check outcomes and consequential unknowns. Use [work review](references/work-review.md) for dependent outputs and [document guidance](../../docs/technical-documents.md) for a formal deliverable.
