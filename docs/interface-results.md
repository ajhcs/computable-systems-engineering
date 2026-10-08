# CSE interface implementation and measured pilot — 2026-10-08

Product implementation is frozen at `2e3525cd5042e793d44d2f4bdf9be76dfc4b0895`,
based on `b01ef01698450e5a47cc20f957fe93a09e9744b4`. Subsequent commits contain
benchmark infrastructure and evidence only. Branch:
`work/cse-interface-context-20261008`; worktree:
`/workspace/worktrees/builderbob/computable-systems-engineering/cse-interface-context-20261008`.
The canonical main checkout remains at the baseline with its unrelated work
preserved. No publication, deployment, semantic migration or native packaging
was performed. No private Codex session store was read.

## What changed

- Added a short `cse` discovery skill while preserving the three independent
  drafting skill names and natural-language entry points. The manifest and
  repository skill links expose the same installed runtime.
- Moved detailed methods into on-demand workflow references. `discover` lists
  operations; `describe` returns one strict typed schema. The local JSON adapter
  dispatches the existing parser/checker without changing its semantics.
- Added explicit format/file/type errors and review-input invariants. Compact
  responses preserve status, scope, digest, findings and coverage and identify
  omitted evidence; full results remain available with `--detail`.
- Added persistent domain-question validation: known/unrelated/read-only needs
  are suppressed; explicit typed answers are revision-bound; cancellation,
  decline, replay and stale replies cannot apply a value. It never edits the
  model or grants acceptance or provider permissions. Native provider/UI
  elicitation transport is not newly implemented or claimed.

The applicable skill methods and record contracts were read before changes.
Required constraints remain available and executable invariants replace repeated
instructions where possible. Deep engineering work may still need the detailed
method and SysML guidance; those costs are not presumed eliminated.

## Deterministic evidence

The full `python3 scripts/check.py --require-sysml` run passed all 15 suites with
the pinned parser required (195 cases at that run). Subsequent focused checks
passed the final 19 interface cases and all 5 benchmark-accounting cases, bringing
the covered final suite total to 198. The changes after the full run were finite
number validation and benchmark accounting; their relevant focused checks passed.
`git diff --check` passed. No runtime dependency was added.

Lifecycle coverage includes valid typed answers, invalid types/choices and
nonfinite numbers, missing explicit answers, cancellation/decline, changed source
and known facts, duplicate/reworded questions, stale IDs, persisted replay,
unrelated/known/read-only questions, foreign ledger protection and separation of
domain answers from permission fields. Runtime checks cover independent launchers,
format admission, review scope/evidence, and preserved parser verdicts.

The estimator is **regex-wordpunct-v2**: Unicode word runs plus individual
nonspace punctuation, applied to exact UTF-8 text without JSON wrapping. These
are reproducible estimates, not model tokenizer or billing counts. Exact byte
counts and each schema/guide cost are in [context results](interface-context-results.json).

| Controlled payload | Baseline estimate | Optimized estimate | Change |
|---|---:|---:|---:|
| Initial skill metadata catalog | 127 | 107 | −15.7% |
| System-concept entry | 1,165 | 431 | −63.0% |
| CONOPS entry | 1,025 | 426 | −58.4% |
| Scenario entry | 1,063 | 437 | −58.9% |
| Actual same-input syntax response | 986 | 310 | −68.6% |
| Plugin manifest | 332 | 342 | +3.0% |

The added generic entry costs 232 estimated tokens, discovery 109, and the
selected operation schema 168–245 with installation prefixes normalized for the
static schema comparison. The actual syntax response comparison uses identical
checker inputs and preserves verdict/scope/digest/coverage/findings; its inventory
is omitted explicitly. Static cold-load scenarios include their named guide
costs; they are not claims about what every agent actually loads.

## Actual Standard model pilot

Existing BuilderBob `codex-cli 0.162.0` reported a ChatGPT login. A fresh ephemeral
access probe succeeded with `gpt-6.1-sol`, medium effort and explicit
`service_tier=default` (Standard), without new credentials or provisioning. The
first probe hung waiting for inherited stdin and timed out before a model turn;
closing stdin fixed the invocation. Its record is retained. The successful
five-output-token probe reported **17,471 input tokens**, illustrating host
overhead outside the controlled repository payloads.

One matched pilot per condition ran in isolated snapshots of the exact baseline
and candidate commits. Task text, source/license hashes, requested model/effort/
tier, CLI, parser hash, workspace-write sandbox and 600-second limits match.
Both used ephemeral sessions, disabled web search and noninteractive approval
policy `never`; denied actions would fail, not gain permission. Response routing
is not exposed by CLI events, so the records establish the requested Standard
configuration, not independent provider-side routing attestation.

The licensed inputs were pinned **after freezing the product code**:

