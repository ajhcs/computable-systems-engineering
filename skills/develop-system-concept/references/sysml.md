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
SysML or generated reports. In this repository, place user-specific models and
reports under the ignored `work/` directory or an approved private location on
`/workspace`; inspect Git status before committing. Tracked examples use only
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
`runtime` command prints the runtime root and profile location. Copying only a
skill folder preserves its legacy helper, but cannot install the shared engine.

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

For an existing version-1 JSON record or an explicit legacy request, read
`references/record.md` and use its original helper. Do not silently translate
its prose into executable SysML constraints. Reconcile any migration with the
engineer and record unsupported or lost meaning.
