# Selecting a bounded behavior check

Use the project's question to select an existing CSE check. Record what a result
can establish before interpreting it. Narrative task entry/completion fields and
scenario walks remain documentary. Parsing a native action, state or transition
does not give it executable CSE semantics. A diagram is a view of that model.

| Question | Existing representation / engine | Evidence and interpretation |
|---|---|---|
| Is selected task/support/ownership information retained? | Native identities plus selected documentary profiles; concept-review. | Supplied sources and separate scope. Coverage, not behavior. |
| Does a sampled response meet an always/within/until clause? | Native subject/attributes and CSE-REQ/2.0; existing language monitor. | Independent obligation manifest, exact clock, model-bound finite observations and completeness. Only observed samples; missing/pending/limits cannot pass a required check. |
| Does each distinct request receive its response by a bound? | Native in/out event occurrences, String correlation identity and CSE-EVENT/2.0; existing event monitor. | Model-bound events, capture horizon/completeness and independent manifest. Distinct IDs stay distinct; the deadline is inclusive. This does not prove reliable storage or physical task completion. |
| Are bounded obligations jointly satisfiable, or can a finite scenario complete? | Explicitly authored version-2 finite contract; existing finite verifier. | Finite properties, typed predicates, atomic steps, declared external changes and analysis caps. Satisfiability is not reactive realizability; a completion path is not progress under every scheduler. No implicit translation from SysML/prose. |
| Is a proposed available configuration adequate under declared rates? | Native-bound cseInquiry, existing conditional inquiry. | Source-bound assumptions, units, demand, capability and shared-resource constraints. A conditional calculation, not observed capacity. |
| Will arbitrary concurrent native SysML behavior execute correctly? | General native state/action execution is unsupported. | Select a supported narrower question or plan a separately scoped extension; do not substitute a successful parse or sampled trace. |

For new SysML work, read [the native profile](sysml-v2-profile.md), including
unsupported forms. Preserve the authoritative model and independent expected
obligations. The [language](requirements-language-v1.md), [event](sysml-v2-profile.md)
and [finite-verifier](verifier-v2.md) contracts define exact engine meanings.
Synthetic evidence demonstrates checker behavior; capture completeness, sensor
meaning, operating conditions and correspondence to reality need actual evidence.

## Worked native mapping

The [return-recording fixture](../examples/behavior-review/concept.sysml) proposes
an item-specific four-minute bound. Its [source brief](../examples/behavior-review/brief.md)
and [separate manifest](../examples/behavior-review/manifest.json) retain the proposed
question and obligation; this example does not introduce a real project threshold.

| Engineering meaning | Explicit native/profile mapping |
|---|---|
| Boundary | ReturnRecording::desk, a ReturnDesk part usage. |
| Start observation | Its input event returnAccepted, with a String correlationId. This is an observation boundary, not an inferred task-activation guard. |
| Completion observation | Its output event conditionRecorded with the same ID. The event name alone does not prove inspection quality or persistence. |
| Proposed obligation | R_RECORD / recordingTime, source SYN-RETURN-1, CSE-EVENT/2.0 within 4 minutes. |
| Reviewed evidence | Model digest, event paths/IDs, exact times, observed_until and complete. Synthetic fixture only. |
| Counterexamples | Late/mismatched/missing item response; one receipt for two returns. |
| Unresolved/refused | Pending capture, no trigger, missing evidence/manifest, stale bytes, budget limit, omitted obligation and unsupported timing/profile. |

Run through any existing drafting launcher, for example:

```text
python3 skills/develop-system-concept/scripts/cse.py check examples/behavior-review/concept.sysml --manifest examples/behavior-review/manifest.json --evidence examples/behavior-review/synthetic-evidence.json --review --json
```

The finite verifier remains independently available for an explicitly authored
finite model; it is not a second automatically maintained concept model or a
claimed general SysML statechart compiler. A future native execution adapter
would need an explicit supported semantic subset, correspondence evidence and
concurrency/control tests before it could support stronger claims.

## Historical method boundary

Harel's 1987 paper identifies hierarchy, concurrency and communication as distinct
statechart extensions. Its author-institution [abstract](https://weizmann.elsevierpure.com/en/publications/statecharts-a-visual-formalism-for-complex-systems/)
was checked; full statechart/SysML execution equivalence is not established here.
Sargent's 1998 engineering-conference [paper](https://www.informs-sim.org/wsc98papers/016.PDF),
pp. 121–123 and 128–129, distinguishes conceptual-model, implementation, data
and operational validity and ties validation to the intended application. CSE
uses those distinctions to bound claims, not to declare a concept validated by
running tests. This increment adds a native worked mapping and controls using
existing engines; it adds no behavior interpreter or task-network simulator.
