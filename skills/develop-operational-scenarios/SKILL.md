---
name: develop-operational-scenarios
description: Help a systems engineer elicit, investigate, draft, or revise a particular operational scenario or set, including normal operation, exceptions, and lifecycle activities.
---

Assist with the engineer's requested scenario question or set. Reuse known needs, actors, boundaries, constraints, and decisions. A clarification, observation plan, or rough sequence can be the whole task. An exception can be explored directly.

For engineering claims and implementation, use [meaning and context](../../docs/meaning-context.md)
before drafting and when reviewing the actual output.

For changes with several dependent outputs, difficult check failures, or review handoffs, read [planning, diagnosis and review](references/work-review.md) and apply the relevant section. Keep small edits and discussion direct. The user's explicit instructions take precedence over skill guidance. Preserve failed findings during repair and reconcile delivered artifacts and current check evidence with the requested scope before claiming completion.

When multiple engineering skills are requested, apply those skills to one shared SysML model or explicitly imported files with common definitions and IDs. Run the draft-shape checks for each requested skill; concept plus scenario work does not require a full CONOPS. Accept natural skill names and handle files, SysML syntax, and commands for the engineer.

Read supplied raw material in place. Keep raw source and private annotations out of Git and generated model/test reports; retain concise derived statements and source references needed for review. Keep user-specific models and reports in the selected project's ignored/private work directory (this repository: `work/` on `/workspace`), outside an installed plugin's directory, and inspect Git status before any commit. If raw material is already tracked, surface that fact instead of silently copying or publishing it.

The engineer directs scope, interpretation, accepted assumptions, and success criteria. Prepare evidence, examples, alternatives, and recommendations. Preserve prior decisions and differing stakeholder perspectives. Elicit missing intent with targeted questions or a concrete sequence when it affects the current decision. Continue independent work with explicit unknowns; routine edits and checks need no confirmation. Mark inferred needs, new requirements, and thresholds as proposals with their basis.

Use these activities where the current question needs them. For a concept handoff, carry its question, relevant existing IDs, actors, trigger, intended outcome and assumptions; keep standalone entry points equally usable.

1. Establish the need, setting, actors, trigger, and observable outcome to the depth needed. Use supplied notes with their linked passages. When framing is unsettled, distinguish the reported situation, desired change, possible explanation and proposed solution. Investigate competing explanations only if they would change the design; do not invent stakeholder input or reopen settled framing. Use existing evidence or prepare focused elicitation, observation or a rough prototype where understanding is weak. Execute external investigation only within authorization. A generated scenario is a hypothesis, not an observed workflow.
2. Draft or revise ordered exchanges across the system boundary. Keep implementation open and preserve requested prototype fidelity. For fresh exploration, begin with a useful simple normal case before adding relevant complexity.
3. Run the available program checks. Investigate reported gaps, unclear intent, and unsupported assumptions. For a consequential investigation, connect the uncertainty to its affected decision, evidence sought and findings that would support or reconsider it. Reuse question, evidence and decision records when recording the work; qualitative findings need no invented threshold. Prepare evaluation data, environments, and stakeholder feedback appropriate to the current question. Qualitative realism and stakeholder intent require evidence or engineer judgment.
4. Return what was learned, affected assumptions and relevant IDs, decisions retained or proposed for reconsideration, and any next engineer decision. Explain why to revisit the affected concept explanation, outcome, boundary, function, means or evaluation method as well as the scenario; preserve accepted scope. Stop at that work unit; additional scenarios and overall CONOPS integration are separate scope choices. Omit filler and repeated questionnaires.

For a scenario question involving human tasks or human/automation allocation, use the [shared human-task workflow](../../docs/human-task-review.md) when useful. Keep task facts in the same native model and select relevant facts in the project's concept-review scope. Inspect normal, peak, absence or recovery contexts as applicable; do not require all four universally. Run the reused concept-review helper for that selected task scope alongside this skill's scenario shape check. Keep proposals, reported observations, unknowns and actual workload/competence evidence distinct; no staffing verdict or executable schedule follows from the task register. Scenario-only discussion and other scenario work remain independently usable without a concept scope.

When common behavior or conditional additions matter, use [use-case refinement](references/use-case-refinement.md)
to distinguish required included behavior from an extension at a selected point.
For enabling, control/object flows, forks/joins, termination or correspondence to
functions, use [activity and function review](references/activity-review.md).
Keep these reviews tied to the same scenario/model IDs. Select executable
semantics explicitly: include/extend execution and general concurrent activity
token semantics remain unsupported; native parsing and narrative order cannot
establish them.

