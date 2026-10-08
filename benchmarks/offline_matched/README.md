# Offline preparation for a matched interface comparison

This package prepares an equal-information comparison and exact source-copy
oracles. It does not implement a native semantic API or run an AI or human trial.
No native capability is accepted by these results. The accepted CSE lifecycle
accountant remains unchanged at base `be800ed4b82d7a68613458cf6a2ca840958365e3`.

## What the comparison can establish

Three arms contain the same task-selected facts, typed values, source identities,
citations, revision, authority statement and evidence limits:

| Arm | Controlled representation | Role |
|---|---|---|
| `semantic_query_replay` | One source-anchored reference packet | Stand-in pending a native query contract |
| `duplicated_artifacts` | Two containers; each has needed unique facts and both repeat one fact | Controlled duplication treatment |
| `deduplicated_artifact` | One container with each fact once | Control for a well-designed artifact interface |

All three use one batch read. The retry condition adds the same failed lookup and
one recovery call in every arm. No arm receives extra evidence or fewer necessary
constraints. A canonical comparison rejects different values, units, labels,
citation offsets, revisions, authority/limits, extra assertions and conflicting
duplicates. The hash identifies the compared bytes; it does not authenticate
semantic authority. The manual qualified labels are explicitly not native IDs.

This fixture deliberately controls retrieval. It does not show that real artifact
users must read duplicate content, or that semantic queries are inherently more
efficient. In the prepared data the deduplicated artifact has exactly the same
size as the semantic-query replay. A future naturalistic trial must let actors
select, batch and avoid unnecessary reads in every arm, then record the actual
retrieval and retries. Unretrieved files have no model-context cost.

## Reproduce without a model or new dependencies

Use existing Python 3 and the exact source and license below, kept outside Git.
No automatic download, model client, native executable or credential read exists
in this package. Run from the repository root:

```sh
OFFLINE_EV_SOURCE=/absolute/cache/EVSample.sysml python3 -B tests/test_offline_matched.py
python3 -B benchmarks/offline_matched/prepare.py \
  --source /absolute/cache/EVSample.sysml \
  --license /absolute/cache/LICENSE \
  --output /absolute/fresh/output
```

`LICENSE` must be beside the source for the CLI tests. Output must not already
exist. Preparation writes only to that fresh directory and verifies source bytes
again after producing evidence. The source stays unchanged. The review bundle
contains answer and patch oracles alongside packets and therefore must never be
used wholesale as an agent workspace. `ROLE_SEPARATION.json` specifies exactly
three allowed files for each task/arm; a future isolated runner must enforce the
allowlist. The manifest itself is not an access-control mechanism.

The BuilderBob evidence run uses the existing seccomp wrapper to deny IPv4/IPv6
socket creation to preparation/tests and their descendants. This is not a claim
of a new protected evaluation runner or a complete syscall audit.

## Measurement contract

`REPORT.json` retains all 36 scripted conditions: six queries, three arms and
clean/one-forced-retry schedules. Per condition it records exact UTF-8 bytes and
**regex-wordpunct-v2**: Python Unicode matches of `\w+|[^\w\s]`. This is a named
text-size estimator, not a model tokenizer or a billable-token conversion.

The fixture's protocol total is bootstrap + task + every request + every result,
including failed calls. It counts each recorded message once. It is not the sum
of complete inputs presented to a model across turns. If complete model request
frames are actually recorded, `cost_ledger` separately sums every whole frame,
including repeated prefixes. Unknown payloads keep the complete protocol total
null and preserve only a known subtotal; explicitly empty bytes are known zero.
Provider usage and billed cost are always null in this offline preparation.

The 396-byte / 98-estimator-unit bootstrap is this fixture's shared envelope,
not the CSE plugin or native application's initial context. Initial native
discovery, tool schemas, hidden provider context, model outputs, compaction/cache
behavior, human/domain questions and provider safety confirmations are not
observed here. These remain unavailable, not zero. Measured fixture totals and
per-operation details are in `MEASUREMENTS.json` and the bundled raw report.

