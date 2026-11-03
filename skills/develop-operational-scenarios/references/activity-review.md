# Activity meaning and scenario/function correspondence

Use this review when start conditions, parallel work, data or termination affect
the scenario question. Keep narrative exchanges useful without claiming an
activity interpreter.

For each selected action, distinguish control arrival from object/item arrival.
Identify the owning activity's execution context, incoming control prerequisites,
required inputs and their lower multiplicities, producer/external source, and
guard. An arrow by itself cannot establish that the action is enabled. Record
missing inputs and unresolved conditions at the affected action ID. A performer
partition identifies responsibility context; it does not implement resource
availability or a schedule.

Review branches in their selected operational context. A decision chooses an
outgoing alternative under its guard; a merge combines alternatives without
waiting for all of them. A fork introduces concurrent paths; a join's selected
synchronization condition needs the required arrivals. Do not use a merge as a
join or infer mutual exclusion from two drawn paths. Retain guard coverage and
overlap questions without inventing default choices. Distinguish ending one
flow from ending the whole activity, and record intentional waits, loops,
cancellation and exceptional outcomes before diagnosing a dead end.

Walk the selected scenario through functions: retain step ID, function ID,
enabling condition, inputs/outputs and performer. Locate missing transformations,
unexplained duplicate work, unproduced data and boundary mismatch. Several steps
may intentionally invoke one function. For broader decomposition or allocation
work, use [system-architecture development](../../develop-system-architecture/SKILL.md).

For a computable question, read [function/flow contracts](../../../docs/function-flow-review.md)
and [behavior correspondence](../../../docs/behavior-review.md); invoke the
selected existing command through this skill's `scripts/cse.py`. For example,
using absolute paths from another working directory:

```text
python3 <skill-dir>/scripts/cse.py analyze functional-graph RECORD.json
python3 <skill-dir>/scripts/cse.py finite FINITE.json --scenario ID --review
```

The function record binds every finite step to an explicit function and checks
selected port/guard/performer/decomposition contracts. Bare finite JSON does not
execute native actions; add the [explicit native binding](../../../docs/function-native-binding.md)
only within its supported Boolean correspondence slice. Do not infer the finite
record from narrative order or arrows.

The finite engine has atomic steps and monotonic data availability: `consumes`
requires a datum but does not remove it. It does not implement general consumable
tokens, input-pin multiplicities, concurrent fork/join schedules, native
include/extend composition or arbitrary activity termination. Its selected
completion check establishes that each explored reachable state has some path to
completion, not that every execution eventually completes. Do not convert a
valid wait into a failure or invent fairness. Missing correspondence, exceeded
caps and unsupported selected behavior remain unresolved required checks.

Method basis: Lenny Delligatti, *SysML Distilled*, Chapter 6, pp. 103 and 119;
Buede and Miller, *The Engineering Design of Systems: Models and Methods*, fourth
edition, Chapter 7, pp. 180 and 193. These guide human review; a complete SysML v1
or v2 execution mapping remains outside this implementation.