Apply concept, CONOPS or scenario draft-shape checks to the requested engineering artifact. A separately scoped verification harness uses its compilation and evidence checks; do not invent concept content to make a harness satisfy an unrelated draft shape.

Use controlled English throughout authored engineering text. Apply the project’s selected terms and rules during drafting through [check-engineering-language](../check-engineering-language/SKILL.md); the normal `check` command enforces a sibling `.english.json` profile. Preserve source quotations, notes, identifiers and literal labels. Unresolved selected violations remain nonconforming.

For evidence-based engineering claims, use the [engineering terminology and standards basis](../../docs/engineering-terminology.md): distinguish needs, requirements, implementation proposals, verification and validation, and state applicability. For a requested local prototype, use the [prototype-verification workflow](../../docs/prototype-evaluation.md) when it answers the current question. Capture executed transactions and observation definitions; run the existing monitor against a separately retained obligation set. Keep authored traces, prototype observations, operational evidence and acceptance distinct. Missing evidence or unsupported behavior cannot satisfy a selected required check. Full ISO conformity is a separate, unevaluated claim; ordinary drafting does not require a full life-cycle dossier.

When a question needs exact calculations, algebraic identities or function/flow checks, read [bounded engineering analysis](../../docs/engineering-analysis.md) and run the selected `analyze` command. Link its findings to the affected model IDs; preserve declared units, assumptions and required scope.

Computed checks require a local execution environment. The shared SysML runtime is qualified on Linux with Python 3.10+ and Java/javac 21+; native Windows SysML is unsupported. When local execution is unavailable, continue useful qualitative work and identify checks as not run. For an installed plugin, set `CSE_SYSML_CACHE` to a private writable cache on the user's workspace before parser setup/checking; keep that value consistent across commands.

For new recorded work, maintain a SysML v2 `.sysml` model as the authoritative scenario artifact; respect discussion-only requests. Read [the SysML record guidance](references/sysml.md) and use [the parser-checked synthetic template](templates/default.sysml) when useful. Keep ordered interactions and unresolved outcomes explicit. Run `python3 <skill-dir>/scripts/cse.py check <model>.sysml --syntax-only --kind scenario` after edits; this launcher resolves the shared engine regardless of the current directory. Compile designated CSE clauses with its `check` command and run `--review` only when independent scope and supplied evidence exist. A narrative use case is not an executable step program.

When a supported sampled requirement is present, run `python3 <skill-dir>/scripts/cse.py testgen <model>.sysml` as part of local draft evaluation and save the synthetic pass/fail variable-influence pairs in the evidence record. Show the pairs directly when the user requests test analysis. If none is present, say what remains qualitative or unsupported without inventing a threshold. Report uncovered variables and search limits; generated tests are not observed behavior evidence or FLIP coverage.

Return the requested engineering view from the shared model, with stable IDs and its revision. For documents, manuals or drawing sets, use [technical document guidance](../../docs/technical-documents.md). Keep detailed check findings and test pairs in linked evidence; include the scope, assumptions and unresolved items needed to read the document correctly. Summarize actual check outcomes briefly in the handoff. Preserve the distinction between parser acceptance, compiled clauses, synthetic tests and supplied behavior evidence.

For an existing `scenarios.json` or explicit version-1 workflow, read [the legacy record contract](references/record.md), run `python <skill-dir>/scripts/conops.py check <record> --scenario <ID>`, and use its `view`, `diff`, and `--review` modes as appropriate. Do not implicitly convert legacy prose into guards or effects. Read program findings, repair within scope, and rerun. Preserve accepted meanings and review scope; changing either is an engineer decision. Use program results for computable claims, without substituting an LLM verdict. Execute scripts without loading their source. Read [provenance](references/notes.md) when explaining or revising the method.

For a separately authored version-2 finite model, run `python3 <skill-dir>/scripts/cse.py finite <model> --scenario <ID> --review` when its guard/effect semantics are explicitly supported. Scenario work remains independently invocable through this skill's own version-1 helper. Do not infer executable steps from version-1 prose or treat a local verifier pass as engineer acceptance.

For a behavior claim, use the [supported analysis correspondence](../../docs/behavior-review.md) to select an existing check. Keep narrative order/entry/completion documentary unless an explicit supported contract and evidence are supplied. A native parse or a path to completion cannot establish all-schedule progress or general concurrent SysML execution.

For requested function trees or sequences, use the documentary view contract in [SysML guidance](references/sysml.md). For user interactions or operational handoffs, use [connected interaction walkthroughs](../../docs/interaction-walkthroughs.md); retain user feedback before expanding the design.
