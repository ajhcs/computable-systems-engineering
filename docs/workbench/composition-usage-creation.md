# Part-usage creation contract

Status: local development implementation in qualification within physical
composition. The native operation, shared editor and guarded site callbacks
exist; actual application and hosted acceptance remain open. This contract
does not close the broader creation row.

## Shared state and command

The engineer captures a native owner from a declaration, diagram frame or
retained-role inspection. Inspection may move while the draft keeps that exact
owner UUID, source revision and occurrence. The owner must be an existing
`PartDefinition` or `PartUsage`; a selected configuration occurrence never
creates a new owner or copies an inherited declaration into a usage.

The `create_usage` request extends the existing preview/apply path:

| Field | Meaning |
|---|---|
| `request_id`, `expected_revision` | Exact request UUID and saved revision, retained for retry. |
| `owner_id`, `element_id` | Existing native owner UUID and distinct proposed engineering UUID. |
| `new_name`, `short_id` | Decoded local name and explicit optional short ID. Source quoting follows native serialization. |
| `type_id` | Existing part-definition UUID, or null for no explicit typing. Null does not mean an unknown external type. |
| `is_composite` | Explicit Boolean: ordinary `part` or `ref part`. This is separate from selected configuration membership. |
| `multiplicity` | Null for the native default, or exactly integer `lower` and `upper`, with `0 <= lower <= upper <= 2147483647`. |
| `view_id` | Existing physical view used to inspect the candidate. |
| `placement` | Null, or the existing exact `box`/`points` format when a new ownership frame is applicable. Declaration-only results refuse supplied placement. |

The source step uses native namespace-terminal and owned-member facts. It
preserves all other source bytes, files, comments and line endings, adds one
registry UUID, reparses, and compares native facts and resolved references.
Typing must resolve to the exact selected definition after native name
serialization; a name that resolves differently in the captured owner refuses.
The pinned language does not admit a leading `::` absolute reference. Native
qualified-name conversion serializes each decoded segment, including keywords; splitting a qualified name on `::` is unsafe for quoted names.
Missing native anchors, ambiguous membership, name/alias/short-ID collisions,
unresolved typing and unintended semantic deltas refuse the entire candidate.

JSON added or rebound inside a native documentation comment Unicode-escapes
slashes. Quoted names containing `/*` or `*/` therefore retain their exact native
meaning without splitting the surrounding view-record comment. Standalone linked
JSON keeps its existing encoding behavior. Creation and subsequent rename share
this source treatment; source declarations still use native name serialization.

## Presentation and interaction mapping

| Path | Before/action/after | Representation and check |
|---|---|---|
| PC-USAGE-OWNED | Select a framed usage; create a composite child. | One source declaration, declaration-table row and ownership frame/route. Existing geometry stays exact; new geometry passes all saved-kit checks. |
| PC-USAGE-DEFINITION | Select a definition; create a role declaration. | Declaration row. A definition hierarchy contains definitions, so the role does not become a child definition frame. |
| PC-USAGE-REFERENCE | Select a native owner; explicitly create a reference. | Declaration row with `is_composite: false`; no owned-composition route. Native namespace ownership is still shown. |
| PC-USAGE-UNTYPED | Explicitly choose no typing; create an ordinary child. | Native type absent, default multiplicity preserved. Do not invent a type or infer a selected installation. |
| PC-USAGE-PREVIEW | Enter name, short ID, optional type, composite/reference and bounds; preview. | Separate candidate drawing plus exact native properties and retained-review findings. Saved source remains authoritative. |
| PC-USAGE-RECOVERY | Save, lose reply, reload, inspect exact receipt, retry. | Same request and proposed UUID; one durable Git revision. Stale revision refuses without retargeting the draft. |
| PC-USAGE-HISTORY | Reopen, inspect, rename and restore. | Exact identities, sources, companions and source-bound exports. Restore adds a monotonic revision. |

The direct form, source CLI, project CLI and guarded site tools call this same
operation. The MCP provider forwards its exact request to the same native
preview/apply path; production MCP data tools and actual-host acceptance remain
separate unfinished obligations. Context carries raw draft values, captured owner,
selected occurrence, revision, pending request and retained scope. A successful
save selects the new frame when present, otherwise its `decl:<UUID>` row.

Use the original [SVG and iconography contract](composition-svg-fidelity.md).
Frames use the saved rectangle master, exact neutral swatches and DejaVu faces;
ownership is unarrowed. A reference is not drawn as composition. No new icon,
texture or engineering category is implied by this operation. Native-size
scrolling preserves label readability on narrow displays.

## CLI and recovery

The source CLI accepts `create-usage`, `--owner-id`, a distinct `--element-id`,
`--name`, optional `--short-id`, optional `--type-id`, explicit `--usage-kind`
(`composite` or `reference`), and either both `--lower`/`--upper` or neither.
Supply the existing `--view-id`, optional exact `--placement` JSON file and
source/bundle digest arguments. Output is an unsaved candidate; retain every
returned source, registry and companion together. The project CLI previews and
applies the typed request above through the existing real Git transaction.

The visible form and `cse_preview_create_usage` use the same controller.
`cse_preview_current_edit` with `kind: create_usage` checks retained raw fields
on their captured owner; it cannot consume another form's draft. The provider
context includes the separate `usage_creation_draft`. Save persists the exact
request and raw fields before dispatch, retains an unconfirmed outcome after a
lost reply, and recovers by exact receipt lookup or retry. A receipt acknowledges
durable storage; it does not establish an engineering verdict.

## Scope and acceptance

Retained configuration bytes remain exact. Creating a declaration does not add
a selected role or equipment quantity. The current configuration checker checks
the separately retained claims; a pass does not enumerate every declaration or
prove an installation. Candidate findings must retain unknown and failed scope.

Qualification requires definition and usage owners; composite/reference;
typed/untyped; default, finite, optional and zero bounds; quoted names and
cross-file types; CRLF/comments; alias collisions; native anchor corruption;
exact geometry; invalid placement; site/manual draft retention; CLI/MCP
equivalence; stale edits; exact/concurrent retries; receipt recovery; real Git
restore; native exports and original-kit pixel/font checks. Actual Codex and
ChatGPT, hosted private durability and the remaining export/font obligations
stay separate required gates.

[Existing usage typing](composition-typing.md) is a separate local development
operation. Package/root and new-view creation, semantic ownership edits, deletion and
other unfinished physical operations remain in the parity matrix. This increment
must not narrow that target.

## Inspected precedents

The official [Syside diagram documentation](https://docs.sensmetry.com/extension/diagram-views/using-diagrams/)
and its `viz_go_to_source.png` screenshot were inspected on 2026-11-17. The
screen links a selected diagram element to its source declaration. That informs
source-linked selection only; it does not prove graphical creation or justify
substituting its styling for CSE's kit.

The [SysON 2026.9 tutorial](https://doc.mbse-syson.org/syson/v2026.9.0/user-manual/hands-on/tutorials/batmobile.html)
and `tutorial-result.png` were inspected. The screenshot places an explorer
beside typed usages and definitions with visible multiplicities. This supports
keeping declarations and visual occurrences inspectable together. Its diamonds,
colors, icons and layout are not adopted. Documentation screenshots are not
observed product executions or CSE acceptance evidence.

Private source-linked examples and screenshot provenance are retained in
`work/workbench/composition-usage-design-20261117/`. They use synthetic SysML;
their recorded configuration pass covers only `$root` and `Sensor`.