## Tasks and oracle boundaries

| Task | Engineering question or proposed change | Original capability mapping | Exact reference check |
|---|---|---|---|
| Q01 | Inspect battery type and four scalar/quantity declarations | K01, K05, K10 | IDs, numbers, units and source locations |
| Q02 | Inspect the directed battery-to-motor declaration | K02, K04, K05 | Endpoints and declared direction; no compatibility or execution verdict |
| Q03 | Disambiguate C1/L1 `requiredRange` declarations | K03, K05 | Qualified labels, 130/200 km and distinct citations |
| Q04 | Follow the small-range analysis requirement binding | K04, K08, K10 | Binding, C1, 130 km and comparator; no successful execution inferred |
| Q05 | Explain large-EV mass prose/assumption discrepancy | K03, K08, K10 | Source says 900 kg in prose, less than 1200 kg in the assumption, 1100 kg for the declared mass; intended limit unresolved |
| Q06 | Inspect capacity/voltage targets before proposing a copy | K05, K09, K10 | Correct targets and unchanged units; proposal only |
| P01 | Change only capacity 50 to 60 A⋅h in a copy | K09, K10 | Exact one-literal byte delta and original preservation |
| P02 | Also change voltage 300 to 310 V in the copy | K09, K10 | Exact two-literal delta; partial/extra changes fail |

There are 16 short attributed source facts. Numeric literals and units are checked
against unique source anchors. Other semantic annotations, including qualified
labels and relation descriptions, still need independent review; this is not a
SysML parser. Exact answer matching checks structured claim fidelity, not the
quality of an open-ended engineering explanation. A future rubric must accept
semantically equivalent explanations and explicitly score uncertainty.

Patch checks compare externally collected bytes to a reference. Tests obtain
expected candidates independently using literal replacements. Synthetic review
records bind base revision, intent, candidate and generation; altered, cancelled
or declined records do not qualify. They are not authenticated human consent,
and a checker cannot prove that a native operation is atomic, recoverable or
replay-safe. Those properties require actual native state-transition tests.

## Future human/AI comparison protocol

1. Freeze one native candidate, support profile, shared semantic-core identity and
   typed API contract before selecting qualification tasks. Route requests through
   the parent. Bind each result to that exact pin; do not edit the native owner's
   checkout or relabel older V8.1 evidence as V8.2 acceptance.
2. An independent reviewer selects licensed held-out task partitions after the
   implementation freeze and records exposure. Keep their source-ID inventories,
   expected paths/diagnostics and allowed patches outside actor context. Public
   availability does not prove absence from pretraining. EV here is calibration.
3. For the primary comparison, match model/version, Standard service tier,
   reasoning settings, task/goal, initial state, dependency closure, support and
   safety policies, output schema, tools available, time/step limits and review
   decisions. Use fresh isolated sessions and copies; counterbalance order across
   tasks/replicates (AB/BA, with the deduplicated control rotated as well). Record
   stochasticity and exact settings. Do not combine single-pair pilot numbers with
   this unexecuted protocol or choose tasks retrospectively from successful runs.
4. Compare equal information both available and actually delivered. Reject a
   primary pair if evidence/revisions differ. Run stale/incomplete/conflicting
   evidence as separately labeled recovery tests; do not call the easier arm's
   advantage an interface-cost gain under equal information.
5. Log every tool request/result, error, retry, schema fetch, elicitation and
   terminal outcome. Preserve raw evidence and use the accepted lifecycle
   accountant for compatible provider events. Report total tools/retries, scoped
   protocol bytes/estimates, actual provider input/cache/output tokens when given,
   complete request-context frames when observable, and all missing fields.
   Failed/cancelled/time-limited tasks stay in the denominator. Do not infer a
   bill from proxy tokens, sum duplicated terminals, or fill unknown inputs with
   zero. Report completion and semantic fidelity separately from context cost.
