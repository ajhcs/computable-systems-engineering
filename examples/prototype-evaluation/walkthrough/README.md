# Synthetic failure and recovery examples

These examples use only the repository's public dummy parts, records, roles and
fixture policy. The cases are authored test inputs, not real notices, delegated
decisions, participant observations or private project records. No private notes,
course extracts, project models or captured user transactions are included.

Run the examples from the repository root with the pinned SysML parser available:

```sh
python3 -B tests/test_walkthrough_limits.py
python3 -B tests/test_human_tasks.py
```

The required regression gate includes both suites and refuses a missing or stale
parser rather than silently accepting skipped native checks:

```sh
python3 scripts/check.py --require-sysml
```

Tests create disposable databases under the repository's `.tmp/` directory.
Set `CSE_SYSML_CACHE` consistently when using a separate workspace parser cache.
There is no network service, live stock, real policy, external backup or actual
participant in these cases.

## Cases and current observations

| Example | Scripted situation and actual local operations | What is established |
|---|---|---|
| Stock adjustment after a lost receipt | A dummy actor without adjustment permission is denied. STORES corrects book 5 to fixture physical 4. The test withholds a fictional receipt, reopens the database, reads 4/4 and retries. | Retry returns `already_reconciled`; there is one adjustment and one matching audit. This is committed-state inspection, not physical counting, crash recovery, delivery acknowledgment or authenticated decision enforcement. |
| Two independent notices | The authored case contains notices SYNTHETIC-A and SYNTHETIC-B. Two `hold` calls set the same Boolean. A release intended for A clears it. An adversarial `dispose` probe bypasses the scripted stop for remaining B. | Disposition commits; the existing Boolean-hold requirement passes and does not detect B. Hold IDs and remaining-hold preservation are unsupported. A tombstone denies restore; that denial does not repair the loss. |
| Residual declared copy | Inject `leave_export`, dispose R-DISPOSE, reopen without the fault and retry. | The export remains and retry returns `already_disposed`. The original `R_D_COPIES` violation remains in the monitored history; there is no supported residual-copy repair. |
| Missing adjustment audit | Inject `omit_adjustment_audit`, adjust stock, reopen without the fault and retry. | Retry does not reconstruct the audit. The original `R_D_ADJUST_AUDIT` violation remains. No retrospective witness is fabricated. |
| Missing disposition audit | Inject `omit_disposition_audit`, dispose, reopen without the fault and retry. | SQL copies are gone, but the audit is still missing. `R_D_AUDIT` fails; content removal alone is not sufficient completion evidence. |

The executable examples are in
[test_walkthrough_limits.py](../../../tests/test_walkthrough_limits.py). Each
captures actual `Store.events()` state and applies the existing separate observer
and native checker. These are direct regression tests, not persisted
`prototype-review` run records or protected execution receipts. The existing
[prototype workflow](../../../docs/prototype-evaluation.md) supplies that separate
artifact/capture review when needed.

These tests intentionally characterize limitations. A green test run means the
documented observations were reproduced; it does **not** mean multiple holds or
the missing recovery behavior are supported. A future repair should replace its
characterization and update the documented claim boundary together.

## Do not turn unexercised conditions into a pass

The full, unchanged eleven-obligation manifest remains selected in every example.
Focused stock or hold cases leave some conditions unexercised, so their native
review remains `unknown`. The stock example explicitly checks that the unused
revocation condition has zero triggers. The injected copy/audit violations make
their reviews `fail`, even where other conditions remain unknown.

The multiple-notice case has no monitored Boolean-hold violation. Its overall
`unknown` comes from other unexercised conditions, not detection of notice B.
Review scope and observation meanings must change explicitly before claiming
that a remaining-hold obligation was checked. Do not drop other obligations,
relabel a monitor result or invent extra operations just to report a broad pass.

## Documentary presence is a different check

[test_human_tasks.py](../../../tests/test_human_tasks.py) uses the existing public
service-desk model, not a user project, to demonstrate two further limits:

- A nonempty completion field containing `Done.` can pass documentary coverage.
  Removing the selected field fails. Presence and semantic sufficiency differ.
- An unexecuted plan with method `Run a test.` can pass documentary coverage.
  The plan remains `not_run`; data acquisition, observer, validation and
  acceptance adequacy still require engineering review.

Scripted decisions and receipts remain authored inputs. Local permission bits do
not verify a separate case ID, current evidence version, delegated decision or
receiver acknowledgment. A role assignment, readable procedure or synthetic
walkthrough does not establish competence, real authority, intended-use
validation, stakeholder acceptance or ISO conformity. Keep full project plans
uncompleted when their participant, policy or evaluation evidence is missing.
