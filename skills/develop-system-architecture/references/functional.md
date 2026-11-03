# Functional architecture

Use this method when the question concerns what the system does or whether its
decomposition supports selected operational situations.

Start with the relevant outcome, boundary and scenarios. Describe each function's
transformation, inputs, outputs and conditions without choosing an implementation
prematurely. Retain source and sink functions when appropriate. Decompose only
until the current question can be answered; show how child inputs and outputs
relate to the parent's boundary.

Walk one selected scenario at a time. For each step, identify its function,
required input and producer or external source, output and intended recipient,
enabling condition and performer. Record the exact step/function IDs where work
is missing, duplicated or inconsistent. Repeated calls to one function can be
valid; apparent overlap needs its operational condition before deletion. Return
an uncovered function to its need or lifecycle/support situation: it may be
unnecessary, or the selected scenario set may omit its purpose. This walk is a
review argument, not execution evidence.

For authored finite semantics, read the existing [function/flow contract](../../../docs/function-flow-review.md)
and use its `function-flow-1.0` record and selected limits. From any directory,
after resolving `LAUNCHER` and `RECORD` to absolute paths:

```bash
python3 "$LAUNCHER" analyze functional-graph "$RECORD"
```

`LAUNCHER` is this skill's sibling
`../develop-system-concept/scripts/cse.py`. A runnable synthetic `RECORD` is
`examples/function-flow/library-return.json` under the runtime root. Add both
`--native-model MODEL.sysml --native-bindings BINDINGS.json` only for an explicit
[native correspondence](../../../docs/function-native-binding.md); its current
type slice is direct Boolean attributes, with guards/effects still authored
separately. The synthetic `examples/function-native/handoff-*` bundle exercises
that route.

Port/type/unit, step binding, selected responsibility and decomposition checks
do not establish transformation correctness, physical conservation or behavioral
equivalence between parent and children. Finite data availability is monotonic;
reading a datum does not consume a token. Return limits and counterexamples with
the affected native IDs; do not reinterpret topology as scheduling or execution.

Method basis: Buede and Miller, *The Engineering Design of Systems: Models and
Methods*, fourth edition, Chapter 7, especially pp. 180 and 193. This is an
original bounded adaptation of scenario/decomposition review.
