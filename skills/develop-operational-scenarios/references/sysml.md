# SysML v2 default record

For new recorded work, keep an authoritative `.sysml` model. Begin from
`templates/default.sysml` when useful, but replace its synthetic content with
the current system's actual known facts and clearly labeled proposals. Keep a
stable package namespace and short IDs for reviewed elements. Reuse/import an
existing system model instead of creating a competing definition.
When multiple skills are requested, share definitions and short IDs across their
views; one file or an explicitly imported bundle is fine. Run the draft-shape
check for each requested kind. Concept plus scenario development needs
`--kind concept` and `--kind scenario`, without a complete CONOPS.
Keep supplied raw files and private annotations out of Git. Record concise
derived content and source references instead of copying source documents into
SysML or generated reports. Keep user-specific models and reports in the selected project's ignored/private
work directory, outside the installed plugin (this repository: `work/` on
`/workspace`); inspect Git status before committing. Tracked examples use only
synthetic material or small attributed public-source derivatives.

Use ordinary SysML elements for the information they actually represent:
parts and interfaces for the boundary and architecture, `concern` for a
stakeholder need, actions and use cases for behavior, and `requirement` for an
actual obligation. Documentation may hold the problem, alternatives, rationale,
assumptions, unanswered questions, and narrative steps; that text does not
become executable merely because SysML contains it. Never invent a guard,
threshold, effect, actor allocation, or accepted decision to make a checker
pass. The engineer resolves consequential meaning.

Use `python3 <skill-dir>/scripts/cse.py` as the installed entry point; it follows
the real skill path to the shared repository or complete plugin runtime. Its
`runtime` command prints the runtime root, profile and parser-cache locations. Copying only a
skill folder preserves its legacy helper, but cannot install the shared engine.

For installed copies, set `CSE_SYSML_CACHE` to a private writable directory on
the user's workspace and retain it for installation and every subsequent check.
It defaults to `<runtime>/.cache/sysml` for source checkouts; do not store user
models inside the installed plugin. The shared SysML runtime is qualified on
Linux and requires local Python 3.10+ and Java/javac 21+. Native Windows SysML
is unsupported. Without local execution, keep the model a draft and report
checks as not run.

Install the pinned parser once with
`python3 <skill-dir>/scripts/cse.py install-parser`, then run
`python3 <skill-dir>/scripts/cse.py check PATH.sysml --syntax-only --kind KIND` after edits,
with `KIND` set to `concept`, `conops`, or `scenario` for the current skill. A successful
syntax-only result means parser/validator acceptance for that file, not a
behavioral verdict. For an explicitly selected checkable requirement, read
`docs/sysml-v2-profile.md` under the runtime root and use its `cseClock`,
`cseSource`, and controlled text conventions. Compile designated clauses with
`cse.py check PATH.sysml` before generating tests. With independent scope and
supplied evidence, run `cse.py check PATH.sysml --manifest MANIFEST.json
--evidence EVIDENCE.json --review`. A required trace review needs independent manifest and
evidence files. If the shared checker is unavailable after copying this skill
folder alone, keep the model a draft and state that parser validation was not
run. Do not substitute a hand-written syntax guess for a parser result.
The assistant runs these local commands and installs the pinned parser when
needed; the engineer need not manage a terminal for an ordinary skill request.

When the system model spans files, pass every required `.sysml` file to the
shared checker; imports are resolved across the supplied set. Keep stable short
IDs unique across that set. The alpha checker supports bounded Boolean and
quantity observations and correlated event deadlines, but a successful shape
or syntax check alone does not verify an operational claim.

For a supported sampled requirement, run `python3 <skill-dir>/scripts/cse.py testgen
PATH.sysml --output TESTS.json` to inspect synthetic variable-influence
pass/fail pairs. Add `--manifest MANIFEST.json` only when an independent scope
file already exists; do not manufacture one from the draft to claim required
review. The test report is not observed evidence, does not satisfy `--review`,
and does not implement NASA FLIP coverage. Keep an uncovered variable as an
unresolved test-generation result, never as permission to remove the variable
or its requirement. See
`docs/variable-influence-tests.md` for the exact criterion and limits.

