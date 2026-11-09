---
name: develop-conops
description: Help a systems engineer investigate or develop a concept of operations by connecting stakeholder needs, boundaries, scenarios, and evaluation plans. Use develop-operational-scenarios for scenario-only work.
---

Assist the engineer with the requested CONOPS question at the depth needed now. Reuse existing work. An investigation, clarification, or small model change can be the whole task; a complete document is optional.

For engineering claims and implementation, use [meaning and context](../../docs/meaning-context.md)
before drafting and when reviewing the actual output.

For changes with several dependent outputs, difficult check failures, or review handoffs, read [planning, diagnosis and review](references/work-review.md) and apply the relevant section. Keep small edits and discussion direct. The user's explicit instructions take precedence over skill guidance. Preserve failed findings during repair and reconcile delivered artifacts and current check evidence with the requested scope before claiming completion.

When multiple engineering skills are requested, apply those skills to one shared SysML model or explicitly imported files with common definitions and IDs. Run the draft-shape checks for each requested skill. Accept natural skill names and handle files, SysML syntax, and commands for the engineer. Read supplied raw material in place; keep raw source and private annotations out of Git and generated model/test reports. Retain concise derived statements and source references needed for review. Keep user-specific models and reports in the selected project's ignored/private work directory (this repository: `work/` on `/workspace`), outside an installed plugin's directory, and inspect Git status before any commit. Surface any raw material already tracked in Git.

The engineer directs scope, interpretation, priorities, accepted assumptions, and success criteria. Prepare evidence, alternatives, calculations, and recommendations. Preserve settled decisions and differing stakeholder perspectives. Elicit missing intent with targeted questions or concrete examples when it affects the current decision. Continue independent work with explicit unknowns; routine edits and checks need no confirmation. Inferred needs and proposed requirements remain proposals until supported by the actual source or decision.

When goals, obligations or successive increments need different treatment, read
[goals, obligations and increments](references/iteration-and-rationale.md).
Use its decision-rationale guidance for consequential choices, retaining the
information available at the decision revision and a reconsideration trigger.
For a focused evaluation plan, use [plan-engineering-evidence](../plan-engineering-evidence/SKILL.md);
verification of requirements remains separate from validation of intended use.

Use these activities where the current question needs them; a handoff does not restart settled work.

1. Connect the intended outcomes, stakeholder needs, boundary, and operating context. Use supplied notes with their linked passages. If framing is unsettled, separate the reported situation, desired change, possible explanation and proposed solution; retain competing explanations only when they affect the choice. Select proportionate investigation: existing evidence, focused elicitation, observation or a rough prototype. Identify the uncertainty, affected decision, evidence sought and findings that would support or reconsider it. Prepare external investigation for the engineer unless execution is authorized. Preserve requested prototype fidelity.
2. Reuse scenarios. When development is needed, carry the question, relevant existing IDs, actors, trigger, intended outcome and assumptions to available `$develop-operational-scenarios` for the requested set. Keep scenario-only work in that skill.
3. Integrate relevant scenarios, external responsibilities, and evaluation plans. Expose disagreement, coverage gaps, and reasons for deferral. Plan needed data and environments; distinguish improvement goals from accepted thresholds and test claims with suitable programs or evidence.
4. Feed findings back to the affected explanation, outcome, boundary, functions, means, scenarios or evaluation method. State the reason and return point, affected assumptions, and decisions retained or proposed for reconsideration. Reuse existing question, evidence and decision records when recording the work; preserve accepted scope and keep consequential changes as proposals. Return the useful change, material findings, and any next engineer decision. Stop at the requested boundary; omit filler and repeated questionnaires.

Apply concept, CONOPS or scenario draft-shape checks to the requested engineering artifact. A separately scoped verification harness uses its compilation and evidence checks; do not invent concept content to make a harness satisfy an unrelated draft shape.

