---
name: develop-conops
description: Help a systems engineer investigate or develop a concept of operations by connecting stakeholder needs, boundaries, scenarios, and evaluation plans. Use develop-operational-scenarios for scenario-only work.
---

Assist the engineer with the requested CONOPS question at the depth needed now. Reuse existing work. An investigation, clarification, or small model change can be the whole task; a complete document is optional.

The engineer directs scope, interpretation, priorities, accepted assumptions, and success criteria. Prepare evidence, alternatives, calculations, and recommendations. Preserve settled decisions and differing stakeholder perspectives. Elicit missing intent with targeted questions or concrete examples when it affects the current decision. Continue independent work with explicit unknowns; routine edits and checks need no confirmation. Inferred needs and proposed requirements remain proposals until supported by the actual source or decision.

1. Connect the intended outcomes, stakeholder needs, boundary, and operating context. Use supplied notes with their linked passages. Select proportionate investigation: existing evidence, focused elicitation, observation, or a rough prototype that answers a specific uncertainty. Prepare external investigation for the engineer unless execution is authorized. Preserve requested prototype fidelity.
2. Reuse scenarios. When development is needed, use available `$develop-operational-scenarios` for the requested set. Keep scenario-only work in that skill.
3. Integrate relevant scenarios, external responsibilities, and evaluation plans. Expose disagreement, coverage gaps, and reasons for deferral. Plan needed data and environments; distinguish improvement goals from accepted thresholds and test claims with suitable programs or evidence.
4. Incorporate feedback into affected work. Return the useful change, material findings, and any next engineer decision. Stop at the requested boundary; omit filler and repeated questionnaires.

Maintain `conops.json`, or the existing operational record, when recording artifacts; respect discussion-only requests. Treat the record as the working model representation and documents/diagrams as views of it. Read [the record contract](references/record.md) when editing. The agent maintains the record; the engineer works naturally. Keep drafts and qualitative unknowns usable. Retrieve relevant IDs with `view`, inspect change impact with `diff`, and generate only requested views.

Run `python <skill-dir>/scripts/conops.py check <record>` after edits; add `--review` for the requested overall review. Read the program's output, repair within the agreed scope, and rerun. Stop repeated unsuccessful repair and surface the unresolved issue. Preserve accepted meanings and the declared review scope; changing either is an engineer decision. Use program results for computable claims, without substituting an LLM verdict. Current checks cover structure/completeness, not arbitrary prose, feasibility, or acceptance; they do not enforce permissions. Execute scripts without loading their source. Read [provenance](references/notes.md) when explaining or revising the method.
