# Human-task and function-allocation review

Priority 2 reuses the native SysML parser, documentary workflow identities and
allocations, optional allocation counts and the separate project review scope.
It adds explicit task facts, not a simulator, staffing algorithm or automatic
choice of people over automation. The engineer directs allocation and criteria.

## Drafting loop

Start with relevant scenarios and functions. Identify the tasks performing that
work and their human/automation participants. Distinguish roles that execute,
assist, monitor or authorize. Each participant needs an existing documentary
function allocation; assignment does not establish competence or availability.

Select facts needed for the question: purpose, entry, inputs, completion, skills,
equipment, procedure, duration, concurrency, interruption, recovery, training and
evaluation. No project must select every field. Inspect relevant normal, peak,
absence and recovery contexts without requiring all four for every project.
Keep active task time separate from waiting or simultaneous capacity. Narrative
conditions are not executable guards or schedules.

Run the normal concept review against the retained project scope. Repair missing
draft facts, retain unknowns, or propose consequential changes to the engineer.
Plan operator-based evaluation before claiming training, tasks or allocation work.
The assistant handles the files and commands.

## One authoritative model

Keep the existing `CSE-WORKFLOW/1.0` record and native definitions. A task is a
workflow `step` bound to a parsed action identity. Add exactly one documentation
block on a parsed concern in the same model:

```text
doc cseHumanTasks /*CSE-HUMAN-TASKS/1.0
{"version":"human-tasks-1.0","tasks":{...}}
*/
```

The named block is extracted from the same captured/native-checked snapshot as
the workflow. Task facts are documentary, not native execution, ISQ quantities,
clocks, guards or requirements. They cannot register executors or open paths/URLs.

`tasks` admits at most 64 rows. Its key is the workflow step ID. Each row has:

```json
{
  "function":"F_REVIEW","scenario":"S_NORMAL",
  "performers":[
    {"element":"R_CLERK","role":"execute","allocation":"human"},
    {"element":"R_APP","role":"assist","allocation":"automation"}
  ],
  "facts":{
    "entry":{"status":"proposed","text":"A request is available.","basis":"CASE","refs":[]},
    "duration":{"status":"unknown","text":"Active time is not measured.","basis":null,"refs":[],"value":null,"unit":null}
  }
}
```

Function/scenario/performer references retain their admitted workflow kinds.
Performers reference elements/systems; add a separate actor role for the same
native participant where an operational view needs it. Roles are execute, assist,
monitor, authorize; allocation classifications are human/automation. These are
declared roles, not capability or independence proofs.

Every fact has `status`, `text`, `basis`, `refs`. Status is proposed/reported/unknown;
basis references an existing supplied source, or is null while unresolved.
Reported facts need a source classified `reported_observation`. Matching bytes
establish attribution, not authentic measurement or correctness. Relabelling a
proposal cannot create evidence.

Every selected fact basis must also be supplied and checked through the project
scope and explicit source arguments. Merely declaring a source in model metadata
does not establish provenance; an unprovided basis leaves the task review unknown.

Equipment/procedure references identify modeled elements/systems. Evaluation
references identify existing evidence records targeted at this task, its function
or its scenario. Selected dependency fields need references, not only vague text.
Other references identify existing modeled context.

Duration additionally uses an exact nonnegative decimal-string value and unit
second/minute/hour, or nulls for unknowns. Floats, negatives and exponent strings
are refused; other unit tokens are unsupported. This profile does no arithmetic,
conversion or workload evaluation. Proposed durations are not throughput evidence.

## Project scope and findings

Use explicit `concept-review-1.1` or `concept-review-1.2` for task expectations;
select 1.2 when ownership expectations are also included. Existing 1.0 scopes
remain supported unchanged. The remaining scope fields retain their existing meanings.

```json
{
  "topic":"human_tasks","kind":"human_task","task":"T_NORMAL",
  "function":"F_REVIEW","scenario":"S_NORMAL",
  "performers":[
    {"element":"R_CLERK","role":"execute","allocation":"human"},
    {"element":"R_APP","role":"assist","allocation":"automation"}
  ],
  "fields":["entry","completion","skills","training","recovery","evaluation"]
}
```

The separate scope retains expected task context/responsibilities and selected
facts. Missing tasks/facts fail; explicitly unknown facts stay unknown. Missing
selected registers fail, unknown profiles are unsupported, malformed/duplicate
documents are errors. None can become a coverage pass. Incomplete drafting can
continue. A pass with proposed facts means selected planning documentation is
present; behavior, staffing adequacy and performance qualification stay unevaluated.
Do not narrow accepted scope as a routine repair.

Use `cse.py concept-review check ...` as before. The
[synthetic service-desk model](../examples/human-task-review/concept.sysml) covers
four proposed contexts with illustrative durations and unexecuted evaluation plans.

## Method sources and remaining investigation

Buede and Miller, *The Engineering Design of Systems: Models and Methods*, fourth
edition, pp. 213, 243–244, 255–256 supplies the procedure, allocation and activation/
completion direction. Pre-2000 supplements are:

- DoD, *MIL-HDBK-46855A*, 17 May 1999, §§4.1.1.1, 4.2.1.1.3, 4.2.1.3 and Appendix B,
  especially B.5.2.1 and B.5.3–B.5.5: task parameters, role allocation, training,
  degraded conditions, recovery and tailoring.
  [Official PDF](https://quicksearch.dla.mil/WMX/Default.aspx?token=185936),
  [official status](https://quicksearch.dla.mil/qsDocDetails.aspx?ident_number=201925).
  This canceled military handbook is historical methodology, not a current
  universal requirement or a claim of contractual applicability.
- NASA, *Systems Engineering Handbook*, June 1995, Appendix B.7.3, printed pp. 129–131:
  selective time-critical analysis and concurrent maintenance tasks.
  [Original edition](https://ocw.mit.edu/courses/16-892j-space-system-architecture-and-design-fall-2004/e5e9dea39ad9594ab73c4c56024bf659_nasasysenghbookpdf.pdf#page=141).
- NASA Human Performance Research Group, *NASA Task Load Index: Paper and Pencil
  Package*, 1986, §2.1, printed p. 2: obtain workload observations from participants.
  [Original](https://ntrs.nasa.gov/api/citations/20000021488/downloads/20000021488.pdf#page=8).
- National Research Council, *The Future of Air Traffic Control: Human Operators
  and Automation*, 1998, Chapter 1, pp. 12–16: allocate automation according to
  operational needs and assess human/automation interaction in context.
  [Publisher chapter](https://www.nationalacademies.org/read/6018/chapter/4).

Further work needs representative task times, skill/competence evaluation,
training transfer, interruption/error-recovery evidence, workload observations
and varying-demand capacity analysis. Reading supplies methods, not project
observations or acceptance criteria. NASA-TLX scoring is not implemented here.
Task-network simulation, fatigue and sleep/rest modeling remain excluded.
See the [bounded-use readiness plan](readiness-plan.md).
