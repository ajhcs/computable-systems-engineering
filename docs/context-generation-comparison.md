# Generation comparison under a source budget

On 10 November 2026, a 24-run synthetic study compared four CSE drafting
workflows using two larger engineering models. Independent model reviewers
assessed the actual prose and Python outputs against the retained source
records. Adjudication found **no meaning errors or unsupported claims**, but
**eight missing essential contributions across seven of the 96 output units**.
Seventeen runs retained every essential contribution. All 708 fixed behavior
cases passed separately.

The shared workflow and assembled-context arms each produced six source-complete
runs. The saved-review arm produced four. These are observations from six runs
per arm, with substantial voluntary checking in the other arms. They do not
establish a general reliability gain or isolate the benefit of requiring review.

## What changed

The implementation adds lossless compact transport to the existing assembled
context view, makes the sampled-check input contract discoverable, and strengthens
the shared workflow's treatment of qualitative goals, evidence stages and
omissions. It reuses the existing definitions, identities, native bindings,
relationships and deterministic checkers. It adds no vocabulary file or
automatic natural-language meaning verdict.

The [meaning workflow](meaning-context.md), [sampled-check contract](behavior-review.md#discover-the-sampled-trace-input-contract)
and [adversarial corpus](../examples/meaning-context/README.md) describe these
features. The public corpus contains 40 authored cases, including 11 interpretive
cases whose computed verdict remains `not_run`. The generation study uses two
larger synthetic projects that exercise the same distinctions; its output
assessments are separate from those fixture expectations.

## Study design

Each project has approximately 100 kB of native SysML and 100 kB of terminology
and binding records, plus seven short authoritative source notes. The projects
describe depot release and microgrid restoration mechanisms. They include
superseded definitions, homonyms in other scopes, multiple roles for one native
entity, current-revision acknowledgement, revocable gate dispositions,
qualitative goals, and distinct plan and supplied-assessment records.

Each fresh generation process received a broad task and produced an operating
note, design note, evidence note and Python implementation. It received no list
of the intended traps. The frozen assessment inventory has 17 essential
contributions per run. Three trials per project and arm give six runs per arm,
24 runs, 96 output units and 408 essential-coverage opportunities.

| Arm | Available workflow |
| --- | --- |
| A | Earlier guidance and the legacy element view. |
| B | A plus the revised shared meaning workflow. |
| C | B plus the lossless compact assembled context. |
| D | C plus a required saved draft, source-linked output review, executed checks and final artifact binding. |

All arms used `gpt-6.1-sol` at `max` reasoning effort through Codex 0.167.0,
with at most two generation processes running concurrently and a 1,200-second
limit per run. No sampling seed was set. All 24 processes completed; no final
was malformed or timed out.

The **32,000 UTF-8 bytes per run are a cumulative source transport allowance**.
Initial project context and both scope files are charged, as is each delivered
broker response, including repeated deliveries. Whole responses that exceed
the remaining allowance are refused. Generic instructions and schema helpers,
local history and expansion of already delivered data are outside that
allowance. It is not a native model context-window limit or a total token cap.

Both view routes initially select `UC_RELEASE`. C/D assembled views use
`--limit 1 --compact --max-bytes 19000`. This ceiling applies to the complete
selected assembled report, including its
metadata and newline. It does not mean that every model element was selected.
Known selection omissions and unresolved mappings remain visible, and additional
records are available through the broker. The independently retained checker
scope is not reduced by the view's element or byte limits.

Every arm received the original native obligation manifest and a separately
pinned language-monitor manifest up front. Every original obligation ID was
retained. The unchanged deterministic language monitor evaluates the supplied
observations; the helper does not infer requirements or normalize away errors.

## Assessment and results

Two independent reviewers received randomized, blinded packets containing the
actual final outputs and authoritative sources. They locked their initial
assessments before seeing execution histories. A third reviewer first performed
and locked a cold assessment of all outputs, then reconciled both initial
reviews and the execution evidence. Separate auditors checked actual generation
and review processes, metrics, byte accounting and retained hashes.

The reviewers used these distinctions:

- **M — meaning error:** a claim or behavior contradicts applicable source meaning.
- **U — unsupported claim:** an established claim lacks the required support.
- **O — omission:** a known essential contribution is missing or materially incomplete.

Honest uncertainty about a genuinely unspecified decision is retained separately.
An available source fact left unretrieved can still be omitted. A missing fact
is counted once in its preferred output unit, even when it is absent from
several notes. A source-complete run requires all four units assessed, no M/U/O
flags, and all 17 essential contributions covered or correctly unresolved.

| Arm | Source-complete runs | M / U / O units, out of 24 | Essential contributions retained, out of 102 | Fixed behavior cases passed |
| --- | ---: | ---: | ---: | ---: |
| A | 1/6 | 0 / 0 / 5 | 97 | 177/177 |
| B | 6/6 | 0 / 0 / 0 | 102 | 177/177 |
| C | 6/6 | 0 / 0 / 0 | 102 | 177/177 |
| D | 4/6 | 0 / 0 / 2 | 99 | 177/177 |
| Total | 17/24 | 0 / 0 / 7, out of 96 | 400/408 | 708/708 |

The 400 retained contributions include 24 correctly unresolved mappings, one per
run. There are 376 covered contributions and eight omissions. All five A-arm
omissions retain that a delay goal is qualitative or has no deadline, but omit
its direction: **reduce** depot release delay or feeder restoration delay.
Naming `N_DELAY` alone does not communicate that direction. All B, C and D
outputs retained it.

Two D-arm design notes omit the binding of the selected receiver's resource and
actor roles to the same native entity. One also omits a usable account of the
dispatch and acknowledgement performers. The notes contain partial correct
information; neither successful code tests nor an acknowledgment of missing
source access fills these prose omissions. All 24 outputs preserve the plan
and supplied-assessment stages of the two relevant source evidence records.

| Project | A | B | C | D |
| --- | ---: | ---: | ---: | ---: |
| Depot: source-complete runs | 0/3 | 3/3 | 3/3 | 3/3 |
| Microgrid: source-complete runs | 1/3 | 3/3 | 3/3 | 1/3 |

The two initial assessments flagged seven and three omitted units. The cold
assessment flagged seven units with nine missing contributions. Adjudication
resolved six coverage differences and four unit-flag differences, retaining
eight omissions across seven units. It also resolved 673 execution/provenance
items against actual test bodies, commands, captured streams, observed file
versions and final code bindings. No assessment issue remains unresolved.
The initial and cold assessments remain unchanged.

## What the executed checks establish

Independent final-code evaluation passed all 708 fixed behavior cases and
recomputed 3,288 snapshots from external event histories. The native safety
monitors separately retain 336 passing and 372 unknown case results; every
run's native-monitor aggregate remains **unknown**. Unexercised triggers are
not promoted to passes. Native required review and engineering acceptance
remain `not_evaluated`.

All 24 participants eventually executed a passing sampled check with the full
independent scope. Across the histories there are 31 passing checker invocations
and nine grammar errors, followed by supported repairs. Schema/help calls remain
`not_run`. There are 42 passing local test invocations and one failed harness
assertion; the latter expected eight completed samples where its actual schedule
has seven. Its corrected assertion and the unchanged implementation are retained.

These are local observation adapters, not automatic native SysML execution.
Seventeen adapters classify the computed Python completion property as
`controlled`, while the native source declares it `input`; seven retain `input`.
That ownership equivalence is not established. Scope pins were checked in all
24 runs; trace hashes identify saved observations after their creation, rather
than an independently pinned trace document before execution. The reports do
not establish arbitrary implementation correctness, capture completeness in a
real system, physical safety, liveness or operational acceptance.

All six required reviews are process-complete, with matching saved-draft and
final bindings. Their implementation bytes did not change. Three reviews added
source context or clarified a performer; all six updated accurate pending
evidence statements after tests ran. Such evidence-status updates are not
meaning-error repairs. Ordinary arms also checked their work: 18/18 executed
local tests and sampled checks, and 12/18 saved source-linked review documents.
D therefore does not supply a clean comparison of review against no review.
Process completion does not override the remaining D-arm omissions.

## Context size and resource observations

| Project | Minified full view | Compact view | Reduction |
| --- | ---: | ---: | ---: |
| Depot | 16,819 bytes | 14,948 bytes | 11.12% |
| Microgrid | 17,736 bytes | 15,500 bytes | 12.61% |

These compare equivalent JSON values; the compact CLI's final newline adds one
byte. Independent expansion recovers the complete original report and digest.
Budget success preserves the original unknown/incomplete semantic statuses.
The compact representation shares repeated values; it does not shorten
definitions or reduce the required checker scope.

| Arm | Mean generation time | Mean charged source bytes | Budget refusals | Broker errors |
| --- | ---: | ---: | ---: | ---: |
| A | 393.4 s | 30,461.5 | 1 | 0 |
| B | 428.5 s | 31,441.7 | 3 | 0 |
| C | 501.7 s | 31,630.8 | 10 | 0 |
| D | 563.9 s | 31,446.8 | 9 | 2 |

There are 23 budget refusals across 14 runs. The two broker errors are requests
for a view limit of 34 where this study broker allows 1–32; no source body was
returned or charged. Four other calls returned a native short-ID lookup error,
and nine requests contained missing lookup keys. They remain in the records.
Compact transport did not eliminate source-access pressure or demonstrate a
reduction in total consumed model context. Latencies are descriptive whole-run
observations, not an isolated measurement of view or review overhead.

The prospective budget preflight recorded a route to all essential source notes
and selected records, leaving 2,881 depot and 1,599 microgrid bytes in C/D. It
retained response digests and byte counts, but not the original response bodies.
An independent audit preserved its eight failed assumptions about those absent
ledgers and added a clarification. A separately recorded post-run replay then
retained all 32 bodies and matched every original digest, length and budget
counter; a second inspection verified those matches. This corroborates
reproducibility without retroactively supplying original execution records.
The 24 generation runs themselves retain their actual source response bodies.

## Interpretation and retained evidence

The revised shared guidance retained the relevant qualitative goals in this
sample. C did not improve source completeness over B, and D did not improve it
over C. The study supports keeping omission review, explicit evidence stages,
strict input contracts and inspectable byte budgets. It does not justify a
claim that assembled context or mandatory review generally prevents meaning
loss.

The earlier harder study remains separate: it reported 20/24 source-complete
runs, 403/408 contributions, and M=0/U=0/O=4 units. This rerun also changes common
schema help, normalized scope delivery and provenance-path handling. Historical
differences cannot be attributed to one workflow change. Both studies use the
same known projects and shared mechanism template. Runs are the replication
units; their claims, cases and snapshots are correlated. Six runs per arm and
same-family model review are not human ground truth, held-out generalization
or a deterministic proof of unrestricted meaning.

The retained study artifacts include the frozen protocol and source hashes,
all drafts/finals and generation histories, source ledgers, failed attempts,
execution captures, initial/cold/final assessments, process/metrics audits and
separate addenda. No prior study was overwritten or pooled. The aggregate
result has SHA-256
`2bb5af7893c8d471a6d4f362bb44b7ec9dbee5f5e1fc0703936c8540807c7c60`.
Hashes identify bytes and detect drift; they do not authenticate engineer
authority or establish an independently administered protected runner.
