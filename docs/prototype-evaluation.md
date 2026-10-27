# Local prototype verification

Use this optional workflow when an engineering question needs evidence from an
executable local prototype. Preserve the authoritative concept and the selected
verification obligations. A verification harness may be a separate, explicitly
mapped analysis supplement; it does not silently translate narrative SysML
actions into executable behavior.

Start with the system of interest, purpose, selected requirements and method.
Identify the implementation, observation boundary, inputs/conditions, expected
results and unresolved conditions before execution. Capture transactions from
the application, then derive monitor observations from committed state and
returned output. The reference capture retains payload-presence facts rather than
record content, so its own trace does not become an undeclared content-bearing
copy. Keep authored fixtures, prototype observations and operational
evidence distinct. The [terminology and standards basis](engineering-terminology.md)
defines the claim boundaries used here.

## Executed reference example

The optional SQLite application uses only Python's standard library. It handles
dummy count discrepancies, authorized adjustment, reservation/issue bounds,
idempotent requests, record-class access, session-epoch revocation, holds and
logical disposition of declared SQL copy rows. Its separate observer derives
signals from captured SQL state, grants and returned payloads without reusing the
application's permission-decision helper.

```text
python3 skills/develop-system-concept/scripts/cse.py prototype-demo --output work/prototype-run-001
```

The output directory must be new. It contains the dummy database, committed
transaction log, observations, frozen implementation/observer/driver sources,
run record, invocation and CSE review. No network service, account, external
backup or user record is touched. The application is an example system under
test, not a new CSE verdict engine or a required architecture for other projects.

The reference driver executes 26 business transactions. Schema/fixture/session
setup is outside its declared capture boundary. Its dummy policy uses logical
eligibility ticks, not an adopted retention period or real-world authority.
The default manifest adds read/issue authorization checks to the earlier nine
stock/revocation/hold/disposition obligations; the separate original manifest
remains available. Fault injection is explicit and restricted to named reference
test defects; every fault run uses a new dummy database.

## Review captured evidence

Use any drafting skill's `prototype-review` route. Supply model files, a separate
manifest and retained byte digest, observations, run record and explicit artifact
paths. No path or executable command is opened from model text.

```text
python3 skills/develop-system-concept/scripts/cse.py prototype-review MODEL.sysml --manifest MANIFEST.json --manifest-sha256 RETAINED_DIGEST --evidence OBSERVATIONS.json --run-record RUN.json --artifact IMPLEMENTATION=IMPLEMENTATION.py --artifact OBSERVER=OBSERVER.py --artifact DRIVER=DRIVER.py --artifact TRANSACTIONS=CAPTURE.jsonl --artifact OBSERVATIONS=OBSERVATIONS.json --json
```

`prototype-evaluation-1.0` has these fields:

| Field | Meaning |
|---|---|
| `system_of_interest`, `purpose` | Object and question of the selected verification. |
| `verification_method` | `sampled_trace_analysis`. |
| `evidence_origin` | `executed_local_prototype`; an authored trace does not satisfy this operation. This declaration is not authenticated by the local tool. |
| `observation_mode` | `transaction_sequence`; inputs represent decision state, outputs committed/returned results. Index is not physical sample time. |
| `adapter` | `repair_reuse_sqlite_v3` recomputes from captured SQL states; `recorded_boolean_signals_v1` checks recorded signals only and declares that narrower correspondence. Other adapters are unsupported. |
| `signal_definitions` | Native-bound signal → `{meaning,phase}`; phase is decision_state/committed_state/returned_output. |
| `artifacts` | Explicit ID → `{role,sha256}`. Required roles: implementation, observer, driver, execution_log, monitor_input. Optional data_store. Paths come only from CLI arguments. |
| `run` | ID, timezone-qualified start/end, exit code, transaction count and capture boundary. |
| `selected_obligations` | Exact requirement-plus-constraint IDs retained in the independent manifest. |
| `unresolved` | `{id,description,scope}` entries; `blocks_selected_scope` prevents success; `outside_selected_scope` remains a reported limit. |
| `claim_limits` | What the evidence and method cannot establish. |
| `standards_basis` | Selected dated references/application, with conformity assessment explicitly `not_performed`. This is not an ISO conformity checker. |

Models/artifacts are bounded regular files; duplicate/nonfinite JSON and unknown
record fields are refused. The native checker binds observations to model bytes
and supplies the behavior verdict. The wrapper also checks artifact/scope hashes,
complete transaction sequence/count and observation correspondence. Missing data,
execution failure, source drift, a blocking unresolved condition or unsupported
analysis cannot produce a successful required review. A changed observer is not
silently used to reinterpret an old SQL capture.

Transaction-index projection admits only the existing row-local `always` clauses.
It refuses within/until/event timing claims, even if a supplied monitor result
would otherwise pass. The native grammar remains unchanged. This avoids treating
transaction order as a one-second execution schedule.

## Interpretation and remaining work

A pass verifies selected prototype observations under the declared fixture and
method. It does not validate stakeholder use or authenticate decisions/observations.
The reference implementation exercises logical SQL content removal, declared copy
accounting and a tombstone restore guard; physical-media erasure, external copies,
distributed sessions/caches, production authentication, per-work-order reservation
ownership and full backup/recovery remain outside this increment.

Keep prototype results with their source/method revisions and counterexamples.
Keep actual project retention, authority, suitability, performance and acceptance
unknown where evidence is missing. Existing operational/participant evaluation
plans are not automatically completed by these prototype transactions. Generic
discussion and ordinary concept drafting do not require this execution record.

## Capture admission and revision boundary

The current application is 1.2 and its registered SQL observer is
`repair_reuse_sqlite_v3`. Every transaction explicitly captures the Boolean
`returned_payload_present`, including false for non-content results. The observer
requires complete event/snapshot/result fields, integer stock counts, SQLite 0/1
flags, Boolean presence facts, bounded typed ledger rows and consistent target/
transaction identities. A served read needs true returned presence; missing,
wrong-type or contradictory fields are errors before native monitoring, never
inferred false. Committed stock/disposition outcomes need their corresponding
captured movement/content-transition facts. Missing required audit/copy receipts
remain actual monitor findings rather than schema assumptions of success.

Run identity, boundary, signal meaning, unresolved-condition text and standards
references/applications must be bounded nonempty strings; artifact digests must
be lowercase SHA-256 values. Type admission does not verify that a statement is
true, adequate or approved. Same-user fabrication/authentication remains outside
this local boundary.

Earlier v1/v2 observer captures are historical and unsupported by this registered
adapter. Do not relabel old sources, edit old observation hashes or silently
reinterpret an incomplete trace. Execute a fresh dummy run with the new observer
when current executed-prototype evidence is needed. The separate recorded-Boolean
adapter remains explicitly narrower and does not acquire SQL correspondence.

Audit evidence must match the selected operation action, target and actor in its transaction. Foreign audit rows do not satisfy the audit signal; they remain a monitor failure when the selected operation lacks its audit. Movement/policy/tombstone references and event/decision actor identity must agree with their captured targets. These are bounded reference-adapter correspondence checks, not authenticated real-world authority.