Use `python3 <skill-dir>/scripts/cse.py view PATH.sysml --id ID` for a parsed context
slice and `python3 <skill-dir>/scripts/cse.py diff --before OLD.sysml --after NEW.sysml`
to inspect structural and documentation changes. The diff reports conservative
directly affected elements; review consequential changes with the engineer.

Return readable views from the model, not a raw SysML dump as the sole result.
For a combined request, show the concept summary and the requested ordered
operational sequence, referencing the same IDs and model revision. Include
useful diagrams when relationships or sequencing need them. Report syntax,
compilation, synthetic test coverage, and supplied-evidence results separately;
explain unsupported constructs and qualitative content in plain language.

For recorded concept work, also follow the system-concept skill's
[project-tailored coverage review](../../../docs/concept-review.md). Its
`cse.py concept-review check` command uses a separately retained project scope
to detect omitted elements, responsibilities, interfaces and evaluation plans.
It supplements these native/behavior checks; it does not make independent
scenario or CONOPS work require a concept scope.

For an existing version-1 JSON record or an explicit legacy request, read
`references/record.md` and use its original helper. Do not silently translate
its prose into executable SysML constraints. Reconcile any migration with the
engineer and record unsupported or lost meaning.

## Requested function hierarchies and sequences

Functions express actions (verb-object naming recommended), while components
and actors identify entities. Assess that distinction semantically with the
engineer; no verb dictionary establishes action meaning. A function tree records
decomposition with an explicit level-0 root, levels, and parent links. Activity
diagrams represent control/object flow; sequence diagrams represent participants
and ordered meaningful exchanges. Do not substitute these views for one another.
Tailor requested levels, breadth/depth counts, and coverage to the actual task;
there are no universal mandatory counts. Record justified exceptions explicitly.
Require timing only when the task calls for it; modeled ranges need finite
nonnegative numeric min <= max, duration units, and a timing reference/basis.

The shared runtime's `docs/engineering-view-quality.md` defines optional
`doc cseViews` metadata (`CSE-VIEWS/1.0`) bound by exact qualified names to native
actions and part usages. It is a documentary view of the model, not native
ownership, decomposition, allocation, or executable behavior. For requested
levels/counts/coverage/timing, supply an explicit task profile:

```text
python3 <skill-dir>/scripts/cse.py check MODEL.sysml --syntax-only --view-profile PROFILE.json
```

Add the relevant `--kind` as before. The assistant maintains the model/profile,
runs these checks when those requested views are recorded, repairs ordinary
structural gaps, and reports remaining human judgments. A tree requires one
explicit level-0 root and consistent parent levels, without orphans, cycles, or
duplicate IDs. A sequence requires declared participants and ordered nonempty
exchanges; whether those messages are meaningful remains a human assessment.
Missing requested views/levels/coverage/timing cannot produce an overall pass.
A task profile may carry justified exceptions to its scope/count/timing gaps,
which are exposed in the report; rationale text does not authenticate approval.
Do not change accepted scope to make a check pass. Existing unannotated SysML and
legacy JSON checks preserve their prior semantics. State that those old checks
do not establish the new view-quality conditions; do not claim all existing
models were checked for them. See the shared runtime's
`examples/sysml/views/sample-handling.sysml` and `task-profile.json` for a neutral
synthetic example. Keep syntax, structure, semantic review, and behavior separate.


For source-grounded diagram work, use the [diagram-generation skill](../../generate-engineering-diagrams/SKILL.md) with an accepted model and its supporting evidence. Keep source versions and IDs, distinguish simplified derivatives, and report fidelity, parser and rendering checks separately from engineering acceptance.
