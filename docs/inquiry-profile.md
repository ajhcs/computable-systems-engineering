# From an engineering question to a capacity answer

This integration reuses the existing candidate inquiry and original tests from
`c27f52a121a00e97900880e95011ff9c9479e634`. Record version `inquiry-1.0` remains
supported. Version `inquiry-1.1` adds optional [conditional mean-flow consistency](#conditional-mean-flow-consistency)
to the same source-bound native documentation profile. The header remains
`CSE-INQUIRY/1.0`; the JSON record carries its explicit minor version.

Use this flow for a particular workload or resource question, at the depth needed now. The engineer supplies intent and consequential facts; the assistant maintains the model, invokes the program and explains the result. A complete system concept or CONOPS is optional.

The question can be small: “Can the backup handle 12 jobs/minute?” Start with the stated work and workload/unit, available means, and their stated capability/rates. Preserve what was supplied, label interpretations and new assumptions, and ask only what changes the answer. Missing figures or compatibility can remain unknown. The engineer retains selection, requirements, thresholds and accepted meanings.

## Workflow

1. Read existing work and the source facts in place. Keep user-specific models, source material and reports in the selected project's ignored/private work directory, outside an installed plugin (this repository: `work/` on `/workspace`). Never commit raw private notes. Original examples here use invented source briefs, not academic figures or vendor specifications.
2. Record a scoped question in the authoritative `.sysml` model. A `cseInquiry` documentation block inside one parsed concern holds the bounded `CSE-INQUIRY/1.0` record. Native actions identify selected functions; native part usages identify means. Quotes and source hashes identify the supplied facts, not accepted interpretation or authentic assent.
3. Run the program with explicitly supplied source files. Read the concise answer or inspect the same JSON evidence. Source/name/schema errors block arithmetic. Unknown facts remain unknown; partial drafts can retain a known arithmetic result while other facets are unresolved. Do not repair a failure by lowering workload/minima or deleting a function without an engineering decision.
4. Explain the result and the next decision. Compare one or more alternatives without automatic ranking or selection. A passing conditional calculation still needs qualification of capability, rates, operating conditions and any concurrent/additive assumptions. Review a changed candidate as a new model/source revision.

These are drafting and read-only analysis operations, not an autonomous agent harness. No LLM provides the deterministic verdict. No model-supplied code or executor is admitted.

The [human-task example](../examples/human-task-review/concept.sysml) now carries
its capacity inquiry in the same authoritative model. Its before-P3 revision is
retained privately with the prior qualification receipt. The new hypothetical
rate source is separate from the task-description source. Rates are not derived
automatically from the proposed task durations. Selecting a primary-clerk loss
gives 8 versus 12 requests/hour for the existing backup, 16 versus 12 for a
proposed larger capability, and unknown when backup capability is unqualified.
Application/terminal availability is an explicit premise; application-loss
analysis is not admitted by this deliberately narrow clerk-rate model.

Use explicit hypotheses to compare alternatives or resource-loss cases. The
program does not infer losses from question text, optimize staffing, automatically
choose an alternative or invent weights. Your system-concept objectives and
stakeholder preferences still determine the decision. Nominal unit equality,
declared capability and arithmetic do not establish physical dimensions, actual
training effectiveness or measured operational capacity.

## Conditional mean-flow consistency

The pre-2000 source is John D. C. Little, *A Proof for the Queuing Formula:
L = λW*, 1961, Operations Research 9(3), pp. 383–387. Its abstract conditions the
result on finite means, strictly stationary corresponding processes and a
metrically transitive arrival process with nonzero mean.
[Publisher original](https://pubsonline.informs.org/doi/abs/10.1287/opre.9.3.383).
The tool retains that bounded theorem profile and additionally asks for a matched
population/boundary and compatible averaging context; it does not infer these
conditions from a short observation window.

Version 1.1 optionally adds `flow_checks`, an ID map of at most 64 entries:

```json
{
  "label":"Declared request means","subject":"R_STATION",
  "boundary":"Entry to exit of the selected station.",
  "population":"Requests in that station.",
  "averaging_context":"Hypothesized compatible stationary means.",
  "units":{"population":"requests","time":"minute"},
  "conditions":{
    "finite_means":{"value":true,"basis":"SRC"},
    "strict_stationarity":{"value":null,"basis":null},
    "metrically_transitive_arrivals":{"value":null,"basis":null},
    "matched_boundary_population":{"value":true,"basis":"SRC"},
    "compatible_averaging":{"value":true,"basis":"SRC"}
  },
  "L":{"value":"2","unit":"requests","basis":"SRC"},
  "arrival_rate":{"value":"1","unit":"requests_per_minute","basis":"SRC"},
  "W":{"value":"2","unit":"minute","basis":"SRC"},
  "tolerance":{"value":"0","unit":"requests","basis":"SRC"}
}
```

The subject references a declared/native-bound resource. Quantities reuse the
existing nonnegative exact-decimal/source-basis contract. L, arrival rate, W and
tolerance may be null while unknown. Conditions are Boolean/null with explicit
source/assumption bases. Sources are supplied explicitly and checked before
arithmetic; neither their bytes nor true flags establish real-world applicability.

When all conditions are explicitly true with checked bases, units match and the
arrival rate is positive, the helper compares `abs(L - arrival_rate * W)` with the
explicit tolerance. It uses existing Fraction arithmetic/decimal display without
rounding or inferred unit conversion. Missing context/quantities/conditions are
unknown, false applicability and zero arrival rate are unsupported by the retained
theorem profile, and malformed records are errors. Unsupported output precision
does not become a rounded pass. No staffing number is computed.

The [synthetic flow example](../examples/inquiry/flow-consistency.sysml) hypothesizes
all applicability conditions; it does not supply observations. A flow-only record
may leave functions/alternatives empty but still needs its native subject and
source-bound question. Combined records aggregate all selected capacity/flow
checks; an unknown or failed selected check cannot become an overall pass.
Changed inputs clear computed results. Flow checks belong to version 1.1;
including them in a 1.0 record is refused.

Further quantitative work needs task-time/demand data, compatibility and shared
resource evidence, uncertainty/sensitivity appropriate to the decision, and
qualification of the declared inputs. The existing qualitative trade-study
directions are not replaced by rate comparisons. Task-network simulation and
fatigue/rest methods remain excluded.

## Minimal start and ordinary use

The assistant handles these commands. A bare question does not need rates, alternatives or a long questionnaire:

```sh
python3 skills/develop-system-concept/scripts/cse.py question start work/question.sysml --text "Can the fallback meet the workload?"
python3 skills/develop-system-concept/scripts/cse.py question answer work/question.sysml --format text
```

The first command exclusively creates an incomplete native draft; it does not infer facts, validate syntax or establish feasibility. `answer` uses the installed pinned parser and returns unknown with the essential missing work/workload/means. It installs nothing automatically. Existing files are never overwritten.

For explicit structured drafting input, `question prepare INPUT.json MODEL.sysml --package PACKAGE` emits the native model. INPUT is temporary drafting data, not a competing authoritative saved model. `prepare` supports direct members of one package, validates names, escapes documentation delimiters and does not run native validation. The assistant can also edit an existing native model directly, preserving other content and accepted meaning. A standalone copied skill needs the complete shared CSE runtime as before.

For a populated original example:

```sh
python3 skills/develop-system-concept/scripts/cse.py question answer examples/inquiry/software.sysml --source SRC=examples/inquiry/software-brief.md --unavailable R_PRIMARY --format text
python3 skills/develop-conops/scripts/cse.py question answer examples/inquiry/hardware.sysml --source SRC=examples/inquiry/hardware-brief.md --alternative A_SPARE --unavailable R_FIRST --format text
python3 skills/develop-operational-scenarios/scripts/cse.py question answer examples/inquiry/physical-process.sysml --source SRC=examples/inquiry/physical-process-brief.md --format text
```

All three launchers expose the same flow. JSON is default; `--audience expert --format text` adds identities/hashes. `--alternative ID` selects one alternative; omission evaluates all declared alternatives. Repeat `--unavailable ID` for joint loss. Availability is the explicitly requested hypothesis, not an observed operating state. The answer separates the recorded question from the actual evaluated hypothesis, including an empty loss selection (all declared means assumed available). It never infers conditions from natural-language question text. The assistant must deliberately pass any intended outage with `--unavailable`; a no-loss baseline is a different calculation when the recorded question asks about an outage. Any declared resource can be unavailable across alternative comparisons; its loss has no effect in alternatives where it is unassigned. Unknown, duplicate or wrong-kind IDs are refused, with no convenient subset evaluated.

A comparison retains failed and incomplete alternatives. Overall status aggregates all selected checks; it does not mean every alternative failed or that no candidate exists. Per-alternative results and a summary retain conditional passes, shortfalls and unresolved options. No selection is made. This query does not run required engineering reviews or weaken their scope.

## Record contract

The documentation body begins with `CSE-INQUIRY/1.0`, followed by one JSON object. The common top-level fields are `version`, `question`, `sources`, `functions`, `resources`, `alternatives`. Version `inquiry-1.0` admits exactly those fields; `inquiry-1.1` also admits the optional `flow_checks` map described above. Maps contain at most 64 ASCII IDs; one alternative admits at most 512 distinct assignments. Record size is at most 1 MB, native model at most 5 MB, and each source at most 1 MB. Quantities are nonnegative exact decimal strings with at most 32 whole and 32 fractional digits; no floats, nonfinite values, negative capacities or unbounded rational formatting. Duplicate JSON keys and unsupported fields are rejected. Linux acquisition rejects final symlinks, FIFOs and other nonregular files. Model/source bytes and the native parser's model digest must remain stable during checking.

- `question`: `{text,basis}`. `basis` is a source ID or null in a draft.
- `sources`: each `{sha256,excerpt,kind}` with kind `provided`, `assumption`, `proposal` or `reported_observation`. `--source ID=PATH` supplies files explicitly; a model record never opens its own paths. The excerpt must occur exactly once in matching UTF-8 source bytes. Missing files/inputs, mismatching hashes, ambiguous quotes and errors cannot pass. A reported observation is not authenticated or independently qualified by this check. Source quotes/hashes prove neither interpretation nor current applicability. Use concise permissible source derivatives/references; keep private source quotations in private artifacts.
- `functions`: each `{native_name,label,demand,minimum_assignments,minimum_basis}`. Native names must bind unique parsed actions. Demand is a quantity or null; minimum is 0..512 or null, with a source/assumption basis. Missing assignment criteria remain separate from otherwise computable capacity arithmetic. Labels are single-line, at most 120 characters.
- `resources`: each `{native_name,label}`, bound to a unique parsed part usage. A resource's type/name does not establish capability. Native aliases cannot count one identity twice in the question scope. Labels that collide use qualified native names.
- `alternatives`: each `{label,assignments,composition,concurrency_basis}`. Every selected alternative evaluates the entire declared function set. Assignments contain exactly `{function,resource,capability,capability_basis,capacity,rationale,rationale_basis}`. Capability is a declared `capable`, `incapable` or `unknown` statement; it is not a program-qualified implementation. Quantities are `{value,unit,basis}`. Nominal unit IDs must match exactly; there is no unit conversion or native ISQ dimensional-conformance claim. Numeric facts live in this analysis document; other native expressions/properties are not silently evaluated or substituted.
- `composition`: per-function `{method,basis}`. One capable provider uses its stated capacity. More than one requires explicit independent additive `sum` with a supplied basis; otherwise capacity is unknown/unsupported. No provider is chosen automatically. Other declared combination methods are unsupported, including when a loss leaves one provider. A declared incapable provider contributes zero; an unknown provider blocks a complete capacity result. Assigned resources, declared capable means and available capacity are distinct.
- `concurrency_basis`: source/assumption ID or null. When one remaining resource has multiple functions, absence keeps the affected capacity answers unknown. Supplying it explicitly declares, conditionally, that the per-function rates are simultaneously attainable; it does not verify a resource budget or scheduling. The answer makes that assumption visible. Use actual evidence or an explicitly new hypothetical assumption, never a misleading citation to turn a gap into a pass.

## Computed meaning and boundaries

The program counts distinct remaining assignments against unchanged declared minima. Separately, it sums supported compatible declared capacity contributions under explicit composition assumptions and compares each function with its own workload. Exact margin identifies shortfall/headroom. Assignment gaps have their own unchanged minimum, gap and next decision even when capacity passes; confirming rates cannot close an assignment obligation. Both failures retain both decisions. A pipeline's stage rates are checked separately; they are not summed across functions. The result does not simulate a queue or prove system throughput, recovery, timing, quality, safety or operational continuity.

Results preserve received hypotheses/input paths, actual model hash, source expected/observed hashes, quoted/classified evidence, parsed names, the structured model view, counts, assumptions, quantities, findings and selected alternatives. `pass`, `fail`, `unknown`, `unsupported` and `error` refer only to this conditional declared scope. Incomplete/changed/errored inputs cannot produce an overall successful review. Required review and engineering acceptance remain not evaluated; hashes protect no independent runner or engineer decision.

The local operation catalog truthfully names `inquiry.answer`, its input and source scope. It is distinct from the two existing model-selected foundation executors. Draft emission is listed separately. The same-user CLI is not a protected verification authority.

## Original demonstrations and evaluation

[Software](../examples/inquiry/software.sysml): fallback 8 jobs/minute against 12, a 16-rate candidate, and an unqualified 24-rate proposal. [Hardware](../examples/inquiry/hardware.sysml): two-channel remaining coverage against four, a four-channel spare, and unknown signal compatibility. [Physical process](../examples/inquiry/physical-process.sysml): assembly 4 versus 6 kits/hour while packing 8 versus 6; a dedicated 8/8 candidate; a shared worker with no concurrent budget. The adjacent source briefs state all invented assumptions and limits. These examples assess generality of the workflow, not actual software/hardware/process performance.

Assess correctness with independent arithmetic/source/name controls and actual launchers. Assess clarity with named work/means, explicit workload/unit, distinct assignment and capacity outcomes, visible assumptions, and specific next decisions. Record actual helper/CLI actions and wall times for effort; this is machine workflow effort, not observed human effort. Automated reader tasks do not establish human acceptance. Actual model-context/token savings remain unverified; bytes, lines, actions and tests are not tokens.
