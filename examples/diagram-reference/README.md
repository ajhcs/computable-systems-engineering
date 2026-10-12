# Matched diagram references

**Rejected experimental draft, 2026-10-01.** Cole rejected this source type. This material is preserved as historical evidence, not approved professional references, current selection guidance, or publication/rollout material. See [draft status](../../docs/diagram-reference-draft-status.md). Wait for genuine attributable project bundles before adaptation.

## Historical draft content

Four original examples pair a readable image, explanation, formal SysML v2 model, and editable draw.io view. Start with the row matching the modeling question; do not load the entire pack.

| Question | Image | Formal model | Editable view | Why this reference |
|---|---|---|---|---|
| What crosses the boundary, in which direction? | [Context](rendered/01-context.png) | [context.sysml](context.sysml) | [draw.io](rendered/01-context.drawio) | Two typed items retain their separate directions. A black-box view leaves internals open. |
| What happens in the selected order? | [Ordered actions](rendered/02-actions.png) | [ordered-actions.sysml](ordered-actions.sysml) | [draw.io](rendered/02-actions.drawio) | Native action successions teach order without invented branches, durations, or allocations. |
| What exactly does a supported obligation check? | [Deadline](rendered/03-deadline.png) | [timed-obligation.sysml](timed-obligation.sysml) | [draw.io](rendered/03-deadline.drawio) | One binding and one inclusive deadline yield different deterministic verdicts. |
| How does a real repository produce its verdicts? | [Runtime](rendered/04-runtime.png) | [runtime.sysml](runtime.sysml) | [draw.io](rendered/04-runtime.drawio) | Actual launcher, CLI, adapter, pilot, and language-checker call paths remain separate. |

The first two images are custom views of formal SysML v2 item flows and action successions. They use textual declaration labels and simplified shapes; they are **not claims of conformance to the complete standard graphical notation**. The timing and runtime images are illustrative graphs. Their corresponding .sysml files are formal, parser-validated models; a formal source does not turn every rendered graph into a formal SysML diagram. Draw.io is an editable presentation format, not a lossless SysML model interchange.

## Read the pairs

**Context.** borrower : Borrower is external to system : ToolLibrary. requestFlow carries Request from borrower.request to system.request; allocationFlow carries Allocation in the opposite direction through assignedTool. The word allocation is reserved in the pinned parser, so the feature has a different name from its item type. These flow declarations establish typed source/target structure, not guaranteed delivery or a timed service. The concern N_ACCESS records a need and supplies no measurable obligation.

**Ordered actions.** BorrowAvailable starts, receives a request, assesses availability, records allocation, and ends. UC_AVAILABLE scopes this to the available-tool scenario. Successions give control order; arrows do not carry data. The unavailable outcome is explicitly omitted, so no diamond, failure path, actor allocation, or duration has been manufactured. Parser acceptance does not establish executable behavior support in the CSE adapter.

**Deadline.** R_RECORD / responseTime binds unit to system : ToolLibrary, whose request is an input Boolean and recorded is an output Boolean. With a one-second clock, the request rises at sample 1. Recording at sample 3 meets the inclusive two-second deadline. Remaining false through sample 3 fails. A sustained true request does not retrigger this clause. [The manifest](synthetic-manifest.json) defines this teaching fixture's scope; [pass](synthetic-pass.json) and [fail](synthetic-fail.json) are complete synthetic evidence bound to the model hash. They are not observed implementation evidence or a real engineer's approved threshold.

**Runtime.** The structural model groups abstract runtime parts. The arrows are documented code dependencies, not native SysML connections or item flows. The skill launcher resolves the runtime and invokes scripts/sysml.py, which calls check_sysml. The adapter invokes SysmlBridge in the Java pilot, compiles supported CSE documentation, and calls check_document in verifier/language.py. Syntax-only returns before behavior computation. Code anchors and file hashes in [the index](rendered/index.json) tie this abstraction to inspected repository code at the recorded baseline. This is a representative repo case; it does not audit other projects.

## Regenerate and check

From the repository with the existing Java 21+ parser runtime selected:

python3 scripts/diagram_references.py

This fixed-fixture generator validates all four models with the pinned OMG pilot (2025-09, kernel 0.52.0), checks selected native constructs and static code anchors, runs the synthetic pass/fail reviews, and emits one geometry into SVG and draw.io. It rejects changes outside its expected teaching contracts; it is not a general exporter or semantic-equivalence prover. SVG remains available for crisp scaling.

Optional browser screenshots use node scripts/render_diagram_references.cjs. Use --check to compare freshly rendered PNG bytes against the saved baseline without overwriting it; regeneration without --check is explicit. The saved receipt also binds PNG and SVG hashes. Supply installed Playwright via CSE_PLAYWRIGHT and Chromium via CSE_CHROMIUM when they are not defaults. No browser dependency is added to the skill runtime. On BuilderBob the existing browser-dependency sysroot must be selected with LD_LIBRARY_PATH, and Chromium needs a short native TMPDIR (the long repo path exceeds its socket limit). The [visual checks](rendered/visual-checks.json) record label clipping; human inspection checks the resulting PNGs. Native draw.io editor round-trip and final standard graphical-notation conformance are separate, unrun integrations.

Run python3 scripts/check.py --require-sysml for the regression suite. The reference tests reject reversed endpoints, changed succession, changed deadlines, broken draw.io references, and image/text mismatches. Scope omissions and source interpretation still need engineering review.

These examples are original MIT-licensed teaching material. They draw on the pack's method synthesis and maintainer study themes without reproducing textbook figures, course readers, or private annotations. Method background remains in [public references](../../docs/references.md); language authority is [OMG SysML 2.0](https://www.omg.org/spec/SysML/2.0), while runtime acceptance is limited to the pinned pilot and [alpha CSE profile](../../docs/sysml-v2-profile.md).

