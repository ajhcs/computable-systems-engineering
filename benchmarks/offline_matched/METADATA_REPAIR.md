# OM-F1: enforce the whole visible packet

The independent review placed offline preparation commit
`3fe4dd75767510436b6bd23e5716c451b963a333` on HOLD. Its equal-information gate
normalized fact records but discarded container IDs and empty containers, so an
evaluator could add answer hints to delivered metadata while retaining the same
normalized hash. All six tasks reproduced for a replaced ID and an added empty
container. Clean shipped packets and reported protocol totals were correct.

This successor changes only the offline harness, focused tests and its evidence
documentation. It does not modify the accepted lifecycle accountant, plugin
semantics, native implementation, original pilots or held review artifacts.
Independent retest of this repair remains pending.

## Enforced packet contract

For each trusted source snapshot, task and declared arm:

- Only the existing top-level fields are admitted. The entire visible JSON value
  must match the packet generated for that task/arm, including every fact field,
  source revision, authority statement, evidence limit and representation field.
- Query replay and deduplicated artifact have exactly one container with ID
  `"0"`. Duplicated artifact has exactly two with IDs `"0"`, `"1"`. IDs are
  mechanical strings, not labels; Unicode/numeric aliases or attached text fail.
- Every container has exactly `id` and `records`, and a nonempty record list.
  Record order, split point, the identity and position of the single repeated
  fact, and all multiplicities follow the existing response layout. Missing,
  added, moved, reordered or repeated containers/records cannot encode guidance.
- JSON object-key order is canonicalized. It is not an actor-visible channel in
  the emitted bytes. Reversing dictionary insertion order remains a valid input
  and returns exactly the original canonical bytes. Unsupported metadata fails
  with a regeneration instruction rather than being silently ignored.

`checked_packet_bytes` serializes once to immutable UTF-8 bytes, compares the whole
canonical payload to the allowed task/arm representation, and returns those same
bytes. `equal_information` validates all three representations before comparing
normalized evidence and includes a separate `checked_packet_sha256` per arm.

`scripted_calls` now requires the trusted `reference` and `task` keyword arguments
and rechecks at serialization. Both its request arm and successful result come
from that checked snapshot. Mutating an earlier accepted packet cannot inject
unchecked data into a later call. `prepare.py` writes checked packet bytes and
requires the successful result hash to match the comparison receipt. The hash is
an integrity binding for this offline preparation, not an authentication boundary.

The low-level `information` helper rejects malformed shapes, IDs, cardinality and
empty record lists; exact task-specific grouping/order is enforced by
`checked_packet_bytes`. It is not a substitute for the complete validation gate.

## Bounded evidence

The unchanged independent 135-probe driver yields 123 passes and the same twelve
failures on the held pin, then 135 passes and zero failures on this successor's
tested source. Its Q04 reproduction leaks the hint before the repair and stops
with a validation error after it. The driver's hardcoded historical commit label
is preserved; replay receipts bind the actual source root and hashes.

The focused suite has 34 passing tests (the prior 24 plus ten new tests with
negative cases across all six tasks and all three arms). Cases include hints in
IDs, empty containers, unsupported metadata/types, fixed cardinality, unchanged
fact sets with different grouping/order/multiplicity, mutation after checking,
immutable serialized results and exact comparison-to-delivery hashes. Positive
controls preserve all valid arm layouts and arbitrary JSON object-key order.

All 36 protocol conditions were recounted from raw calls including errors and
retries. The 76 preparation-file names are unchanged; only the report and its
manifest change, to record complete packet hashes. All 74 remaining outputs,
including 18 packets, 36 call traces and both patch candidates, are byte-identical.
The source/fixture/bootstrap and the cost definition have not changed.

| Representation, six tasks | Clean UTF-8 bytes | Clean regex units | With retry bytes | With retry regex units |
|---|---:|---:|---:|---:|
| Query replay | 18,585 | 4,523 | 19,497 | 4,817 |
| Deduplicated artifact | 18,585 | 4,523 | 19,497 | 4,817 |
| Duplicated artifacts | 22,092 | 5,403 | 22,998 | 5,697 |

The estimator remains regex-wordpunct-v2, not provider tokenization. Query replay
has no demonstrated advantage over the deduplicated control. There are zero new
model runs, human trials or native acceptances; full model context, provider usage
and billed cost remain unavailable. These owner-run replays are not a new
independent GO or evidence of agentic task success.

Before real runs, the original ten-capability gate still requires a frozen native
API/core contract, independent semantic and state-transition oracles, fresh
licensed held-out tasks, an actor-visible common output schema and blinded rubric,
enforced evaluator/actor isolation, assigned human reviewers and a parent decision
on bounded Standard scope/budget. The manifest alone does not enforce isolation,
and EV remains exposed calibration data. No paid run is part of this repair.
