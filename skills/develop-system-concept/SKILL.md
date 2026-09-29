---
name: develop-system-concept
description: Help a systems engineer investigate or develop a system concept by connecting the problem, desired outcomes, functions, alternatives, and feasibility evidence. Scenario-only and overall CONOPS work have separate skills.
---

Assist the engineer with the current concept question at the depth needed now. Start from existing work. Framing a need, investigating uncertainty, or comparing one aspect of alternatives can be the whole task; a complete proposal is optional.

The engineer directs scope, interpretation, priorities, accepted assumptions, tradeoffs, and selection. Prepare evidence, calculations, alternatives, and recommendations. Preserve settled decisions and differing stakeholder perspectives. Elicit missing intent with targeted questions or concrete examples when it affects the current decision. Continue independent work with explicit unknowns; routine edits and checks need no confirmation. Inferred needs, new requirements, and thresholds remain proposals with their basis; weights require actual preferences.

Use these activities as relevant to the current question and maturity:

- Investigate the present gap and desired outcome/timeframe. Use supplied notes with their linked passages; select existing evidence, focused elicitation, observation, or a rough prototype to resolve a particular uncertainty. Prepare external investigation for the engineer unless execution is authorized. Preserve requested prototype fidelity.
- Distinguish needs from proposed products while retaining explicit user constraints. Clarify terms, responsibilities, boundary, and essential functions before committing to components. Link functions to needs; coarse components, interfaces, and allocations are optional aids to assessment.
- Explore meaningful alternative approaches and compare them against stakeholder objectives and constraints, including people, integration, lifecycle effort, and uncertainty where relevant. Keep qualitative criteria. Use quantitative trade studies when inputs and preferences support them; no fixed alternative count is required.
- Test feasibility claims with appropriate calculations, evidence, prototypes, or simulations. Plan evaluation data, environments, and stakeholder feedback. Surface unsupported assumptions and conflicting constraints. Modification, further inquiry, and no selection remain possible outcomes.
- Incorporate feedback into affected earlier work. Return the useful change, material findings, and any next engineer decision. Stop at the requested boundary; omit filler and repeated questionnaires.

Reuse linked operational artifacts. Use available `$develop-operational-scenarios` or `$develop-conops` only when that work is needed. Concept exploration does not require a complete CONOPS.

Maintain `concept.json` when recording artifacts; respect discussion-only requests. Treat it as a working representation of the concept, with documents/diagrams as views. Read [the record contract](references/record.md) when editing. Keep drafts and qualitative unknowns usable; link operational records rather than copying them. Retrieve relevant IDs with `view`, inspect change impact with `diff`, and generate only requested views.

Run `python <skill-dir>/scripts/concept.py check <record>` after edits. Add `--concept <ID> --review` for a requested focused review or `--review` for the whole recorded set. Read program findings, repair within the agreed scope, and rerun. Stop repeated unsuccessful repair and surface the unresolved issue. Preserve accepted meanings and declared review scope; changing either is an engineer decision. Use program results for computable claims, without substituting an LLM verdict. Current checks cover structure/completeness, not arbitrary prose, feasibility, or acceptance; they do not enforce permissions. Execute scripts without loading their source. Read [provenance](references/notes.md) when explaining or revising the method.

For a separately authored version-2 finite model in this repository, run `python3 scripts/verify.py <model> --review` when typed predicates are explicitly supported. Keep the version-1 concept check for its own record; its qualitative assessments do not become formal predicates automatically. The local verifier is not an engineer acceptance channel or protected runner.
