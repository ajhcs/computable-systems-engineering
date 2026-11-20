---
name: coordinate-engineering-work
description: Coordinate a systems engineering question that crosses activities or has an unclear entry point. Connect model edits, checks and deliverables across the relevant CSE skills.
---

Identify the current engineering question, requested result, source revision and how the engineer will review it. Use the existing model and begin with the activity that can answer the question. A single activity may be enough.

| When the question concerns | Read |
|---|---|
| Problem framing, desired outcomes or alternatives | [System concept](../develop-system-concept/SKILL.md) |
| Operating concept, lifecycle or responsibilities across scenarios | [CONOPS](../develop-conops/SKILL.md) |
| One operational sequence, exception or recovery | [Operational scenarios](../develop-operational-scenarios/SKILL.md) |
| Functions, parts, allocations or interfaces | [System architecture](../develop-system-architecture/SKILL.md) |
| Quantity, collection conditions or baseline meaning | [Engineering measures](../define-engineering-measures/SKILL.md) |
| Verification, intended use or testability | [Evidence planning](../plan-engineering-evidence/SKILL.md) |
| Waiting and utilization | [Queue analysis](../analyze-queues/SKILL.md) |
| Fault tree or FMEA record | [Failure analysis](../analyze-system-failures/SKILL.md) |
| Project terminology and controlled English | [Engineering language](../check-engineering-language/SKILL.md) |
| A source-linked view or reusable graphic | [Diagrams and components](../generate-engineering-diagrams/SKILL.md) |

Carry the same model revisions, stable IDs, governing conditions, unknowns and engineer decisions through each activity. Apply [meaning and context](../../docs/meaning-context.md) to the actual outputs. Keep project inputs and reports in the project's private workspace.

For connected changes, use the relevant part of [work review](../develop-system-concept/references/work-review.md). Use subagents as needed, where authorized, for independent investigations or artifact reviews with distinct inputs and outputs. Keep one owner for changes to shared definitions and reconcile findings against the same source revision.

Load additional methods when needed:

- For exact calculations or function/flow correspondence, select a mode in [engineering analysis](../../docs/engineering-analysis.md).
- After a model or evidence change, identify affected outputs through [change review](../../docs/engineering-change-review.md). Use [impact analysis](references/impact-analysis.md) for declared propagation and widen rechecks when native dependency coverage is incomplete.
- For implementation increments, goal-seeking or decision rationale, use the [CONOPS method](../develop-conops/references/iteration-and-rationale.md).
- For a proposal, report, manual or drawing set, use [technical document guidance](../../docs/technical-documents.md) and resolve any requested visual reference before layout.

Finish when the requested artifacts agree with the authoritative model and the applicable checks have been examined against independently retained scope. A compact drafting view leaves check scope intact. Deliver the primary artifact first, with material findings, unresolved evidence and decisions that remain with the engineer. Carry new evidence back to each affected view or proposal.
