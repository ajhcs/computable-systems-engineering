# Concept record

Use Python 3.10+ and `scripts/concept.py`; no third-party dependencies. `init concept.json` creates a draft without overwriting. The agent maintains JSON; people can work through prose, sketches, or discussion. JSON supplies identifiable data and links, not inherently lower token use. Keep descriptions concise and retrieve relevant slices.

Only `version: 1` is required while drafting. Other top-level fields are below. Record maps use unique stable IDs across all groups: an ASCII letter followed by up to 63 letters, digits, underscores, or hyphens; `framing` is reserved. Missing fields and empty strings/lists are allowed in drafts. An optional `extra` object permits extensions in any schema object; other unknown fields are errors. Extension semantics are unchecked.

| Field | Contents |
|---|---|
| `framing` | Strings `name`, `problem`, `current_state`, `desired_outcome`, `boundary`, `context`, `timeframe`, `basis`. Explain unknowns instead of inventing dates or observations. |
| `needs` | Map of `{text, stakeholder, basis}`. Preserve distinct stakeholder perspectives and the source or assumption behind each need. |
| `functions` | Map of `{text, needs, inputs, outputs}`. `needs` contains need IDs; inputs/outputs are strings describing transformations. |
| `criteria` | Map of `{text, kind, needs, basis, measure}`. `kind` is `constraint` or `goal`; `needs` contains the need IDs to which the criterion applies. Empty/missing `needs` means global. `measure` may describe a qualitative evaluation. Record the basis for a constraint or preference and distinguish proposals from accepted choices. |
| `concepts` | Map of `{summary, functions, allocations, operations, assumptions, assessments, evaluation, comparison}`. `functions` and `operations` contain IDs. Optional `allocations` are `{function, element}` with a referenced function and coarse realizing element. `assumptions` are strings. `comparison` explains the meaningful tradeoffs, rationale, or remaining alternatives to explore; one candidate is allowed. |
| `operations` | Map of `{path, ids, sha256}` linking local version-1 CONOPS/scenario records. Paths resolve relative to `concept.json`. `ids` select referenced actors, needs, scenarios, or criteria; empty means the whole record. `sha256` is the semantic-content hash returned by the operational checker, not the raw file hash. |
| `decisions` | Map of `{text, status, by, basis, affects}`. `status`: `proposed`, `accepted`, `deferred`, or `superseded`. `affects` contains record IDs or `framing`. For accepted decisions record the actual decision maker and supporting user statement or artifact in `by`/`basis`; populated strings do not authenticate assent. |
| `questions` | List of `{text, affects, blocking}`; `affects` contains IDs or `framing`, or is empty for a global question. `blocking` is boolean. Unresolved questions remain visible. |

Each concept's `assessments` maps criterion IDs to `{finding, evidence, basis, next_check}`. `finding`: `supported`, `contradicted`, `unknown`, or `deferred`. `evidence`: `assumption`, `analysis`, `test`, `observation`, `source`, or `unknown`. Cite the actual evidence, conditions, and limitations in `basis`; use `next_check` to say how to resolve uncertainty. A supported finding based on an assumption remains a conditional claim. The checker does not calculate or independently verify these findings. Execute relevant calculations/tests separately and link their results in `basis`.

Each concept's `evaluation` has strings `method`, `data`, `environment`: the proposed evaluation and feedback plan, including what needs preparing. Plans are not completed evaluations.

```text
python <skill-dir>/scripts/concept.py init concept.json
python <skill-dir>/scripts/concept.py check concept.json
python <skill-dir>/scripts/concept.py check concept.json --concept K1 --review
python <skill-dir>/scripts/concept.py check concept.json --review
python <skill-dir>/scripts/concept.py view concept.json K1
python <skill-dir>/scripts/concept.py diff prior.json concept.json
```

`check` validates types, unique IDs, references, and allocation membership throughout the record. It reports completeness gaps separately. `--review` makes those gaps affect the exit code; drafts otherwise remain usable. Whole-record review checks framing, existing needs/functions/criteria, candidate descriptions and evaluation plans, need coverage by functions, and assessment coverage of recorded criteria. It requires no fixed alternative count, selection, quantitative weights, operational artifact, or detailed architecture. Unknown/deferred assessments can be complete for review when their basis and next check are recorded; contradicted constraints are reported as concerns, never silently converted into feasibility.

`--concept ID` reviews only the selected candidate(s), dependencies, associated decisions, and relevant questions. A criterion applies when it is global or shares a need with that candidate's functions; a missing assessment is a gap even if no assessment entry was written. Explicitly assessed criteria are also reviewed. This does not establish coverage of unrelated needs/criteria or prove that the declared applicability captures reality. Structural errors anywhere still fail. Blocking relevant questions are review gaps; unrelated incomplete drafts are not.

Linked operational records are read only when relevant to the review. The checker reports missing files, missing referenced IDs, or content drift; it does not run the operational checker, validate scenario meaning, or update saved hashes automatically. Run the peer skill's checker as needed. A formatting-only change preserves the semantic hash; any content change conservatively requires review even if only an unrelated scenario changed.

`view` without IDs returns an inventory; with IDs it returns dependency closure, relevant decisions and questions, plus framing. It includes links but does not load linked operational content. `diff` compares local records and reports changed/removed/added IDs and transitively affected dependents using both versions. It cannot detect external file changes; `check` does. Preserve previous versions before consequential changes. Neither command approves revisions or modifies records.

Exit codes: 0 = requested structural/completeness checks pass; 1 = structural errors or gaps under `--review`; 2 = unreadable input or command misuse. Duplicate JSON keys and nonfinite numbers are rejected. Reports explicitly leave semantic validation, implementation, and decision authenticity unevaluated. These local checks are not an enforcing agent harness.

## Model, views, and program feedback

This record is the current durable representation of engineering knowledge. Prose fields retain unsettled intent and qualitative evidence; they are not executable predicates. A document, diagram, or machine export is a view with a declared scope and source revision. Reconcile view edits back into the record before relying on a new check. No general SysML, Draw.io, Arcadia, or Cameo adapter is implemented here; a future exporter must expose unsupported or lost meaning.

Keep stable IDs and shared definitions; use `view` to load relevant dependencies and `diff` for changed records. Token efficiency comes from measured payloads and retrieval, not JSON or cryptic abbreviations by themselves. Preserve enough context to interpret each slice.

For computable conditions, use the actual program report for the exact record and requested scope. Repair the affected draft and rerun. Preserve source evidence and accepted criteria; removing an obligation, relaxing a threshold, narrowing applicability, changing a rule, or labeling an assumption as evidence cannot count as a routine repair. Explain a proposed engineering change for the engineer to decide. Report unsupported semantics, missing evidence, and unsuccessful checks explicitly. Discussion and incomplete drafting may continue without a review pass.

The checker is a local helper, not a protected verification authority. These instructions do not prevent bypass, edited scripts, forged results, or fabricated evidence. An enforcing harness needs independently controlled rules and accepted baselines, fresh checks bound to the submitted record and dependencies, and acceptance outside the drafting model's write authority. Populated approval fields and hashes alone do not provide that boundary. No FRET engine, protected runner, or general behavioral proof is installed by this revision.
