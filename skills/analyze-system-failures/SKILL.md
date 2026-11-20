---
name: analyze-system-failures
description: Analyze an explicit Boolean fault tree, shared failure events or linked failure modes and effects analysis (FMEA). Use for bounded cut sets, conditional probabilities or record consistency.
---

Start with the failure question, boundary and source revision. Preserve event IDs and treat each repeated ID as the same event. Model shared causes explicitly. Leave unknown causes, effects, detection methods and probabilities open. Independence and mission assumptions need an authored basis.

Use the [record contract](references/record-contract.md) for bounded AND/OR logic and FMEA consistency. Standalone FMEA drafting can leave the event mapping unresolved. Run the checker when an authored event and top anchor exist.

```sh
python3 <skill-dir>/scripts/failure_analysis.py RECORD.json
```

Retain the independently selected checks using repeatable `--required` values from `fault_tree`, `probability` and `fmea`. Repair draft structure within accepted meaning and rerun. Unsupported gates, incomplete bases and exceeded bounds remain unresolved.

Review the findings against the actual fault or failure claims using [meaning and context](../../docs/meaning-context.md). Return supported minimal cuts, conditional probabilities or FMEA findings with their assumptions, limits and checked scope. Effects, detection effectiveness, severity and reliability in service require their own evidence. Keep records private and use [implementation evidence](../../docs/failure-analysis.md) when explaining qualification or comparing methods.
