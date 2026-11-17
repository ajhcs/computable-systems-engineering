# Owned definition creation

This development path adds an ordinary native `PartDefinition` under an existing
part definition selected in a saved physical definition hierarchy. The new source,
registry UUID, diagram occurrence, ownership route and presentation companions
form one candidate and one Git transaction. It belongs to the active physical
capability; it does not complete creation or actual application acceptance.

The interaction separates the captured native owner from inspection selection,
the declared name from an optional short ID, and the model element from its
diagram occurrence. A draft stays attached to that owner while the engineer
inspects another frame. Creation and unrelated edit forms cannot consume each
other's drafts. Site context exposes the same names, raw placement fields and
retained request.

## Native and visual contract

The pinned parser supplies the owner's terminal body/semicolon token and owned
member names. Insertion converts a semicolon declaration to a body or adds the
new declaration before its closing token. Other source bytes, comments, line
endings, files and unsupported surrounding syntax stay intact. Native escaping
follows the [decoded-name contract](composition-native-names.md). Owned names,
alias names and short IDs are checked before insertion. Reparse must add exactly
one ordinary definition while retaining every existing extracted native fact
and resolved reference.

The caller supplies a distinct canonical engineering UUID. Preview reserves no
durable identity; exact save/retry carries the same UUID. Presentation node/edge
IDs derive deterministically from it and remain distinct from the optional
engineering short ID. CSE-VIEWS/1.1 still binds the native qualified name; the
saved registry supplies the UUID during projection.

Only the selected view's node array receives the new occurrence. Existing JSON
text remains around that insertion. Old frames and routes keep exact geometry.
Automatic placement proposes a frame to the owner's right and below existing
frames/routes; it can refuse when geometry or canvas limits prevent that
proposal. Manual placement supplies the new frame and ownership route. Both
use existing endpoint, label, visible-ink-clearance and key-area checks. General
obstacle-aware routing remains open.

The new frame uses the original plain-white rectangle master, exact neutral
swatches, original DejaVu fonts/metrics and unarrowed ownership. Existing
appearance entries and the authored key remain intact; no texture, color or
icon is inferred as an engineering property. Every declared physical view is
checked before publication. Unsupported glyphs, collisions and insufficient
space refuse the whole candidate. Follow the [SVG fidelity contract](composition-svg-fidelity.md).

## Shared operation

`CompositionDocument.create_definition` serves the source CLI and local project
transaction. The visible form and `cse_preview_create_definition` site callback
use that same transaction preview and save path.
`cse_preview_current_edit` with `kind: create_definition` checks retained visible
creation values on their captured owner. It refuses to consume another form's
draft; other operation kinds likewise refuse an active creation draft.

| Request field | Meaning |
|---|---|
| `operation` | `create_definition`. |
| `request_id`, `expected_revision` | Exact request UUID and captured project revision. |
| `owner_id` | Existing engineering UUID of the selected native definition owner. |
| `element_id` | Distinct proposed engineering UUID, retained for exact retries. |
| `new_name` | Decoded local name; source quoting is automatic. |
| `short_id` | Explicit nonempty decoded short ID or null. No engineering short ID is invented. |
| `view_id` | Existing definition hierarchy containing the native owner. |
| `placement` | Null for automatic placement, or exactly `box` and `points`. Box has x/y/width/height; points are two through 128 finite x/y pairs. |

The project CLI accepts this request through existing `preview` and `apply`
commands. The source CLI accepts `create-definition` with `--owner-id`,
prospective `--element-id`, `--name`, optional `--short-id`, `--view-id`, optional
`--placement` JSON file and the existing source/bundle digest arguments. It
returns an unsaved candidate including new layout records. Persist its registry
and companions together with the SysML through the project transaction.

## Interaction and recovery

1. Select the owner; enter the new name, optional short ID and placement. The
   form shows its fixed owner and captured revision.
2. Preview the native candidate diagram separately from the authoritative saved
   diagram. Site context returns candidate native properties without copying
   embedded font data into conversation or recovery storage.
3. Save the exact checked request. The created occurrence is selected after a
   confirmed save. A revision conflict retains input rather than changing owner.
4. A lost acknowledgement retains the exact request, prospective UUID, captured
   owner and raw form values. Reload, receipt lookup and retry recover the same
   receipt; they cannot create another element.
5. Reopen or restore through real Git history. Whole-snapshot restoration creates
   a monotonic revision. Retrying a creation that was later restored returns its
   original receipt rather than reapplying it.

Retained configuration bytes remain exact and are checked again. A new definition
does not create an installed instance, add a selected role, narrow review scope
or establish engineering acceptance.

## Remaining creation coverage

Package/root and new-view creation, usages and type/multiplicity inputs,
definition-owned role-table selection, richer inherited/configuration edits,
complete artwork/drawing/export coverage, MCP/MCP Apps, remote private storage
and actual Codex/ChatGPT journeys remain required. This path does not silently
mix definition and usage projections or close the broader creation matrix row.
