# CSE transcript lifecycle correction — 2026-10-08

This isolated successor addresses F2-R1 and F2-R2 from the independent HOLD on
`2695544fb3243b11f8e69d524f8b189d2bfa2bd3`. The previous repair, original pilot,
historical reports and review packages remain preserved. F1 ledger admission and
F3 unknown-input handling are unchanged. Final independent acceptance remains
pending; the implementation author has not lifted either HOLD.

Branch: `work/cse-interface-lifecycle-20261008`. Worktree:
`/workspace/worktrees/builderbob/computable-systems-engineering/cse-interface-lifecycle-20261008`.
Only the benchmark accountant, its tests and new evidence/documentation change.
No skill-entry instructions, native implementation or engineering models change.

## Executable lifecycle contract

Accounting version `cse-accounting-3` validates each event transition, retaining
errors permanently instead of deciding validity from the final open-item set.

| Boundary | Allowed | Rejected or incomplete |
|---|---|---|
| Stream | One optional initial thread header; sequential turns | Repeated/late thread headers, unknown event types |
| Initial turn | Explicit start, or the supported initial form with omitted start | An explicit start after item activity has already opened the turn |
| Next turn | A new explicit `turn.started` after the prior terminal | Extra terminal events or item events after a closed turn |
| Item identity | One type and one turn for each item ID in the stream | Type changes, ID reuse across turns, duplicate or late terminal/update/start events |
| Missing item start | A first completion may stand alone; a first update opens an item | An update that never completes; a later start after the observed update |
| Turn terminal | All observed items have completed | A terminal while an item is open, even if a later record closes it |
| Supplied turn identity | Optional `turn_id` stays bound across turn/item events | Mismatched, malformed or reused explicit turn IDs |
| End of log | A completed, closed turn with no errors/failures | Dangling starts/updates are incomplete; contradictions remain invalid |

Items can omit start events, but observed starts and updates must finish within
their turn. Valid multiple-turn logs remain supported and sum each accepted
turn's usage once. A failure does not disappear when later records succeed.
Invalid/incomplete logs withhold complete provider usage and tool totals; observed
payloads remain diagnostic data. Missing tool arguments remain unknown.

The scorer requires the current accounting version and a complete error-free
lifecycle before considering independent oracles. Stored older `complete` flags
must be recomputed from raw events. This is input validation, not authentication
of same-user metadata or proof of engineering success.

## Reproductions and final checks

The unchanged supplied transcript driver first reproduced all nine failures on
the frozen previous commit. Its duplicate pilot fixture still demonstrated the
old incorrect baseline total of 1,221,498 from a disposable copy. The originals
were never modified.

Against the final successor, all **86 new supplied probes** pass: 30 transcript,
6 comparison and 50 ledger invariants. All **64 prior supplied invariants** also
pass. The ledger driver still uses the real limits and 413 actual CLI calls.
The complete parser-required suite passes **236 tests / 15 suites / no skips**,
including 32 accounting/comparison tests. The supplied network-denial wrapper
verified IPv4/IPv6 socket creation was denied for these checks and descendants;
no separate syscall trace is claimed.

The old assertion for an item after a terminal turn now expects `invalid` rather
than `incomplete`; both are nonpassing, and the new status identifies the explicit
contradiction. No acceptance invariant was weakened. Added cases retain initial
completion-only forms, updated items with omitted starts, valid multiple turns,
error persistence, identity checks and comparison output preservation.

See [bound evidence](../benchmarks/interface/lifecycle-fix-evidence.json) for
source pins, driver hashes, full-suite counts and before/after receipts. The
review handoff retains raw fixtures, logs and both duplicate-pilot outcomes.
Supplied drivers retain their historical embedded commit strings; the enclosing
receipt identifies the actual product root and accountant hash used in each run.

## Preserved pilot and next review

[Lifecycle-validated accounting](interface-pilot-lifecycle-validated.json) is a
new report derived from the original logs. It preserves aggregate input
**610,749 / 560,012**, tool counts **15 / 15**, unknown optimized input IDs
`item_13`/`item_16`, and broad completion **unreviewed / unreviewed**. Only the
accounting-version field differs from the preceding corrected report. Appending
a duplicate terminal to a disposable pilot copy now fails comparison without
writing a report. No fabricated usage replaces the rejected total.

This remains one baseline-first real model pilot, not general engineering
acceptance. No new model batch, API credentials, paid provisioning, source
migration, publication or deployment occurred. Native slash-menu transport and
NASA numerical/migration acceptance remain unproven. Independent retest of the
new frozen pin is still required before lifting the interface HOLD.
