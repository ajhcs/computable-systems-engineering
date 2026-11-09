---
name: define-engineering-measures
description: Define or revise an engineering measure, its collection conditions and baseline meaning. Use for measurement dictionaries or changed metric definitions; use evidence planning for a broader evaluation plan.
---

Define the quantity needed for the engineer's question. Reuse existing measure
IDs, sources and accepted definitions. Ask only for consequential missing intent;
keep other gaps explicit. Do not supply targets, acceptance thresholds or modality.

For engineering claims and implementation, use [meaning and context](../../docs/meaning-context.md)
before drafting and when reviewing the actual output.

Read the [record contract](references/record-contract.md) when creating or checking
a definition. Keep formula, units, population, boundary, aggregation, exclusions,
window, sampling, conditions and uncertainty together in one versioned record.
Preserve nominal, ordinal, interval and ratio distinctions. Provide a concise human
view beside the typed record; a prose definition alone has no computed verdict.

Run `python3 <skill-dir>/scripts/measures.py check RECORD.json`. Repair reported
draft defects within accepted meaning and rerun. Unknown or unsupported fields
cannot pass a required definition check. The helper reuses bounded arithmetic
syntax and unit checks; it does not evaluate measurements or infer prose meaning.

For a revision, read [baseline and feedback](references/baseline-and-feedback.md).
Retain old and proposed files. Run `python3 <skill-dir>/scripts/measures.py compare BEFORE.json AFTER.json`.
Report changed meaning separately from labels and provenance metadata. Exact
definition equality does not establish statistical comparability of observations.
Present changed accepted meaning for engineer judgment before adoption.

When a discrepancy motivates a design change, link its question, corrective
action and follow-up measure without claiming causation. Use
[evidence planning](../plan-engineering-evidence/SKILL.md) for collection and
evaluation evidence, or the existing calculations helper for numeric evaluation.
For collected aligned data, read [observation computation](references/observation-validation.md)
to select interval scores, weighted summaries or conditional binomial checks.
Keep sources and private annotations outside public artifacts. Do not claim
physical validity, source truth or acceptance from a well-formed definition.
