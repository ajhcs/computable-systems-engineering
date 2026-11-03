---
name: analyze-system-failures
description: Analyze an explicit Boolean fault tree, shared failure events, or FMEA record consistency with bounded deterministic checks. Use for failure-analysis work; quantitative results require authored probabilities and independence and mission assumptions.
---

Identify the engineer's failure question and retain existing event IDs, source
revisions and intended boundary. Read the [record contract](references/record-contract.md)
before authoring or checking the separate analysis record. Keep unknown causes,
effects, probabilities and detection methods explicit; propose consequential
interpretations for engineer judgment.

For FMEA drafting without a fault-tree anchor, retain the draft and unknown event
mapping. The current checker needs an authored event/top anchor; do not invent
a tree to make a standalone FMEA draft pass.

Run `python3 <skill-dir>/scripts/failure_analysis.py RECORD.json`. Retain separately
selected checks with repeatable `--required fault_tree`, `--required probability`
and `--required fmea`. Repair draft structure within accepted meaning and rerun.
Return minimal cuts and conditional probabilities with the assumptions, limits
and completed scope. A repeated event ID denotes one event everywhere; model
shared causes explicitly. Never infer independence from separate component names.

The helper handles bounded AND/OR logic and record consistency. Unsupported gates,
incomplete bases and exceeded bounds cannot pass. FMEA completeness does not prove
effects, component existence or detection effectiveness. Do not invent severity
scores, infer omitted failure modes, rank risk automatically or present local
Boolean results as reliability validation or stakeholder acceptance.

Keep real project records private. Read [implementation and source evidence](../../docs/failure-analysis.md)
when explaining the method, upstream comparison or its qualification limits.
