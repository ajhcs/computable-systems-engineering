# SysML v2 record and checks

For new recorded work, maintain one authoritative `.sysml` model with a stable package namespace and short IDs. Reuse explicit imports when the model spans files. The skill's `templates/default.sysml` is a synthetic starting point. Replace its content with known project facts and labeled proposals. Keep raw sources and private annotations in the project workspace and retain concise source references in the model and reports. If raw material is already tracked, surface it before committing or publishing.

Use native parts and interfaces for architecture, concerns for stakeholder needs, actions and use cases for behavior, and requirements for actual obligations. Keep narrative steps, assumptions, questions and rationale documentary unless an explicit supported representation exists. The engineer decides proposed guards, allocations, effects, applicability and thresholds. Use the [terminology and standards basis](../../../docs/engineering-terminology.md) for engineering claims and preserve project terminology, quotations and literal labels.

## Run the applicable checks

Use `python3 <skill-dir>/scripts/cse.py` from the full checkout or plugin. The launcher follows the real skill path. Its `runtime` command prints the runtime, profile and parser-cache paths. A copied skill folder retains its legacy helper. The native launcher needs the shared engine.

Native checking is qualified on Linux with Python 3.10+ and Java/javac 21+. Use a private writable `CSE_SYSML_CACHE` outside the installed plugin. Keep it consistent across setup and checks. A source checkout defaults to `<runtime>/.cache/sysml`. Install the pinned parser with `cse.py install-parser` when needed within the task's authority. Help with model files and commands. If the runtime is unavailable, report which checks are unrun and continue useful draft work.

- **Native draft shape.** Run `cse.py check MODEL.sysml --syntax-only --kind KIND` after edits. Supply every required native file and keep short IDs unique across that set. Use the kind for each requested drafting artifact (`concept`, `conops` or `scenario`). Architecture uses `--syntax-only` without a kind. Concept plus scenario checks can run on one model. A separately scoped verification harness uses its own compilation and review without added drafting content.
- **Supported clauses.** Use the [native profile](../../../docs/sysml-v2-profile.md) for `cseClock`, `cseSource`, and the supported sampled, quantity and correlated event semantics. Compile designated clauses with `cse.py check MODEL.sysml`. Apply the project’s sibling `.english.json` profile when supplied.
- **Synthetic test generation.** For a supported sampled requirement, run `cse.py testgen MODEL.sysml --output TESTS.json` and retain the pass/fail variable-influence pairs with the evidence. Show the pairs when test analysis is requested. Inspect each clause result and retain supported pairs when another clause makes the overall result unsupported. Report uncovered variables and search limits. Add `--manifest MANIFEST.json` only when independently retained scope exists. If no supported sampled requirement exists, describe the remaining qualitative or unsupported work without supplying a threshold. The [generation contract](../../../docs/variable-influence-tests.md) defines its coverage. Pairs are synthetic and do not establish observed behavior or FLIP coverage.
- **Required review of supplied evidence.** Run `cse.py check MODEL.sysml --manifest MANIFEST.json --evidence EVIDENCE.json --review` with independent scope and evidence. Keep that scope intact across draft changes. Use [behavior review](../../../docs/behavior-review.md) to select the check for the actual claim. For an already authored [finite verifier model](../../../docs/verifier-v2.md) with supported typed predicates and effects, run `cse.py finite MODEL.json --manifest RETAINED_SCOPE.json --review` when an independent manifest exists. For draft exploration without one, run the selected finite check and describe its candidate-local scope. Use `--scenario ID` for a focused draft check when it covers the selected question. Preserve the full retained scope for a required review. Finite inputs are authored separately from documentary prose.
- **Legacy records.** For explicit version-1 work, use the skill's [record contract](record.md) and its original helper. Keep legacy prose documentary. Review any migration with the engineer and record lost or unsupported meaning.

Use `cse.py view MODEL.sysml --id ID` for parsed context, or [assemble governing definitions and evidence](../../../docs/meaning-context.md#retrieve-an-assembled-view) for a focused question. Use `cse.py diff --before OLD.sysml --after NEW.sysml` for structural and documentary changes. Review consequential changes with the engineer.

For recorded concept work, also apply the [project-tailored coverage review](../../../docs/concept-review.md) to the separately retained scope. Independent scenario and CONOPS drafting can run their own checks.

Return the requested view with its model revision and IDs. Link detailed findings and test pairs. State which evidence supports draft form, compiled clauses, synthetic examples, supplied observations and acceptance. A failed, unsupported or unrun required check remains unresolved. See [technical document guidance](../../../docs/technical-documents.md) for documents and drawings.

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

## Current configuration reconciliation

For an explicitly selected configuration, use the optional
[configuration review](../../../docs/configuration-review.md). Retain the engineer's
configuration scope separately from the candidate, supply every required native
model file explicitly, and check the selected root and qualified role identities.
The `configuration-review` command is available through each drafting launcher.
Its derived current view reports the declared selection and open alternatives;
it does not select products, update accepted meaning, prove installed quantities,
or establish interface behavior. Unsupported selected obligations remain unresolved.

For a selected connected context, opt in to `configuration-1.1` and retain explicit
external peer and native connection obligations. The same command derives a
current system view and checks a saved view against fresh native reconciliation;
see [connected system views](../../../docs/configuration-system-view.md).
The view presents supported native adjacency and selected ownership, with omitted
or unresolved facts visible. A connection/view result does not execute exchanges
or establish a vendor protocol, operational behavior or engineering acceptance.