6. Independently score goal completion; correct source/native IDs, units,
   ownership, relations, requirements and allowed patch; preservation and
   save/reopen/reversal; uncertainty and recovery; human usability; and needless
   questions. UI mechanics, deterministic reference checks and actual agent
   behavior are separate evidence classes. Do not award agentic success from a
   replay or award human usability from scripted clicks.

Current Q01–Q06 goals and P01/P02 edit intents contain all requested facts/values.
They should require no plugin domain question. Q05 asks to report uncertainty,
so it does not require asking the engineer to resolve the mass limit. A separate
follow-up that asks to repair that ambiguous intent needs one focused question
unless earlier authorized context resolves it. Preserve supplied answers; reject
invalid/stale bindings in code; cancellation/decline yields no mutation. Test
unnecessary question, valid answer, invalid answer, cancellation, stale source and
already-answered cases against the actual future elicitation transport. Record
provider safety confirmations separately, even when they interrupt a task. They
are not plugin domain questions or automatically a plugin defect.

## Native contract and original ten-capability gate

Required native contract: typed discovery/support states; scoped query and
pagination semantics; stable IDs/source mapping; revision-bound snapshots;
validation/uncertainty codes; and preview/review/apply identities bound across
calls to the same base, exact proposal, candidate and generation. Apply must
reject stale/replayed/cancelled review or changed operations without partial
mutation. Include save/reopen/undo and interruption outcomes. Existing V8.1
`functional-copy` internally prepares a fresh proposal and does not take the
caller's previous preview identity; this bounded observation remains a question
for the native owner, not a change made here.

The original scope remains exactly these ten capabilities:

1. Build a typed system hierarchy
2. Define interfaces and connect components
3. Author structured requirements
4. Trace requirements to design and verification
5. Find and inspect anything in the model
6. Create linked architecture views
7. Import real models with a fidelity report
8. Validate meaning and show actionable diagnostics
9. Review and reverse model changes
10. Expose a safe automation and agent API

This package adds acceptance preparation within that scope. It does not complete
the positive jobs for any capability; K06 and K07 have no positive fixture in this
package. The previously frozen H01–H10/A01–A10 native acceptance plan remains the
full gate. Required official v2 and licensed TMT import/fidelity cases remain;
NASA JT9D is a separate unsupported-native-format/uncertainty case until a reviewed
adapter and numerical oracle exist. Safe rejection is not a positive capability
pass. Migration, simulation, numerical accuracy and cross-platform packaging are
not accepted by these checks.

## Attribution and source pins

The short quotations in `fixtures.json` are derived from the Systems-Modeling
SysML-v2-Release contributors' [EVSample.sysml at fb97b754](https://github.com/Systems-Modeling/SysML-v2-Release/blob/fb97b754f29588b8e9c7a35f370880cd15eb29e7/sysml/src/examples/State%20Space%20Representation%20Examples/EVSample.sysml),
licensed under [EPL-2.0](https://github.com/Systems-Modeling/SysML-v2-Release/blob/fb97b754f29588b8e9c7a35f370880cd15eb29e7/LICENSE).
Retain the upstream license with raw copies. No endorsement is claimed.

- Source: 11,002 bytes; SHA-256 `4834675f798fb275b847887b53661bc351be8094b2f320ee4819d2bb4b71d3db`.
- License: SHA-256 `0becf16567beb77fa252b7664631dd177c8f9a1889e48995b45379c7130e5303`.
- Exposure: previously used public pilot, calibration only; not newly held out.
- Raw source, license, modified source-copy candidates and run outputs stay in
  ignored cache/evidence directories, outside Git. No coursework input is used.

Independent oracle/native review, human reviewers and parent-authorized bounded
Standard runs remain outstanding. No new paid batch, credentials, subscription,
publishing, deployment or external communication is part of this preparation.
