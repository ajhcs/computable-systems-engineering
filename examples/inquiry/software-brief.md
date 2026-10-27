# Original hypothetical backup-processing brief
Question: Can fallback processing meet 12 jobs/minute if the primary worker is unavailable?
Work: Process jobs. Proposed workload: 12 jobs/minute. At least one assignment is required.
Existing arrangement: Primary worker (20 jobs/minute) and Backup worker (8 jobs/minute).
Candidate arrangement: Primary worker plus Larger backup worker (16 jobs/minute).
Unqualified arrangement: Experimental worker has a proposed rate of 24 jobs/minute; whether it can process these jobs is unknown.
For the first two arrangements, assume the named workers can perform this function, have independent additive rates, and meet the same operating conditions.
All rates, capability assertions, minima and the workload are invented design inputs, not measured service performance or accepted requirements.
No recovery timing, job correctness, queueing, failover mechanism or continuity has been demonstrated.
