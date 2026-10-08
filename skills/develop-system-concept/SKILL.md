---
name: develop-system-concept
description: Investigate needs, functions, alternatives and feasibility with the engineer; draft or revise a shared system concept.
---

Start from existing work and the current engineering question. Connect the present gap, desired outcomes, boundary and essential functions. Compare alternatives at the requested depth, retaining qualitative criteria and actual preferences. Test feasibility with relevant evidence or calculations. A framing question or unresolved comparison may be the complete task.

Preserve accepted intent, sources, assumptions, obligations and units. New
requirements, thresholds and interpretations remain proposals with their basis.
Ask only for missing intent that affects the current decision; continue useful
work with explicit unknowns. Routine edits and checks need no domain confirmation.
Use [domain elicitation](../../docs/interface/elicitation.md) when a consequential
answer needs validation; host safety confirmations are a separate channel.

For recorded work, read [SysML guidance](references/sysml.md); keep one shared
model or imported bundle with common IDs across requested skills. Respect
discussion-only scope. Keep raw/private material out of Git and reports; use
ignored `work/` for user models. Do not invent semantics to obtain a pass.

Run `python3 <skill-dir>/scripts/cse.py discover`, then `describe OPERATION`
only for the next operation. The JSON `invoke` adapter returns compact findings;
`--detail` retrieves complete evidence. Existing direct commands remain available.
After edits, run `check MODEL.sysml --syntax-only --kind concept`; run each requested
skill's shape check. Concept plus scenario work needs no full CONOPS. For supported
sampled clauses, generate synthetic tests and report coverage and limits.

Return useful readable views, saved-model links and actual findings. Keep parser
acceptance, compilation, synthetic tests, supplied behavior and engineer acceptance
distinct. Read [detailed workflow](references/workflow.md) for method depth,
[legacy contract](references/record.md) only for existing v1 JSON, and
[provenance](references/notes.md) only when explaining or revising the method.
