---
name: develop-system-concept
description: Explore or revise a system concept by connecting a problem, desired outcomes, functions, alternatives and feasibility evidence. Use for decisions about what a system should accomplish and which approaches merit investigation.
---

Help the engineer decide the current concept question. A diagnosis, boundary clarification or comparison of alternatives can be the whole result.

- Start with supplied observations and accepted decisions. Where framing is unsettled, distinguish the reported situation, desired change, possible causes and proposed solutions. Investigate competing explanations when the difference would change the design. Link needs to functions and conditions before committing to components.
- Compare viable approaches against the engineer's objectives and constraints. Include people, integration and lifecycle effects where they affect the decision. Use quantitative criteria and weights only when there is a basis for them. For a consequential claim, state what evidence could support or overturn it and choose a proportionate observation, calculation, prototype or simulation.
- Preserve agreed scope, assumptions and preferences. Keep inferred needs, requirements and thresholds as proposals with their basis. Ask only for consequential missing intent and continue with explicit unknowns where possible. Keep external investigations within the requested authority.

Use [meaning and context](../../docs/meaning-context.md) to check that the proposed concept and delivered view carry source conditions, goals and evidence. Load a focused method when it answers the question:

| Question | Method |
|---|---|
| How should the team refine functions, parts, allocations or interfaces? | [Architecture handoff](references/architecture-handoff.md) |
| Which scenario or operating context would change the concept? | [Operational scenarios](../develop-operational-scenarios/SKILL.md) or [CONOPS](../develop-conops/SKILL.md), using the same model and IDs |
| Who performs the work, and under what conditions? | [Human tasks and allocation](../../docs/human-task-review.md) |
| Who owns, funds, operates or accepts a shared element? | [Ownership review](../../docs/ownership-review.md) |
| Can a resource meet a conditional capacity or workload need? | [Resource inquiry](../../docs/inquiry-profile.md) using `cse.py question answer` with explicit sources and unit, availability and rate assumptions |
| Does a function/flow contract, calculation or proposed behavior hold? | [Bounded analysis](../../docs/engineering-analysis.md) or [behavior review](../../docs/behavior-review.md) |
| What did a prototype actually do? | [Prototype observations](../../docs/prototype-evaluation.md) under separately retained obligations |

### Recorded concept

Use one authoritative SysML v2 model and stable IDs. Read the [record and check guide](references/sysml.md) and use the [synthetic template](templates/default.sysml) when helpful. Keep project inputs and outputs private. Run `python3 <skill-dir>/scripts/cse.py check MODEL.sysml --syntax-only --kind concept` after edits and apply the selected [English profile](../check-engineering-language/SKILL.md).

For recorded concept development, use [project-tailored review](references/concept-review.md). Start with existing retained scope or propose a small scope based on the question and sources. Run `cse.py concept-review check` after relevant changes. Keep the obligation set outside the candidate so a missing function, responsibility or evaluation plan remains detectable. A discussion can finish without model or scope files.

For version-1 JSON, use the [legacy record contract](references/record.md) and its own helper. For relevant user interactions and handoffs, use [connected walkthroughs](../../docs/interaction-walkthroughs.md). See [method provenance](references/notes.md) when explaining the method.

### Review the result

Deliver the requested concept or decision comparison with source/model IDs, assumptions that affect the choice, and the evidence or decision still needed. Feed findings back to the affected outcome, boundary, function, means, scenario or evaluation method. Report actual checks with their limits. Use [work review](references/work-review.md) for dependent outputs or difficult failures and [document guidance](../../docs/technical-documents.md) for a formal deliverable.
