---
name: develop-system-architecture
description: Develop or review a connected slice of functional, physical, allocated or interface architecture from an engineer's question and existing model. Use for architecture meaning and correspondence; diagram rendering has a separate skill.
---

Develop the architecture needed for the current engineering decision. A single
interface, missing function or allocation question can be the whole task. Reuse
the existing boundary, stakeholder outcomes, scenarios and accepted decisions;
use [system-concept development](../develop-system-concept/SKILL.md) only when
those need investigation. Do not require a complete CONOPS or detailed design.

The engineer directs intent, applicability, responsibility policies, thresholds
and selection. Mark inferred functions, allocations and interface obligations as
proposals with their source or rationale. Repair ordinary draft/check defects
within scope; preserve accepted meaning and prior failed findings. Missing facts
remain unknown. Do not narrow retained obligations to obtain a pass.

Select only the method needed now:

- [Functional architecture](references/functional.md): transformations,
  decomposition and a scenario walk to locate missing or overlapping work.
- [Physical architecture](references/physical.md): parts, types, ownership,
  multiplicity and selected configuration.
- [Allocation](references/allocation.md): functions, performers, resources and
  accountable parties under project-selected policies.
- [Interfaces](references/interfaces.md): endpoints, exchanged items, direction,
  conditions and source-linked obligations.

For recorded work, keep the existing SysML v2 model authoritative and retain
stable IDs across views. Read the [native record contract](../develop-system-concept/references/sysml.md)
before editing a model. Selected analysis profiles are explicit check inputs,
not competing architecture definitions. Keep raw sources, private annotations
and user models in the selected project's private workspace, outside the plugin
and Git; distribute only concise attributed derivatives.

Use the shared launcher at
`<architecture-skill-dir>/../develop-system-concept/scripts/cse.py` in the complete
plugin or checkout. Resolve its absolute path before running from another
directory; input paths remain relative to the caller. Run
`python3 <launcher> check MODEL.sysml --syntax-only` after native edits, supplying
every required model file explicitly. There is no architecture `--kind` shape
check. Run additional concept/scenario shapes only when those artifacts are part
of the requested work. Local native checks require Python 3.10+, Java/javac 21+
and the pinned parser on Linux. Follow the record contract for workspace cache
setup; when execution is unavailable, report checks as not run.

Apply [selected terminology and controlled English](../check-engineering-language/SKILL.md)
while drafting; preserve quotations and literals. The normal native `check`
applies a sibling `.english.json` profile when supplied. This is selected rule
coverage, not complete STE compliance. For multi-output work or difficult check
failures, use [planning and review](../develop-system-concept/references/work-review.md).

Return a concise architecture view with its model revision, material assumptions,
unresolved correspondences and decisions needed. Use [technical document guidance](../../docs/technical-documents.md)
for documents and [diagram generation](../generate-engineering-diagrams/SKILL.md)
for requested visuals. Keep detailed reports in linked evidence. Route missing
verification or intended-use evidence to [evidence planning](../plan-engineering-evidence/SKILL.md).
State the actual checked scope: parsing, declared coverage, finite execution,
physical feasibility and engineer acceptance are separate claims. Unsupported,
incomplete, errored or unrun required checks cannot establish success.

For presentation of selected parts, ports, connections and boundaries, see the [engineering component library](../../docs/component-library.md). Its per-ID modeling contexts support explicit architecture bindings; selecting a drawing does not declare ownership, direction, multiplicity or compatibility.
