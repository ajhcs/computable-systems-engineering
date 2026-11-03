# Interfaces

Use this method for a boundary or internal exchange. Retain exact endpoint IDs,
the exchanged item, source and destination, direction, type/unit, operational
conditions and source requirement. An interface can be unresolved without
inventing a protocol or threshold.

Distinguish the connection from its obligations. For a selected exchange, ask
which properties matter: compatibility, timing, integrity, loss/duplication,
fault reporting or recovery. Derive each proposed obligation from the applicable
need/system requirement or label its assumption. Define what delivery or recovery
would mean and under what conditions it is required. Eventual delivery,
conservation and universal fault recovery are not default interface rules.
Link a quantitative observation to its [measure definition](../../define-engineering-measures/SKILL.md)
when the question needs one; keep measure IDs and definition revisions shared.

Choose the check that covers the actual question:

- [Configuration 1.1](../../../docs/configuration-review.md) checks selected
  ordinary native endpoint adjacency; it does not check flow direction or payload.
- [Function/flow contracts](../../../docs/function-flow-review.md) check declared
  directed ports, data identity and exact type/unit agreement for their finite
  profile, with no inferred unit conversion or physical connection.
- [Behavior correspondence](../../../docs/behavior-review.md) selects existing
  sampled, correlated-event or explicitly authored finite checks. Required
  completeness, observation boundary, conditions and limits stay visible.

Do not bridge these claims merely because labels match. Bind supported finite
checks to native sources only through the existing explicit correspondence
contract; unsupported units/events/ports in that adapter remain unresolved.
For observational or physical evidence, use [evidence planning](../../plan-engineering-evidence/SKILL.md)
and keep its target IDs tied to this model revision. A passing local check cannot
authenticate an agreement, prove operating delivery or establish physical fit.

Method basis: Buede and Miller, *The Engineering Design of Systems: Models and
Methods*, fourth edition, Chapter 10, p. 266. This adaptation preserves source
requirements and makes proposed exchange properties conditional.
