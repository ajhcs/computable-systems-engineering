# Allocation

Use this method when relating work to its realizing means. Start with existing
function, resource/part and scenario IDs. Keep the performer, supporting resource
and accountable party distinct; shared work can be intentional.

For the selected functions and resources, retain each allocation's rationale and
operational conditions. Elicit cardinality only where the project needs a rule:
for example, one performer, several collaborators, or an unused reserve resource
may each be appropriate. Inspect unallocated functions and resources with no
assigned work as findings to investigate. Do not automatically remove a reserve
component, force a single performer, or treat allocation presence as competence,
availability, capacity or organizational consent.

Reuse the existing `foundation-1.0` allocation contract where its explicit
function/resource sets, pairs and per-element minimum/maximum bounds answer the
question. The maintained synthetic example is
`examples/foundation/profile.json` paired with `cse-self-model.sysml`; the shared
library entrypoint is `verifier.foundation.inspect(profile_path, model_path)`
from the runtime root. This is a library API, not a `cse.py foundation` command.
Its existing native binding and declared bounds supply a structural verdict;
they do not interpret arbitrary allocation prose.

For finite function contracts, use the [function/flow check](functional.md).
It already supports several performers and project-selected accountability
policies (`exactly_one`, `at_least_one`, `not_selected`). Actor IDs are required
by that finite contract; a physical resource does not silently become an actor.
For human work use [human-task review](../../../docs/human-task-review.md), and
for independent organizations use [ownership review](../../../docs/ownership-review.md)
only when those facts affect the decision. Retain the selected project scope;
ordinary architecture discussion does not need every profile.

Method basis: Buede and Miller, *The Engineering Design of Systems: Models and
Methods*, fourth edition, Chapter 9, p. 243. CSE adapts allocation coverage to
explicit project policies; the textbook's single-component allocation example
does not become a universal restriction on shared work.
