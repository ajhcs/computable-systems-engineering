# Physical composition interaction proposal

Open [the editable walkthrough](composition-walkthrough.html). This is a rough
interaction proposal over the [synthetic source](../../examples/workbench/composition/model.sysml),
not a connected editor or application-acceptance receipt.

| State | Originating purpose | Data and authority | Command and evidence |
|---|---|---|---|
| PC-INSPECT | Inspect the selected subsystem without leaving conversation | Native `Composition::Base::sensor`, short ID SENSOR and separate registry UUID; exact owner/type/multiplicity | Existing parser facts; workbench selection transport remains open |
| PC-RENAME | Change one selected element through inspector or agent | Name and resolved references in SysML; registry preserves engineering identity | Source candidate implemented in `composition_edit.py`; durable transaction and host equivalence remain open |
| PC-CONFLICT | Preserve an intervening engineer edit | Expected project revision, exact pending command and current head | Proposed revision-checked command; no overwriting; transaction implementation and race tests remain open |
| PC-REOPEN | Continue the same project in ChatGPT | Exact SysML, registry, companions and Git history | Proposed durable save/restart/reopen path; actual Codex/ChatGPT tests remain not_run |
| PC-OPTIONAL | Inspect optional multiplicity without claiming installed presence | Native 0..1 bounds and separately retained selected configuration | Existing configuration profile returns unknown; graphical/result integration remains open |

Declaration ownership and inherited selected membership are different facts.
The sketch labels each independently. Type membership is shown without claiming that a retained configuration scope has been checked. Moving a box must not change its owner.
The stale-request and reopen examples are alternative paths from the rename
candidate, not sequential states of the same edit history.

The rename adapter currently handles a single native source without documentary
records. Those restrictions are temporary missing cells. The target includes
atomic multi-file and linked analytical/documentary bindings. A synthetic
single-file demonstration cannot close that requirement.

## Inspected precedent

Observed 2026-11-16: SysON v2026.11.0 [model-management documentation](https://doc.mbse-syson.org/syson/v2026.11.0/user-manual/hands-on/how-tos/model-management.html),
sections 7–9, and its linked Read Element screenshot. The screenshot visibly
pairs an explorer selection with declared/qualified name fields in Details.
The documentation also describes editing through Details and diagram tools.
These support investigating selection-bound properties. They do not prove CSE
usability, concurrent editing, persistence or any runtime behavior.

SysON's direct-edit guidance warns that omitting parts of a compound label can
unset values. This proposal therefore separates declared-name editing from
type and multiplicity fields. That is a proposed CSE interaction choice, not a
SysML rule. The raw precedent screenshot stays in ignored research storage.

## Open interaction dispositions

- Review the separation of box movement, ownership changes and selected membership.
- Review conflict recovery and the visibility of pending versus committed edits.
- Add creation, reparenting, deletion and property-edit routes before declaring
  interaction coverage complete. This initial sketch is not the complete UI.
- The sketch now reuses `palette-rectangle-white-plain`, exact N0/N100 neutrals,
  DejaVu Sans/Mono and the existing unarrowed hierarchy route. Its adapted
  bounds and model bindings are recorded in `composition-kit-usage.json`.
  Production visual acceptance remains open.

Before substantial UI implementation, present this concrete proposal to the
engineer and record feedback under the repository's interaction walkthrough
guidance. Backend candidate and source-preservation work can continue meanwhile.

## Review corrections and remaining dispositions

Astra identified ambiguity in the original branch numbering, shared-role impact,
identity labels and configuration claims. The revised pixels label success and
conflict as alternative branches, keep the committed name separate from the
pending name, identify the shared Base declaration, and distinguish inherited
type membership from checked configuration selection.

The diagram uses saved kit frame geometry and real DejaVu font files. Specimen
words are removed; source-bound text stays independent. No formal meaning is
assigned to a neutral color or selection border. The former handmade diamond
was removed in favor of the preserved unarrowed hierarchy convention. This
mixed declaration/usage ownership projection remains an explicit proposal.

The implemented candidate call is
`CompositionDocument.rename(element_id, new_name, expected_source_sha256=...)`.
`element_id` is the stable project registry UUID, not the SysML short ID SENSOR.
Durable command IDs and monotonic project revisions belong to the proposed
transaction layer. A source hash does not supply that revision or history.

Renaming a shared role affects its inherited and redefined consumers. Exact
`native_name` fields in a retained configuration scope require explicit migration
or a stale/unresolved finding; preserving the registry alone does not migrate
that scope. This adapter and impact preview are required before the row closes.

Creation, reparenting, deletion, general literal-multiplicity editing and richer
inherited/redefined selection are unsketched, open interaction obligations.
The sketch does not waive them or freeze the old renderer exclusions.

Astra reviewed the revised desktop/mobile preview and conflict pixels. The
remaining 24px multiline spacing discrepancy was corrected from 31px to 34px
(at least 1.4em). Current renders and font-supplier evidence are retained
privately; this is initial-review readiness, not capability acceptance.
