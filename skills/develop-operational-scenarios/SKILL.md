---
name: develop-operational-scenarios
description: Help a systems engineer elicit, investigate, draft, or revise a particular operational scenario or set, including normal operation, exceptions, and lifecycle activities.
---

Assist with the engineer's requested scenario question or set. Reuse known needs, actors, boundaries, constraints, and decisions. A clarification, observation plan, or rough sequence can be the whole task. An exception can be explored directly.

The engineer directs scope, interpretation, accepted assumptions, and success criteria. Prepare evidence, examples, alternatives, and recommendations. Preserve prior decisions and differing stakeholder perspectives. Elicit missing intent with targeted questions or a concrete sequence when it affects the current decision. Continue independent work with explicit unknowns; routine edits and checks need no confirmation. Mark inferred needs, new requirements, and thresholds as proposals with their basis.

1. Establish the need, setting, actors, trigger, and observable outcome to the depth needed. Use supplied notes with their linked passages. Where understanding is weak, investigate existing evidence or prepare focused elicitation, observation, or a rough prototype; execute external investigation only within authorization. A generated scenario is a hypothesis, not an observed workflow.
2. Draft or revise ordered exchanges across the system boundary. Keep implementation open and preserve requested prototype fidelity. For fresh exploration, begin with a useful simple normal case before adding relevant complexity.
3. Run the available program checks. Investigate reported gaps, unclear intent, and unsupported assumptions. Prepare evaluation data, environments, and stakeholder feedback appropriate to the current question. Qualitative realism and stakeholder intent require evidence or engineer judgment.
4. Incorporate feedback. Return the useful change, material findings, and any next engineer decision. Stop at that work unit; additional scenarios and overall CONOPS integration are separate scope choices. Omit filler and repeated questionnaires.

Maintain the existing operational record, or `scenarios.json` for standalone artifacts; respect discussion-only requests. Treat the record as the working model representation and human documents/diagrams as views. Read [the record contract](references/record.md) when editing. Keep drafts and qualitative unknowns usable. Use `view` to retrieve relevant IDs and `diff` for change impact; generate only requested views.

Run `python <skill-dir>/scripts/conops.py check <record> --scenario <ID>` after edits; repeat `--scenario` for a set and add `--review` for the requested review. Read the program's output, repair within the agreed scope, and rerun. Stop repeated unsuccessful repair and surface the unresolved issue. Preserve accepted meanings and declared review scope; changing either is an engineer decision. Use program results for computable claims, without substituting an LLM verdict. Current checks cover structure/completeness, not arbitrary prose, realism, or acceptance; they do not enforce permissions. Execute scripts without loading their source. Read [provenance](references/notes.md) when explaining or revising the method.
