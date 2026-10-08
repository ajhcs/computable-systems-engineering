# CSE interface benchmark protocol

This is a product-improvement corpus, separate from all private/coursework tests.
Baseline is `b01ef01698450e5a47cc20f957fe93a09e9744b4`. Candidate code is frozen
before opening the held-out model contents; record its commit in the run manifest.
Synthetic unit fixtures are development data and never count as real engineering
task success. A public source may be known to the pretrained model: held-out here
means not used to develop this interface, not provably absent from model training.

Pin each upstream Git revision, raw bytes, license and README with
`scripts/pin_interface_corpus.py`. Raw public models live only in ignored cache.
Verify bytes against `corpus-lock.json` before each run. A changed hash stops the
run. Keep native families distinct: NASA T-MATS MDL is Simulink, TMT mdzip is
SysML v1/MagicDraw, and EVSample is an official SysML v2 example. The official
example is not a proven industrial project. Reserve TMT for independent follow-up.

## Task matrix and oracles

| Task | Inputs | Genuine oracle and limit |
|---|---|---|
| Inspect | Held-out SysML example and NASA JT9D | Pinned native declarations, IDs, source lines; parser inventory only for SysML. |
| Decompose | NASA JT9D | Upstream component/block connections with source citations; independent engineer checks proposed boundary and allocations. No thermodynamic result. |
| Edit | SysML example | Engineer-specified bounded edit, original declarations/units, parser validation and unaffected-structure diff; expert checks meaning. |
| Validate | SysML example; NASA/TMT unsupported formats | Independent parser diagnostics and exact supported claim scope. NASA numerical baseline requires native simulation and is unavailable here. |
| Migrate | NASA MDL or reserved TMT archive | Correctly identify unsupported conversion, preserve source, elicit the missing export/target decision, enumerate semantic losses. No claimed lossless migration. |
| Explain uncertainty | All families | Source-backed limitations and separation of parser acceptance, computation and real-system evidence, reviewed by an independent engineer. |
| Recover | Missing bundle member, invalid ID, syntax defect, stale question | Injected defect manifest and restored parser result; invalid/stale/cancelled questions cannot mutate the candidate or satisfy an obligation. |

## Matched model runs

Use the existing ChatGPT login, ephemeral sessions, explicit `service_tier=default`
(Standard), one fixed available model/effort, identical input bytes/task text,
budgets, sandbox and tools. Never resume private sessions or read session stores.
Use separate snapshots of baseline and candidate, not either owner's live tree.
Record CLI version, requested model/effort/tier, input hashes, code commits, order,
UTC start/end, complete new event logs, provider-reported usage when available,
tool calls/results, final artifacts and independently scored outcomes. Stop on
access/approval/quota errors; do not switch tier, provider or credentials.

Counterbalance order across repeats. Report sample size, paired per-task outcomes,
failures and unfinished trials. A single pair is a pilot, not a reliability estimate.
Do not tune on failed held-out cases and continue calling them held-out: reserve a
fresh family or report contamination and rerun a new frozen candidate explicitly.

## Scoring and cost

Score completion per task only after both artifact and task oracle checks.
Report separately semantic fidelity (preserved IDs, units, thresholds, source
meaning, uncertainty), invalid claims, unsupported-format handling, tool count,
context bytes, provider tokens and elapsed time. Unknown/timeout/skipped oracle
checks are incomplete, never passes. Human meaning judgments require signed
review notes; parser equality alone does not establish fidelity.

Count domain questions and needless questions separately from provider permission
confirmations. A question is needless when its answer was already supplied,
unrelated, repeated after cancellation, or routine mechanics. Inspecting existing
facts and explaining uncertainty should not trigger domain elicitation. Record
valid necessary questions, cancellations and unresolved decisions, not just a low
question count. Provider safety policy must remain unchanged across conditions.

`measure_interface.py` measures exact controlled payload bytes and
`regex-wordpunct-v2` estimates. CLI/provider scaffolding is excluded and disclosed.
Model-reported usage from actual trial events is a separate field; unavailable is
null, never zero. Deep workflow guidance may still be necessary; its loading cost
must be counted when used. Static cold-load comparisons are scenarios, not proof
of universal savings.

## Independent handoff

Review schemas/CLI admission, cancellation/replay/staleness, transcript event
counts, output truncation disclosure and the preservation of engineering authority.
Audit every claimed real-model completion against source and genuine oracle.
Reproduce `scripts/check.py --require-sysml`, then run a fresh counterbalanced pair
on reserved TMT/native formats only with the needed native tooling and engineering
oracle. No proprietary simulator installation or paid provisioning is authorized.
