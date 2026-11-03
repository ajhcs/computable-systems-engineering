---
name: analyze-queues
description: Analyze waiting and resource utilization for an explicit workload or a conditional M/M/c queue. Use for queueing questions with stated arrivals, service and capacity; preserve unknown assumptions and measurement boundaries.
---

Identify the queue, resource pool, operating question and model revision. Reuse
the engineer's measure definitions and data. Keep the service boundary, unit of
work, resource availability and collection window explicit. Missing rates or
distribution evidence remain unknown; do not infer them from a diagram.

Read the selected method in the [queue contract](../../docs/queue-analysis.md).
Use finite FCFS replay for supplied arrival/service times and one fixed pool.
Use M/M/c only with its explicit stationary arrival/service assumptions. The
two methods answer different questions; a replay does not validate the analytic
assumptions. General routing, priorities and shared multi-resource work need a
separately supported model.

Run `python3 <skill-dir>/scripts/queueing.py RECORD.json`, retaining independently
selected checks with repeatable `--required ID`. Use `--details` when job-level
timing explains a finding. The default output is compact. Repair ordinary draft
defects within accepted meaning and rerun; do not change assumptions or narrow
scope to obtain success.

Return waiting, queue occupancy and utilization with their window, population
and assumptions. Keep completed-job means separate from full-cohort projections;
retain unfinished work at the horizon. A simulation slot is not an allocated
person. Calculated capacity does not establish competence or staffing suitability.

Use [measure definitions](../define-engineering-measures/SKILL.md) to settle the
meaning of a metric and [evidence planning](../plan-engineering-evidence/SKILL.md)
for needed operating observations. Keep project inputs private. Unsupported,
incomplete and errored required checks remain unresolved. These computations
provide model results; the engineer owns applicability and design selection.