- [Official EVSample](https://github.com/Systems-Modeling/SysML-v2-Release/blob/fb97b754f29588b8e9c7a35f370880cd15eb29e7/sysml/src/examples/State%20Space%20Representation%20Examples/EVSample.sysml), EPL-2.0, 11,002 bytes. This is an official example, not an independently proven industrial system.
- [NASA T-MATS JT9D dynamic model](https://github.com/nasa/T-MATS/blob/ad6e4d5d0d76c229db4eb72ca40ef58d5ddc4014/Trunk/TMATS_Examples/Example_JT9D/JT9D_Model_Dyn.mdl), Apache-2.0, 172,639 bytes. It is a genuine Simulink model, not SysML v2.
- [TMT model](https://github.com/Open-MBEE/TMT-SysML-Model/tree/b2a33b71c65678498b538195dcb947a7962ca75b), Apache-2.0, 27,193,371 bytes, pinned and **reserved without a model trial**. Its native archive is SysML v1/MagicDraw.

Source, license and README SHA-256s are in the [corpus lock](../benchmarks/interface/corpus-lock.json).
Held-out means excluded from interface development, not guaranteed absent from
pretraining. Public data remained separate from coursework/private tests.

| Actual pilot measure | Baseline | Optimized |
|---|---:|---:|
| Reported input tokens, including cached input | 610,749 | 560,012 |
| Reported cached input tokens | 539,392 | 499,456 |
| Input minus cached input | 71,357 | 60,556 |
| Reported output tokens | 6,709 | 6,677 |
| Reported reasoning output tokens | 548 | 280 |
| Completed tool calls | 15 | 15 |
| Elapsed seconds | 202.037 | 165.965 |
| Exact authorized capacity edit | Pass | Pass |
| Independent parser rerun | Pass | Pass |
| Source inputs / frozen runtime unchanged | Yes / yes | Yes / yes |
| Full engineering fidelity review | Pending | Pending |

Observed total input was 8.3% lower; input minus cached input was 15.1% lower.
These are provider-reported run totals, distinct from the static estimates.
One baseline-first pair cannot establish a reliable saving or isolate causes
from stochastic behavior, cache warming or latency variation. The optimized
agent chose `--detail` for retained diagnostics; the pilot therefore does not
demonstrate universal use of the smallest default response. Per-tool logged
input/result payload estimates and evidence hashes are in
[pilot results](interface-pilot-results.json); they do not reconstruct hidden
provider prompt overhead.

## What the actual agents did, and what remains unproved

Both agents produced a byte-exact copy changing only battery capacity from 50 to
60 A⋅h. An external oracle compared the bytes and reran the unchanged checker.
Both preserved all source inputs, identified EV parts and declarations, diagnosed
the missing controlled-profile clock without inventing one, recovered from the
deliberately wrong path, and produced source-cited NASA component descriptions
with proposed decompositions labeled as inferences. Both identified an existing
EV discrepancy between prose and a numeric mass assumption without changing it.
These are actual model-in-the-loop artifacts, not scripted repair success.

The baseline sent MDL to the SysML parser and received 196 syntax diagnostics.
The optimized adapter rejected the format before parsing with an actionable
recovery message. The optimized agent also tried a qualified battery part ID;
the existing inspect surface supports short IDs for concerns/use cases/requirements,
so that request failed and it recovered using source reading and a supported
requirement ID. Better target-kind discovery is a concrete review follow-up;
the held-out result was not hidden or tuned away.

Transcript audit by the implementation author found no blocking domain requests,
needless requests, or provider confirmation events in either run. Baseline's
structured `domain_questions` list is empty. Optimized's list contains one
**prospective migration-scope decision explicitly requested by task 6**; it did
not block the task or request an answer to the specified edit. Treating that list
length as needless elicitation would be incorrect. Independent classification
is pending, so the machine counters intentionally remain null.

The scorer marks both broad outcomes **unreviewed**, despite their own success
summaries. The byte edit and parser checks have genuine narrow oracles. NASA
engineering decomposition and semantic fidelity still require independent
engineering review. No thermodynamic simulation, observed real-system behavior,
lossless migration, acceptance or full reliability claim is established. No
numerical baseline or native runtime was fabricated or installed.

## Access and handoff

The local sandbox runner failed during startup (`setup refresh had errors`).
Approved host execution through the existing Lenovo→BuilderBob SSH connection
worked. No automatic approval rejection or outstanding permission blocker
occurred. Saved native Codex session stores were not inspected; only new explicit
ephemeral trial output files were read.

For the next numerical/migration milestone, the missing decisions are an existing
licensed MATLAB/Simulink/T-MATS execution environment, an intended target/fidelity
scope, and accepted baseline outputs, operating cases and comparison tolerances.
TMT similarly needs its compatible native toolchain and oracle. This task does
not authorize purchasing/installing proprietary runtimes or issuing credentials.

See the [independent-review request](../benchmarks/interface/independent-review-request.md)
for exact checks, reserved-family work and a counterbalanced repeat. The live
desktop slash menu and native elicitation UI transport remain untested; filesystem
discovery, CLI routing and real AI invocation were tested. No independent reviewer
approval is implied by this handoff.