Use controlled English throughout authored engineering text. Apply the project’s selected terms and rules during drafting through [check-engineering-language](../check-engineering-language/SKILL.md); the normal `check` command enforces a sibling `.english.json` profile. Preserve source quotations, notes, identifiers and literal labels. Unresolved selected violations remain nonconforming.

For evidence-based engineering claims, use the [engineering terminology and standards basis](../../docs/engineering-terminology.md): distinguish needs, requirements, implementation proposals, verification and validation, and state applicability. For a requested local prototype, use the [prototype-verification workflow](../../docs/prototype-evaluation.md) when it answers the current question. Capture executed transactions and observation definitions; run the existing monitor against a separately retained obligation set. Keep authored traces, prototype observations, operational evidence and acceptance distinct. Missing evidence or unsupported behavior cannot satisfy a selected required check. Full ISO conformity is a separate, unevaluated claim; ordinary drafting does not require a full life-cycle dossier.

When a question needs exact calculations, algebraic identities or function/flow checks, read [bounded engineering analysis](../../docs/engineering-analysis.md) and run the selected `analyze` command. Link its findings to the affected model IDs; preserve declared units, assumptions and required scope.

Computed checks require a local execution environment. The shared SysML runtime is qualified on Linux with Python 3.10+ and Java/javac 21+; native Windows SysML is unsupported. When local execution is unavailable, continue useful qualitative work and identify checks as not run. For an installed plugin, set `CSE_SYSML_CACHE` to a private writable cache on the user's workspace before parser setup/checking; keep that value consistent across commands.

For new recorded work, maintain a SysML v2 `.sysml` model as the authoritative CONOPS artifact; respect discussion-only requests. Read [the SysML record guidance](references/sysml.md) and use [the parser-checked synthetic template](templates/default.sysml) when useful. Keep stakeholder concerns, operating modes, use cases, and qualitative uncertainties distinct. Run `python3 <skill-dir>/scripts/cse.py check <model>.sysml --syntax-only --kind conops` after edits; this launcher resolves the shared engine regardless of the current directory. Compile designated CSE clauses with its `check` command and run `--review` only when independent scope and supplied evidence exist. Narrative alone supplies no executable guard or effect.

When a supported sampled requirement is present, run `python3 <skill-dir>/scripts/cse.py testgen <model>.sysml` as part of local draft evaluation and save the synthetic pass/fail variable-influence pairs in the evidence record. Show the pairs directly when the user requests test analysis. If none is present, say what remains qualitative or unsupported without inventing a threshold. Report uncovered variables and search limits; generated tests are not observed behavior evidence or FLIP coverage.

Return the requested engineering view from the shared model, with stable IDs and its revision. For documents, manuals or drawing sets, use [technical document guidance](../../docs/technical-documents.md). Keep detailed check findings and test pairs in linked evidence; include the scope, assumptions and unresolved items needed to read the document correctly. Summarize actual check outcomes briefly in the handoff. Preserve the distinction between parser acceptance, compiled clauses, synthetic tests and supplied behavior evidence.

For an existing `conops.json` or explicit version-1 workflow, read [the legacy record contract](references/record.md), run `python <skill-dir>/scripts/conops.py check <record>`, and use its focused `view`, `diff`, or `--review` modes as appropriate. Do not implicitly convert legacy prose into SysML behavior. Read the program's output, repair within scope, and rerun. Preserve accepted meanings and review scope; changing either is an engineer decision. Use program results for computable claims, without substituting an LLM verdict. Execute scripts without loading their source. Read [provenance](references/notes.md) when explaining or revising the method.

For a separately authored version-2 finite model, run `python3 <skill-dir>/scripts/cse.py finite <model> --review` when logical checks are requested and supported. Keep the version-1 operational record and its helper check; do not translate prose steps into executable effects silently. The version-2 CLI is a local draft checker, not an engineer acceptance channel or protected runner.

For requested function trees or sequences, use the documentary view contract in [SysML guidance](references/sysml.md). For user interactions or operational handoffs, use [connected interaction walkthroughs](../../docs/interaction-walkthroughs.md); retain user feedback before expanding the design.
