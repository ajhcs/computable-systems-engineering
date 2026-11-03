# Goals, obligations and increments

Read this when the operating concept is evolving or a decision needs a durable
explanation. Select a working approach for the current question; a project may
use both approaches at different levels.

For goal-seeking work, begin with the desired stakeholder outcome and competing
explanations of the problem. Use an operational scenario, observation or modest
prototype to find what changes the outcome. Retain uncertainty, evidence and the
reason to revise a proposed means. Goals can guide exploration without invented
mandatory thresholds.

For requirements-driven work, retain the specified obligations, applicability
and sources. Connect them to the relevant scenarios, responsibilities and
evaluation method. Investigate missing or conflicting obligations explicitly.
Conformance to those requirements remains separate from evidence that the
requirements and concept serve the intended use. Route an evidence question to
[plan-engineering-evidence](../../plan-engineering-evidence/SKILL.md).

For an increment, state what useful capability or uncertainty it addresses,
which dependencies and prior decisions it retains, and what evidence will inform
the next decision. Review intermediate requirements, interfaces and prototypes
before the full implementation exists. Apply the relevant existing checks after
each change; an increment's local pass does not establish full-system readiness.
Carry unresolved interactions and deferred work forward rather than calling
the increment a complete CONOPS. Keep unrelated held work outside its scope.

Record rationale when the choice has consequential alternatives or depends on
uncertain context. In the existing workflow decision's `text`, `basis` and
`affects`, retain the choice and status, affected IDs, reason, known evidence at
the decision revision, material unknowns, and a trigger for reconsideration.
Link supporting artifacts/revisions instead of copying them or creating a second
decision log. Do not add unsupported schema fields. An ordinary edit resolved by
a settled rule needs no elaborate rationale. A later outcome does not establish
that the earlier decision was unreasonable with the information then available.

When a change crosses model dependencies, use
[bounded change review](../../../docs/engineering-change-review.md). Preserve the
engineer's authority over accepted intent and consequential changes.

Original project synthesis informed by Buede and Miller, *The Engineering Design
of Systems: Models and Methods*, 4th edition, Chapters 9 and 13. This is method
guidance, not an automated development strategy or decision-authentication system.
