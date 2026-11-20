---
name: develop-system-architecture
description: Develop or review functions, physical parts, allocations or interfaces in a connected system model. Use for architecture decisions and correspondence between views.
---

Resolve the architecture question at the scale of the decision. A single interface, missing function or allocation can be the entire task. Reuse the existing boundary, outcomes, scenarios and accepted decisions. Use [concept development](../develop-system-concept/SKILL.md) when the underlying need or scope is unsettled.

| If the question concerns | Use |
|---|---|
| Transformations, decomposition or missing work | [Functional architecture](references/functional.md) |
| Parts, types, ownership, multiplicities or configuration | [Physical architecture](references/physical.md) |
| Function performers, resources or accountable parties | [Allocation](references/allocation.md) |
| Endpoints, direction, exchanged items or conditions | [Interfaces](references/interfaces.md) |

Maintain the authoritative SysML v2 model and stable IDs. Apply [meaning and context](../../docs/meaning-context.md) and the [native record contract](../develop-system-concept/references/sysml.md). Link analysis profiles to the selected model. Keep inferred functions, allocations and interface obligations as proposals with their basis. Component artwork and presentation IDs cannot declare architecture meaning.

After native edits, run `python3 <skills-dir>/develop-system-concept/scripts/cse.py check MODEL.sysml --syntax-only` using the absolute launcher path and every needed model file. Add concept or scenario shape checks when those artifacts are requested. Apply the selected [English profile](../check-engineering-language/SKILL.md). For unavailable native execution, report the unrun checks and finish the supported review. Keep project materials private.

Check the delivered view for source-bound roles and relationships, applicable conditions, and unresolved correspondences. Return the selected architecture with its model revision, material assumptions, actual check outcomes and engineer decisions. Use [work review](../develop-system-concept/references/work-review.md) for dependent outputs or difficult failures. Use [diagrams](../generate-engineering-diagrams/SKILL.md), [technical documents](../../docs/technical-documents.md) or [evidence planning](../plan-engineering-evidence/SKILL.md) for those requested deliverables.
