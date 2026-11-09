# Meaning-context adversarial study

This synthetic study exercises the assembled view and the shared
[meaning-preservation workflow](../../docs/meaning-context.md). Its source is
[brief.txt](brief.txt), an authored proposal. It is not a clinical requirement,
validated workflow or operational dataset.

The source defines handoff completion as receiving acknowledgement for the same
referral from the selected receiving clinic. Sending alone does not complete it.
Waiting is allowed and has no declared deadline. The native model contains a
sampled safety invariant for active handoffs: completion implies acknowledged.
That invariant does not establish eventual completion or the reverse implication.

## Inputs and evidence boundaries

- [handoff.sysml](handoff.sysml) is the native model. It contains documentary
  workflow records, a qualitative delay-reduction goal, explicitly different
  roles for one clinic, and the selected completion requirement.

- [handoff.english.json](handoff.english.json) reuses `foundation-1.0` and
  `english-1.0`. The two `handoff` labels have different namespaces, definitions
  and native identities. Existing source, term and text pins are retained.

- [manifest.json](manifest.json) independently selects the native requirement;
  [sampled-obligation-scope.json](sampled-obligation-scope.json) selects the same
  obligation for the existing pure language monitor. View limits change neither.

- [cases.json](cases.json) names 37 adversarial and valid-control cases. Eight
  interpretive cases pair actual candidate/control text under [outputs](outputs).
  Their expectations are authored review oracles; `computed_verdict` is `not_run`.
  Other cases exercise existing checks, assembled context and normal unit code.

- [reference.py](reference.py) is trusted synthetic test code, including two
  deliberate implementation faults. The tests use an independent observation of
  received referral/clinic identities. They do not reuse the implementation's
  acknowledgement decision. Corpus records supply bounded input data, not code.

`E_PLAN` remains an unexecuted plan. `E_REPORTED` remains a supplied assessment.
Executing this test suite does not upgrade those model records to observations.
The open acknowledgement transport mapping remains unresolved. A separate unit
control reuses the existing `examples/sysml/quantity.sysml` clause; its quantity
bound is unrelated to handoff completion.

## Run

From a complete checkout or installed runtime, with the pinned SysML parser
available in the selected cache:

```sh
python3 scripts/sysml_view.py examples/meaning-context/handoff.sysml --profile examples/meaning-context/handoff.english.json --element S_HANDOFF --source SYN_HANDOFF=examples/meaning-context/brief.txt
python3 -B tests/test_context_evaluation.py
```

Native cases parse the actual fixture and exercise the CLI. In-memory mutations
then test status handling without repeatedly parsing edited files. The real view
entry point reads model/profile/source files and never accepts a saved parser
inventory as an authoritative input. Without the parser, native cases are skipped;
that is not evidence that they passed. The required full regression can use
`python3 scripts/check.py --require-sysml`.

Suite controls cover scoped homonyms, multiple roles, relationship direction,
completion, applicability, units and revision drift. Other cases cover evidence
stages, missing mappings, retrieval limits, unsupported comparisons and implementation faults.
A lexical pass on the supplied bad completion sentence remains possible and is
exercised as an expected coverage limit. The view exposes definitions and text;
it does not compute an unrestricted prose-meaning verdict.

The implementation controls show sending, waiting, a matched acknowledgement,
an unrelated referral and another clinic. The two faulty variants complete on
send or accept any acknowledgement. The existing sampled monitor detects their
observed completion-without-matched-acknowledgement counterexamples. Reference
unit assertions also check that the matched acknowledgement completes the handoff.
These tests support this synthetic mechanism, not general implementation,
physical, clinical or operational correctness.

## Generation comparison protocol

Generation quality remains **unmeasured**. The deterministic suite does not run
an autonomous agent benchmark or infer scores from authored expectations.
To evaluate the shared workflow, keep the model, source, retained obligations,
model version, task prompts and resource budget identical across four arms:

| Arm | Context and review |
|---|---|
| A | Existing CSE workflow and current parsed view. |
| B | A plus the shared meaning-preservation instruction. |
| C | B plus the assembled definitions and context. |
| D | C plus review of the actual output claims or implementation behavior. |

Use the same complete model and independent obligations in every arm. Record
actual tool calls and the exact delivered text/code, not only a successful view
receipt. Reset each trial so a corrected answer or earlier oracle does not leak
into the next generation. Run repeated trials; record the model and configuration.
Randomize output labels and order for independent interpretive assessment. Keep
the evaluator separate from the generating agent and withhold the bad/control
answers during generation.

For a material finding, retain the disputed output and its location. Record
relevant concept/relationship IDs, source meaning, review method and result. Use deterministic checks for supported properties.
Interpretive judgments remain assessments; disagreements and unsupported claims
stay visible. A candidate cannot obtain success by deleting a retained obligation
or changing the definition to match its output.

Report meaning errors, unsupported claims, unresolved-mapping handling and valid
controls separately from deterministic check results. Counts of tokens and time
are secondary measurements. Do not claim a reliability gain until actual trial
outputs have been evaluated under this protocol.
