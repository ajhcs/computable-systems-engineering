# Explicit part-usage typing

Status: local development implementation in qualification within the active
physical-composition capability. Source, transaction, inspector and guarded
site operations exist. Actual application and hosted acceptance remain open.
This contract does not close the capability or its host gates.

## State, command and authority

The editing target is one existing native part-usage UUID. Selecting an inherited
role captures its actual declaration, including its native owner. Editing that
shared declaration can affect its consumers. It does not copy the role into the
selected configuration. Definitions use specialization, a different operation.

`set_types` accepts exactly `operation`, `request_id`, `expected_revision`,
`element_id` and `type_ids`. `type_ids` is an ordered array of zero through 128
distinct existing project part-definition UUIDs. Each entry is an explicit
native feature typing; the list is not a set of alternatives. An empty array
removes the selected declaration's explicit typing. It does not assert that the
feature has no implied or inherited type. Display it as **No explicit typing**.

The same source operation must serve the source CLI, project preview/apply,
visible controller, guarded site callback and supplied MCP transport. Actual
Codex, ChatGPT, production MCP data tools and remote durability remain required
unfinished acceptance obligations.

Native nodes determine reference tokens and their typing delimiters. Retarget,
add and removal preserve hidden comments, whitespace, names, bounds, native
ownership, composition/reference kind, redefinition and subsetting clauses,
source-file boundaries, companions and existing UUIDs. The pinned native name
converter serializes qualified references; never split a name on `::`.
Reparse independently and refuse native diagnostics, unexpected native facts,
unintended reference relinking or unsupported source boundaries. Explicit
feature-chain typing without a directly bound type-reference node is not a
plain definition reference and must refuse with its reason.

Retained configuration input stays byte exact and is checked again. A changed
type may produce failed, unknown or unsupported retained claims. A successful
preview or Git receipt must not rewrite the scope or turn those findings into
pass. There is no implicit type compatibility or installation verdict.

## Connected interaction proposal

| Path | Before / action / after | Realization and acceptance obligation |
|---|---|---|
| PC-TYPE-INSPECT | Select a usage frame, declaration or retained role; inspect its actual declaration and explicit types. | Show owner, UUID, saved revision and complete type list. External/unavailable types stay visible and cannot become an empty selection silently. |
| PC-TYPE-EDIT | Change a type selector, add a definition row or remove a row. | Keep the captured target and raw ordered choices while inspection moves. Empty unfinished rows refuse preview; removing every row explicitly requests no explicit typing. |
| PC-TYPE-PREVIEW | Preview the exact choices. | Separate unsaved native properties, candidate SVG and retained-review findings; saved source and layout remain authoritative. Preserve the original kit and inspection/source links. |
| PC-TYPE-CONFLICT | Another edit saves before this request. | Exact stale request refuses; retain target, values and request. A fresh preview explicitly binds the newer revision. |
| PC-TYPE-RECOVERY | Save, lose acknowledgement, reload and retry. | Retain the exact request and raw rows before dispatch. One durable receipt/revision; a missing type after restore remains an unavailable choice until explicitly changed. |
| PC-TYPE-HISTORY | Reopen, export and restore the prior snapshot. | Exact sources, registry, companions, complete type list, original fonts/artwork and real Git history; restoration adds a monotonic revision. |

The low-fidelity form uses one labelled definition selector per explicit type,
with Add type and per-row Remove actions. Existing types appear before any empty
new row. No generic compound-label replacement is proposed. Keyboard activation
and native select navigation cover the same actions. Unavailable choices retain
their full name/UUID in adjacent wrapping text. Candidate properties carry all
types; a frame remains the existing composition presentation. No new icon,
texture, relationship arrow or ownership meaning is introduced by typing.

Follow the [original SVG and iconography contract](composition-svg-fidelity.md)
for candidate, saved and exported views. Keep exact original masters and font
files; inspect desktop and narrow pixels at readable size. Unchanged native
composition and layout should produce unchanged drawing geometry.

## Source, direct and agent access

The source CLI accepts `set-types --type-ids '["<definition UUID>"]'` with the
existing element UUID, project/registry and exact source or bundle digest.
Supply `--type-ids '[]'` to remove explicit typing deliberately. Omission is an
error. Its output is an unsaved candidate; retain every returned source,
registry and companion together. The project CLI previews/applies the same
`set_types` request through real Git transactions.

The visible inspector presents one selector per explicit type, Add and Remove
actions, and a separate preview. Row removal restores keyboard focus to the
successor/previous selector, or Add when empty. An unfinished row refuses
preview. Complete unavailable type names and UUIDs remain visible and retained.
Changing the inspection selection cannot retarget this draft.

`cse_preview_types` uses that same controller. Unknown or empty IDs refuse before
changing the form. `cse_preview_current_edit` with `kind: typing` checks retained
choices without replacing another form's draft. Context includes the raw ordered
`typing_draft.rows`, captured declaration, revision and availability. The supplied
MCP provider forwards the same operation and carries that context; production
MCP data tools and actual hosts are separate unfinished obligations.

Preview returns source-bound native properties and the same original-kit SVG.
Save retains the exact request and raw rows before dispatch. A lost reply keeps
the request for receipt lookup or retry. Reopen preserves unavailable identities;
exact stale retry refuses, and a fresh preview still requires explicit repair
of a missing choice. Restoration adds a monotonic revision and recovers all
sources, identities and companions. A later retry can recover the old receipt
without reapplying an edit that was restored away.

## Evidence required

Qualify add, retarget, remove, multiple and repeated typing clauses; `defined by`
and colon forms; direct reference usages; inherited/redefined declarations;
quoted and keyword names; cross-file types; CRLF, Unicode and valid hidden
comments; preserved multiplicity and other specializations; deliberate invalid
and unsafe transformations. Independently expect exact fact/reference deltas.

Exercise manual/site/CLI/MCP equivalence, source-bound candidate properties,
saved-kit pixels/font suppliers, stale and concurrent requests, lost response,
missing-type draft recovery, reopen, export and monotonic restore together.
Run the required complete native regression after shared-runtime changes.
Actual application and hosted private persistence evidence stays separate.

## Inspected precedents and source limits

Observed 2026-11-17: the official [Syside diagram UI documentation](https://docs.sensmetry.com/extension/diagram-views/using-diagrams/)
and its `viz_go_to_source.png` screenshot pair selected drawing elements with
their source. Reuse the existing CSE source-linked selection pattern. That does
not establish editing behavior or justify changing CSE styling.

The official [SysON 2026.1 release notes](https://doc.mbse-syson.org/syson/v2026.1.0/user-manual/release-notes/release-notes.html)
and linked redundant-feature-typing screen distinguish typing relationships and
show explicit feedback for duplicate creation. This informs explicit choices
and refusal messages, not a claim that CSE has adopted SysON notation or proved
semantic compatibility.

The pinned Pilot kernel 0.52.0 grammar, `SysML.xtext` rules
`FeatureSpecializationPart`, `Typings`, `TypedBy`, `DefinedByKeyword` and
`OwnedFeatureTyping`, admits multiple typings and both `:` and `defined by`.
Read-only native probes separately establish actual accepted examples. Syntax
acceptance does not prove arbitrary multiple-type compatibility, engineering
validity or configuration completeness.
