# Trace-linked low-fidelity interaction walkthroughs

Use rough mockups frequently as a normal part of engineering discovery when people must interact with the proposed system or interpret an operational handoff. Make a specific visual proposal that the engineer can inspect and challenge. A paragraph about a future interface alone is often insufficient to expose assumptions. Keep fidelity deliberately low until the important behavior and meaning have been reviewed.

This workflow applies to relevant concept, scenario, CONOPS and diagram handoffs. It does not require UI work for a calculation, language test or task with no interaction question. When no new interface is needed, record the external/manual, existing-tool or backend-only route and its reason. Keep skills independently invocable and tailor coverage to the selected scope; a scenario question does not require a complete CONOPS.

## Research before wireframing

Before drafting a relevant interaction, inspect current professional precedents for the specific task. Inspect primary product documentation together with actual screens, official demonstrations or official videos; documentation prose alone does not establish what the interface does. Reuse suitable inspected evidence when it remains applicable. Record the product/version or observation date, exact URL, page/figure or video timecode, observed behavior, what was inferred, and why the pattern fits or should be avoided. Keep inaccessible sources and evidence gaps explicit. Research informs a proposal; a precedent is not a requirement or proof of suitability. Do not impose a fixed product list or example quota.

## Start with a useful example

1. Read the actual needs, selected user actions, existing model, data contracts and implementation/unsupported boundaries. Preserve accepted decisions and identify proposals and unresolved meaning.
2. Publish a small shared state/command/trace contract before visual work: stable IDs, selected actors/actions, typed candidate changes or explicit unsupported semantics, and who owns each artifact. Do not delay the first sketch for a complete model or a process-document change.
3. Show an initial representative set promptly. Use plain connected low-fidelity wireframes in an editable SVG, HTML or similarly lightweight source, readable annotations and realistic source-bound examples. Make the walkthrough routes and transitions explicit; show consequential fields, available options, defaults, unknowns, actions and states. State side effects, validation, errors and recovery instead of hiding them behind a generic placeholder. Opinionated choices are welcome as hypotheses with alternatives and omission conditions; do not add a slider, dropdown, palette or other control merely to cover a category.
4. Expand shared sketches only as needed to cover the selected actions and important before/action/after, refusal, unknown and recovery states. Several actions may share a context, and one action may use several contexts. A modeled physical activity is engineering content, not automatically an operative UI action or a screen.

Include workspace and navigation chrome only where the selected interaction needs context, location, mode switching or movement between work areas. Show enough surrounding context to assess that interaction, and record intentional omissions; do not turn one project's panel arrangement, menu or navigation pattern into a universal requirement.

## Iterate toward sufficient definition

Sketching is an iterative engineering-definition activity, not a fixed mockup count or a one-time delivery. Obtain user feedback on a concrete initial walkthrough before substantial expansion; use that feedback to select the next uncertainty to resolve. Reuse feedback and stage authorization already given. Explore as many relevant interactions, states, errors and alternatives as needed to expose consequential ambiguity. Let risk, uncertainty and coverage guide depth; omit gratuitous screens. After review, reconcile findings into the affected needs/requirements, model semantics, component responsibilities, data contracts and checks, then revise the sketches against that source. Distinguish a proposed interaction visualization from implemented behavior and from verified evidence.

## Preserve the semantic contract

For each important state or transition, record:

- before state, user action, after state and visible feedback;
- selected need/scenario/activity IDs and requirement status: accepted need, implemented invariant, candidate behavior or unresolved decision;
- responsible components, data/field semantics and the explicit interaction purpose;
- a supported typed command/candidate change, or a clearly labelled conceptual/unsupported change and any proposed migration;
- actual validation scope, source/base binding, missing capability, errors, undo and recovery;
- acceptance evidence needed, what was actually observed and what remains not_run.

Place engineering mappings adjacent to the walkthrough in companion notes or a linked ledger: source/model IDs, typed data, command contracts, constraints, requirements and planned acceptance evidence. Keep this material outside the main user flow unless it helps that user make a meaningful decision. Keep the authoritative SysML model and source IDs distinct from the sketch. Preserve rich narrative, unknowns and original source bytes. Containment, membership, ownership, presentation position and annotation are different meanings; do not infer a semantic relation from a visual frame or gesture. Do not invent commands or quietly strengthen a supported schema. A draft control does not become an accepted requirement because it appears in a sketch. Current alpha capability limits describe the implementation, not the target product requirements; keep unsupported target needs and proposed migrations visible.

Maintain the trace from need → selected user action → requirement/behavior → component/data contract → interaction purpose → proposed context → acceptance evidence. Use explicit action/context bindings so an unrelated globally connected path cannot fill a missing obligation. Check coverage in both directions: source/model/requirement obligations to interaction paths or explicit dispositions, and controls/actions back to those obligations and supported contracts. For every in-scope requirement, identify its proposed realization and planned acceptance criterion/evidence, or declare a specific coverage gap and its disposition. A requirement declaration or a complete control inventory alone does not establish that chain. Every proposed control needs an originating purpose. Every selected required action needs a path or a justified external/manual/backend-only disposition. Relevant fields may be editable through a containing operation, conditional, on-demand, protocol-only or internal; an inventory is not a visible-control count.

## Review before polish or implementation

Inspect actual rendered pixels and basic navigation at the requested viewing sizes. Check legibility, clipping, endpoints/labels, important error states and editable source links. Ask an independent reviewer when the task calls for independent review. Record assumptions, findings and dispositions against stable IDs. Preserve requested prototype fidelity.

Before moving to polish or UI implementation, the engineer must have had a concrete trace-linked low-fidelity walkthrough to review, and material semantic/interaction assumptions must have a recorded disposition or remain explicit open proposals. Existing user authorization and already completed review carry forward; do not repeatedly ask for permission to do routine sketches, repairs or checks within that scope. A request for a rough walkthrough does not authorize product implementation, publication or deployment. A request explicitly authorizing the next stage governs that stage without a newly invented approval flow.

Bind each check receipt to the exact authoritative model revision and its imported sources, the sketch/view revision, and the relevant input/evidence/provenance revisions, using content hashes or immutable identifiers. Record the command, checker/runtime version, selected scope, result and exclusions. After a bound artifact changes, rerun the affected check or label the receipt as applying only to the earlier revision; never carry a stale pass forward as current evidence.

Run actual affected model/structure checks and supported computational checks where applicable. Report source/context coverage separately from human interpretation, usability, accessibility, engineering acceptance and implemented-system behavior. A clean parse, graph or sketch is not a mathematical verdict on arbitrary prose or all diagrams. Do not execute a physical operation or hosted service merely to illustrate it.

## Return reviewable artifacts

Return a short walkthrough route, editable sketch sources and requested rendered companions, the authoritative model and trace, source/command mappings, coverage/dispositions, actual check receipts and open assumptions. Preserve earlier frozen versions. Keep private raw material and user-specific drafts in the authorized private work area. Hand the shared contract and reviewed assumptions to the next owner rather than copying unreviewed implementation or silently changing a separately maintained skill.
