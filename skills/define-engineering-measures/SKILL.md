---
name: define-engineering-measures
description: Define or revise an engineering measure and its collection conditions. Use for measurement dictionaries, changed metric definitions or baseline comparability.
---

Define the quantity the engineer needs for the current decision. Reuse existing measure IDs, sources and accepted definitions. Keep unestablished targets or acceptance thresholds open for the engineer.

Use the [record contract](references/record-contract.md) to put the formula, scale type, units, population, boundary, aggregation, exclusions, window, sampling, conditions and uncertainty in a versioned record. Keep a readable definition beside it. Review both against the project's [defined meaning](../../docs/meaning-context.md).

Run `python3 <skill-dir>/scripts/measures.py check RECORD.json` for typed syntax and unit checks. Repair draft defects within accepted meaning and rerun. Unknown or unsupported fields leave a required check unresolved.

For changed definitions, use [baseline and feedback](references/baseline-and-feedback.md). Retain both revisions and run `python3 <skill-dir>/scripts/measures.py compare BEFORE.json AFTER.json`. Explain changed measurement meaning and how it affects the baseline. Keep observed comparability open where the collection evidence does not establish it. The engineer decides whether to adopt changed meaning.

For aligned observations, use the [observation computation](references/observation-validation.md) for supported interval scores, weighted summaries or conditional binomial checks. Use [evidence planning](../plan-engineering-evidence/SKILL.md) for new collection and [engineering analysis](../../docs/engineering-analysis.md) for calculations. Link discrepancies to the design question, proposed action and follow-up measure without inferring causation.

Deliver a definition another person can apply to the same work and identify exclusions and unknowns. Include the check result and, for revisions, the baseline consequence. A definition check covers the supplied formula and declared units. Collection validity and acceptance need their own evidence. Keep source observations and annotations private.
