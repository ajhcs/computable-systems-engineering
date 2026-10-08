# CSE interface review corrections — 2026-10-08

The successor fixes the three findings in the independent HOLD on implementation
`2e3525cd5042e793d44d2f4bdf9be76dfc4b0895`. Acceptance remains on HOLD until an
independent reviewer checks this final version. Passing the supplied probes is
implementation evidence, not a new independent approval or an agentic success claim.

The isolated branch is `work/cse-interface-reviewfix-20261008`, based on frozen
evidence commit `0a4f5dfab7e828e18cc2e0e7b959a576ae3287e8`. Its worktree is
`/workspace/worktrees/builderbob/computable-systems-engineering/cse-interface-reviewfix-20261008`.
The original branch, pilot logs, reports and public inputs remain unchanged.
Canonical, accepted/submitted, Alex-held, semantic-migration and native-packaging
worktrees were not edited. No integration, publication, deployment or new model
batch was performed.

| Finding | Correction | Evidence |
|---|---|---|
| F1: admitted ledger strands answer and cancellation | Separate 1,000,000-byte request and 16 MiB ledger limits. Check canonical serialized state under the existing lock before admission, reserving 64 KiB plus overhead for a typed answer. Keep every admitted record. Capacity rejection is atomic. Cancellation/decline does not require reading changed or deleted sources; acceptance still requires the matching source revision. | Exact old pending ledger replay: the same 169-byte answer and 155-byte cancel now both exit 0, with `applied: false`. Boundary, accumulated-size, 128-record, stale-source and concurrent-resolution regressions pass. |
| F2: discarded malformed lines can score pass | Reject malformed/unknown events, duplicate fields/completions, invalid usage and unfinished lifecycles. Expose invalid/incomplete transcript state, withhold complete usage, and require a complete valid log before a pass. The comparison recomputes accounting from logs and rejects invalid transcripts. | Exact two-line independent fixture changes from `pass` to `incomplete`, `transcript_status: invalid`, and no aggregate usage. Malformed/truncated/Unicode/lifecycle and comparison regressions pass. |
| F3: unavailable edit arguments measured as zero | Missing input is `null` with explicit unavailable scope. Report known logged-command subtotals and unknown counts; all-tool input totals are `null` when any input is unavailable. No fabricated arguments or empty-string hash. | Original optimized events `item_13` and `item_16` are unknown. Both tool counts remain 15 and provider usage is unchanged. |

The ledger limits are executable admission constraints, disclosed on demand by
`elicit-help`; they do not add skill-entry instructions or grant host permission.
The helper output increases from 1,049 to 1,150 UTF-8 bytes and from 421 to 445
**regex-wordpunct-v2** estimates. This estimator counts Unicode word runs and
individual nonspace punctuation on exact output text; it is not a model tokenizer
or a billing measure. Original initial-entry measurements remain historical
evidence for the unchanged entry files.

## Final deterministic checks

`python3 -B scripts/check.py --require-sysml` completed with exit 0:
**221 tests, 15 suites, no skips**, including all 30 interface tests and 17
accounting/comparison tests. Test sources remained unchanged through the run.
The shared helper checks and existing parser/verifier suites passed.
The supplied independent targeted driver also passed **64 invariants** when
re-executed against the final code. No provider was called by these checks.

The original independent size driver was first replayed against the frozen old
product, changing only its disposable output directory. It reproduced the
stranded ledger. The exact resulting pending ledger and its exact saved answer
and cancel requests were then replayed on separate successor copies. Request
hashes, original driver hashes, results, final suite source pins and preservation
checks are in [review-fix evidence](../benchmarks/interface/review-fix-evidence.json).
Raw reproduction requests and logs are retained in the separate review handoff.

## Corrected pilot accounting

[Corrected accounting](interface-pilot-accounting-corrected.json) supersedes the
per-tool zero-input entries in the preserved historical
[pilot report](interface-pilot-results.json). It reads the original events and
does not rewrite the trial files or historical reports.

| Measure from the original pair | Baseline | Optimized |
|---|---:|---:|
| Reported aggregate input, including cached input | 610,749 | 560,012 |
| Reported cached input | 539,392 | 499,456 |
| Derived input minus cached input | 71,357 | 60,556 |
| Reported output | 6,709 | 6,677 |
| Completed tools | 15 | 15 |
| Known logged-command input estimates | 15 | 13 |
| Unknown tool inputs | 0 | 2 |
| Known command text: UTF-8 bytes / regex estimate | 21,029 / 5,480 | 6,384 / 2,274 |
| Total tool-argument or billed cost | Unknown | Unknown |
| Broad completion/engineering fidelity | Unreviewed | Unreviewed |

The unequal-coverage command subtotals do not establish whole tool-input savings.
Provider aggregates are independently reported and unaffected by missing edit
arguments. The previously supported observation remains one baseline-first pair
with 8.307% lower reported aggregate input and 15.137% lower derived input minus
cached input. It does not establish billed savings, causation or reliability.
The requested configuration was the existing Standard/default infrastructure;
no new model runs, credentials, subscriptions or provisioning were used here.

The prior independent review classified zero blocking domain questions, zero
needless questions and zero provider confirmation events in both preserved
transcripts. The required prospective migration question was not a blocking
request. Machine counters remain unknown until an attributed classification is
supplied; the accounting code does not infer zero from missing information.

## Final-version review handoff

Review the frozen successor commit named in the accompanying handoff, not the
old implementation alone. Re-run the complete suite with the existing pinned
runtime, inspect the admission reserve and lifecycle races, and repeat the exact
old-ledger and malformed-log fixtures. Confirm missing edit arguments stay
unknown and the corrected report still matches the preserved event hashes.
The implementation author has not lifted the independent HOLD.

The original limitations still apply: the desktop slash menu and native
elicitation transport are untested, NASA numerical execution/migration lacks an
authorized native runtime and accepted cases/outputs/tolerances, and broad
engineering fidelity is unreviewed. No additional model batch is needed to review
these three fixes. There is no outstanding permission rejection for this work.
