---
name: develop-conops
description: Develop or revise a concept of operations that connects stakeholder outcomes, system boundaries, operating modes, responsibilities, scenarios and evaluation. Use the scenario skill for an individual sequence.
---

Answer the requested operating question at the current design stage. Use existing decisions and scenarios. A clarification, proposal or edited slice can be the complete result.

- Connect intended outcomes and stakeholders to the system boundary, external roles, operating modes and relevant lifecycle conditions. Use source-linked notes. If framing is unsettled, distinguish the situation, desired change, possible explanation and proposed solution.
- Walk the relevant operations end to end. Carry existing actors, triggers, intended outcomes and IDs into any [scenario development](../develop-operational-scenarios/SKILL.md). Expose disagreements, unassigned responsibilities and deferred cases with their consequences.
- Identify uncertainties that would change the operating concept. Use a source, observation or prototype when it can inform that choice. Link evaluation to the affected decisions through [evidence planning](../plan-engineering-evidence/SKILL.md). Use [goals, obligations and increments](references/iteration-and-rationale.md) for staged delivery or to record a rationale and reconsideration trigger.

Preserve accepted intent, conditions and thresholds. Keep inferred obligations and changes to responsibility proposed. Continue with explicit unknowns where possible. Use [meaning and context](../../docs/meaning-context.md) to review what the delivered work carries from the sources.

### Recorded CONOPS

Use the [SysML record guide](references/sysml.md) and [synthetic template](templates/default.sysml). Keep one authoritative model and stable IDs across views. Run `python3 <skill-dir>/scripts/cse.py check MODEL.sysml --syntax-only --kind conops` after edits. The record guide covers supported sampled clauses, required review, tool setup and [legacy version-1 records](references/record.md). Apply the selected [English profile](../check-engineering-language/SKILL.md) and keep project materials private.

Use [bounded engineering analysis](../../docs/engineering-analysis.md) or [behavior review](../../docs/behavior-review.md) for the selected claim. For relevant user interactions or handoffs, use [connected walkthroughs](../../docs/interaction-walkthroughs.md). Read [method provenance](references/notes.md) when explaining the method.

### Review the result

Check that the selected operations have clear initiating conditions, roles, exchanges and outcomes where known. Trace material evidence or unresolved questions back to the affected assumptions and decisions. Deliver the requested view with actual checks and their limits. Treat documentary operating intent and observed work as different evidence. Use [work review](references/work-review.md) for coupled outputs or difficult failures and [document guidance](../../docs/technical-documents.md) for a formal CONOPS.
