---
name: analyze-queues
description: Compute waiting, queue occupancy and resource utilization for a supplied finite workload or conditional M/M/c model. Use when arrival, service and capacity assumptions can be made explicit.
---

Answer the waiting or utilization question for a stated queue and resource pool. Reuse the supplied arrivals, service data and accepted [measure definitions](../define-engineering-measures/SKILL.md). Identify the unit of work, capacity actually available, collection window and model revision. Leave missing rates or distribution evidence open.

Read the selected mode in the [queue contract](../../docs/queue-analysis.md). Use finite FCFS replay for supplied arrival and service times in one fixed pool. Use M/M/c for a conditional result under its stationary assumptions. General routing, priorities and shared multi-resource work need a supported model of their own.

Run `python3 <skill-dir>/scripts/queueing.py RECORD.json` with the independently retained checks as repeatable `--required ID` arguments. Use `--details` if individual job timings explain a finding. Repair input defects within accepted assumptions and rerun. Preserve the selected scope and identify unrun or unsupported checks.

Use [meaning and context](../../docs/meaning-context.md) to confirm the reported measures use the same window and population as the question. Report completed-job means and unfinished work at the horizon. Label full-cohort projections when used. A replay is evidence about the supplied workload. An analytic result is conditional on its model. Competence and staffing suitability require operating evidence. Use [evidence planning](../plan-engineering-evidence/SKILL.md) when collection would resolve a decision. Keep project inputs private.
