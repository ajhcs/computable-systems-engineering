# Shared legacy version-1 operational record

This contract remains for existing `conops.json`/`scenarios.json` files and
explicit version-1 work. New recorded operational work defaults to the
authoritative SysML v2 model described in [sysml.md](sysml.md). No implicit
prose-to-behavior conversion is performed.

Use Python 3.10+ and `scripts/conops.py`; it has no third-party dependencies. Paths in commands are relative to the working directory, so use the actual skill directory when invoking the script. `init conops.json` creates a draft and refuses to overwrite an existing file.

Both skills use this version-1 format. Reuse an existing record; standalone scenario work can use `scenarios.json`. Keep engineer decisions and proposed assumptions distinguishable in the relevant `basis`, `assumptions`, or `questions` text. A populated field does not prove an engineer endorsed it.

The repository also offers an opt-in version-2 finite verifier (`scripts/verify.py`, contract in `docs/verifier-v2.md`). This version-1 record has no executable guard/effect semantics and is not implicitly adapted to version 2. Its standalone helper remains the correct checker for this format.

The agent writes this record; people can discuss, sketch, or edit natural-language descriptions. JSON is an interchange format, not a claim that JSON is inherently token-efficient or a new engineering language. Keep descriptive text concise, preserve meaning, and do not copy source documents into the record.

Top-level fields: `version` (1), `system`, `actors`, `needs`, `scenarios`, `criteria`, `questions`, `review_notes`. All except `version` may be omitted while drafting. Each object can carry an optional `extra` object for extensions; other unexpected fields are errors to catch misspellings. Stable IDs are unique across actors, needs, scenarios, and criteria. `system` is reserved for the system of interest.

| Field | Contents |
|---|---|
| `system` | Strings `name`, `purpose`, `boundary`. |
| `actors` | Map from ID to a nonempty description of an external person, organization, or system. |
| `needs` | Map from ID to `{text, actor, basis}`. `actor` references an actor ID. `basis` identifies the user/source statement, observation, or assumption and its reason; it is not a truth certificate. |
| `scenarios` | Map from ID to `{need, kind, setting, trigger, steps, outcome, assumptions, evaluation}`. `kind`: `normal`, `off_normal`, or `lifecycle`. `need` references a need ID. `steps`: ordered `{from, to, exchange}` objects whose endpoints reference actor IDs or `system`; each exchange crosses the system boundary. `assumptions`: strings. `evaluation`: strings `method`, `data`, `environment`. |
| `criteria` | Optional map from ID to `{scenario, metric, op, value, unit, basis}`. Numeric thresholds only; `op` is `<`, `<=`, `==`, `!=`, `>=`, or `>`. Record who established the threshold or that it is an assumption. Qualitative evaluation remains in the scenario. Improvement goals do not need invented pass/fail thresholds. |
| `questions` | List of `{text, affects, blocking}`. `affects` is a list of record IDs or `system`; `blocking` is a boolean identifying a decision-blocking question. Missing questions remain visible in the report; `--review` flags blocking ones. |
| `review_notes` | Strings `stakeholders`, `off_normal`, `lifecycle`: explain coverage, relevance, or why further work is deferred. No required number of scenarios or fixed sequence of conversation turns. |

Strings may be empty during drafting. The checker reports incomplete review fields separately from malformed data and broken references. It checks presence and linkage, not the quality or truth of text. It cannot establish that a stakeholder was consulted or that a scenario faithfully represents reality.

Commands:

```text
python <skill-dir>/scripts/conops.py init conops.json
python <skill-dir>/scripts/conops.py check conops.json
python <skill-dir>/scripts/conops.py check conops.json --review
python <skill-dir>/scripts/conops.py check scenarios.json --scenario S1 --review
python <skill-dir>/scripts/conops.py check scenarios.json --scenario S1 --scenario S2 --review
python <skill-dir>/scripts/conops.py view conops.json S1
python <skill-dir>/scripts/conops.py diff old.json conops.json
python <skill-dir>/scripts/conops.py evaluate conops.json observations.json
```

`view` without IDs returns a compact inventory. With IDs it returns those records plus their referenced dependencies and related questions. `diff` reports changed, added, and removed records and transitively affected dependents; it does not rewrite the record or erase old evidence. Preserve the prior version before consequential revisions. Wording-only changes can conservatively mark evidence for reconsideration.

`check --scenario ID` checks the entire record for malformed data and broken references, but reviews completeness only for the selected scenarios, their dependencies and criteria, and relevant questions. Global questions still apply. An incomplete unrelated draft does not become a scenario-review gap. This mode does not require a normal scenario when reviewing an exception, overall need coverage, or the CONOPS `review_notes`. Whole-CONOPS review remains `check --review` without selection. A focused pass does not establish overall CONOPS coverage. Existing review rules require context, a linked need, inbound and outbound exchanges, and an evaluation plan; these are this checker's declared conditions, not a universal definition of every operational event.

`check` returns a semantic-content SHA-256, independent of JSON whitespace and object-key ordering. For numeric evaluation, supply observations shaped as follows:

```json
{"model_sha256":"<hash returned by check>","results":{"C1":{"value":85,"unit":"ms","evidence":"Run artifact and location","context":"Workload and measurement conditions"}}}}
```

`evaluate` refuses mismatched model hashes, invalid measurements, unknown criteria, and unit mismatches. Missing observations are `unknown`. It compares finite numbers against the declared criteria, without running supplied code or converting units. Observation provenance and context are required strings but are not independently authenticated. It does not measure the implementation, prove unobserved behavior, or validate a chosen threshold. Never describe synthetic observations as an implementation test.

Exit codes: 0 = requested checks completed without their listed failures; 1 = malformed structure, review gaps under `--review`, failed/unknown numeric result, or stale evidence; 2 = unreadable input or command misuse. These are local checks. A skill cannot force an agent to invoke them; an external harness would need to enforce any consequential gate.

## Model, views, and program feedback

For a legacy version-1 workflow, this record is the durable representation of engineering knowledge. Prose fields retain unsettled intent and qualitative evidence; they are not executable predicates. A document or diagram is a view with a declared scope and source revision. Reconcile view edits back into the record before relying on a new check. The separate SysML-first path does not silently convert this record.

Keep stable IDs and shared definitions; use `view` to load relevant dependencies and `diff` for changed records. Token efficiency comes from measured payloads and retrieval, not JSON or cryptic abbreviations by themselves. Preserve enough context to interpret each slice.

For computable conditions, use the actual program report for the exact record and requested scope. Repair the affected draft and rerun. Preserve source evidence and accepted criteria; removing an obligation, relaxing a threshold, narrowing applicability, changing a rule, or labeling an assumption as evidence cannot count as a routine repair. Explain a proposed engineering change for the engineer to decide. Report unsupported semantics, missing evidence, and unsuccessful checks explicitly. Discussion and incomplete drafting may continue without a review pass.

The checker is a local helper, not a protected verification authority. These instructions do not prevent bypass, edited scripts, forged results, or fabricated evidence. An enforcing harness needs independently controlled rules and accepted baselines, fresh checks bound to the submitted record and dependencies, and acceptance outside the drafting model's write authority. Populated approval fields and hashes alone do not provide that boundary. No FRET engine, protected runner, or general behavioral proof is installed by this revision.
