# Bounded queue analysis

Use `scripts/queueing.py` for a supplied finite FCFS workload or a conditional
stationary M/M/c calculation. Both use exact rational arithmetic and the existing
CSE input helpers. No new runtime dependency, random sampler or native behavior
interpreter is added. A computation pass does not validate its operating assumptions.

```sh
python3 scripts/queueing.py examples/queueing/service-pool.json --required Replay --required Stationary
python3 scripts/queueing.py examples/queueing/service-pool.json --details
```

The default report omits the full job trace. `--details` includes at most 512
scheduled jobs. The input file hash, canonical record hash and trace hash retain
identities; they do not establish accepted engineering meaning. Keep the model,
measure definitions, data and selected obligations in the project workspace.

## Record

`queue-analysis-1.0` contains exactly `version`, `id`, `revision`, `subject`,
`time_unit`, `job_unit` and `checks`. IDs use the existing engineering identifier
rule. `subject` is `{id, model_revision, basis}`; a null basis remains unknown.
The subject link is documentary and is not checked against a native model.
Units are explicit nominal identifiers. All times use `time_unit`; both arrival
and per-server service rates use `job_unit/time_unit`. No unit conversion occurs.

`checks` is a nonempty ID map. All authored checks run. Repeat `--required ID`
for independently selected obligations; missing IDs fail. An empty explicitly
selected scope is an error. Without this argument, completeness against external
obligations is unevaluated. No program chooses staffing or acceptance thresholds.

Each assumption is `{holds: true|false|null, basis: text|null}`. False applicability
returns unsupported; an unresolved value or basis returns unknown. Affirmative
declarations are not observations or proof of applicability. Unknown fields and
malformed inputs are rejected. Numeric values are exact integer, decimal or
rational strings, never code or binary floats.

## Finite FCFS replay

A `fcfs_replay` check contains exactly `kind`, `servers`, `window`, `jobs` and
`assumptions`. The window is `{start,end}` with `0 <= start < end`. Each job has
`{id,arrival,service}` with a unique ID, arrival within `[start,end)`, and
nonnegative service duration. Zero service is permitted. An empty workload has
no performance means and returns unknown.

Declare these assumptions: `empty_initial_system`, `unit_demand`,
`identical_servers`, `nonpreemptive`, and `complete_arrivals_in_window`.
The model has one FCFS queue, constant capacity and one slot per job. It has no
priorities, cancellation, abandonment, routed queues, failures or replenishment.
Do not silently flatten such behavior into this contract.

The recurrence is `start = max(arrival, earliest_free_slot)` and
`finish = start + service`. Arrival ties retain input-list order. Equal slot
availability uses the numeric slot index; indices are simulation slots, not
physical component allocations. A slot released at a time can be reused then.
Zero-duration jobs complete before the next tied job receives that slot.

The full supplied cohort is scheduled, including projected completion beyond
the window. Occupancy is clipped to the declared window. Queue area is the sum
of clipped waiting intervals; busy area is the sum of clipped service intervals.
Mean queue is queue area/window duration. Utilization is busy area divided by
servers times window duration. Idle tails and unfinished waiting are included.
Peak queue groups simultaneous changes and excludes zero-duration waiting.

The reported horizon state includes completions and grants exactly at `end`,
but arrivals exactly at `end` are excluded. Completed, active and waiting counts
partition supplied jobs. Full-cohort means include projected future service;
completed-job means use only jobs completed by the horizon and are null if none
completed. The latter can be biased by censoring. Neither is a steady-state
estimate or a new observed measurement. An arbitrary finite-window Little's Law
identity is not imposed.

## Conditional M/M/c

An `mmc` check contains exactly `kind`, `servers`, `arrival_rate`, `service_rate`
and `assumptions`. Service rate is **per server**. Arrival rate is nonnegative;
service rate is positive. Required assumptions are `poisson_arrivals`,
`exponential_service`, `independent_arrivals_and_services`, `identical_servers`,
`fcfs`, `infinite_queue`, `no_abandonment` and `stationary_rates`.

With arrival rate λ, service rate μ and c servers, define a = λ/μ and ρ = a/c.
A stationary distribution requires ρ < 1. Otherwise the calculation returns
`fail` with `queue_unstable`, not a finite waiting-time estimate.

The finite normalization is
`S = sum(a^n/n!, n=0..c-1)` and `T = a^c/(c!*(1-ρ))`.
Then `P0 = 1/(S+T)`, `P(wait) = T/(S+T)`,
`Wq = P(wait)/(c*μ-λ)`, `W = Wq+1/μ`, `Lq = λ*Wq`, and `L = λ*W`.
At zero arrivals, waiting/service times are the limiting values. The helper
reports utilization, empty/wait probabilities and means. It does not fit arrival
or service distributions, estimate tail percentiles, select capacity or model a
network. The finite replay does not establish any M/M/c assumption.

## Limits and evidence

Inputs are regular non-symlink UTF-8 JSON files up to 1 MiB, with unique keys and
no nonfinite values. Limits are 16 checks, 512 jobs per replay, 64 servers,
2,048 characters per text field, 80 characters per rational literal and 4,096
bits per rational numerator/denominator. Numeric exhaustion returns unknown;
malformed or oversized inputs return error. Required non-success never becomes
an overall pass. Exit codes are 0 for completed scoped computation, 1 for
non-success, and 2 for malformed input or operational error.

The implementation was written from the recurrence, finite interval integrals
and stationary normalization above. Source-informed components came from
[SimPM at `603f0997`](https://github.com/Project-SimPM/SimPM/tree/603f0997347f0fa224ee0920c4d5085b989afc96),
MIT: [waiting records and utilization](https://github.com/Project-SimPM/SimPM/blob/603f0997347f0fa224ee0920c4d5085b989afc96/src/simpm/des.py#L472-L587),
[FIFO request/grant/release](https://github.com/Project-SimPM/SimPM/blob/603f0997347f0fa224ee0920c4d5085b989afc96/src/simpm/des.py#L823-L918).
The M/M/c basis is the stationary birth/death balance in
[NPTEL's queueing lecture](https://archive.nptel.ac.in/content/storage2/courses/117103017/module3/lec2/1.html).
No upstream implementation was copied into the runtime.

The unmodified SimPM resource test passed. Three actual source smokes matched
hand-worked start times and exposed two measurement boundaries: utilization
ended at the last logged transition, and mean queue omitted a pending wait.
CSE checks idle tails and censored waits explicitly. Independent CSE tests use
hand calculations, a separate time-grid oracle, malformed/unsupported controls
and exact M/M/1 and M/M/2 values. The public fixture is synthetic; it contains no
NIST operating observations. Full routed pharmacy modeling remains separate work.
