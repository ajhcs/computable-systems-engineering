# Physical composition interaction proposal

Open [the editable walkthrough](composition-walkthrough.html). This is a rough
interaction proposal over the [synthetic source](../../examples/workbench/composition/model.sysml),
not a connected editor or application-acceptance receipt.

| State | Originating purpose | Data and authority | Command and evidence |
|---|---|---|---|
| PC-INSPECT | Inspect the selected subsystem without leaving conversation | Native `Composition::Base::sensor`, short ID SENSOR and separate registry UUID; exact owner/type/multiplicity | Existing parser facts; workbench selection transport remains open |
| PC-RENAME | Change one selected element through inspector or agent | Name and resolved references in SysML; registry preserves engineering identity | Source candidate and local Git transaction reference exist; connected graphical/host equivalence remains open |
| PC-CONFLICT | Preserve an intervening engineer edit | Expected project revision, exact pending command and current head | Local Git publication rejects stale revisions and is race-tested; connected UI/host conflict recovery remains open |
| PC-REOPEN | Continue the same project in ChatGPT | Exact SysML, registry, companions and Git history | Local restart and portable Git restoration are tested; actual Codex/ChatGPT tests remain not_run |
| PC-OPTIONAL | Inspect optional multiplicity without claiming installed presence | Native 0..1 bounds and separately retained selected configuration | Existing configuration profile returns unknown; graphical/result integration remains open |

Declaration ownership and inherited selected membership are different facts.
The sketch labels each independently. Type membership is shown without claiming that a retained configuration scope has been checked. Moving a box must not change its owner.
The stale-request and reopen examples are alternative paths from the rename
candidate, not sequential states of the same edit history.

The rename adapter now prepares multi-file candidates with typed workflow/view
and display-label binding updates. Retained configuration bytes remain fixed,
with explicit reconciliation and fresh configuration findings. Remote atomic
publication, remaining analytical adapters and host equivalence remain open; see the
[bundle contract](composition-bundle.md). The walkthrough remains a synthetic
example and cannot close those requirements.

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
The [local transaction reference](composition-persistence.md) now implements
request IDs, monotonic project revisions and Git receipts. The sketch is not
connected to it yet; remote publication and both host adapters remain open.
A source hash does not supply that project revision or history.

Renaming a shared role affects its inherited and redefined consumers. Exact
`native_name` fields in a retained configuration scope require explicit migration
or a stale/unresolved finding; preserving the registry alone does not migrate
that scope. Typed workflow/view and display-label adapters now exist at the candidate
boundary. The retained scope stays unchanged and is checked again. Remote
commit and an interactive impact preview remain required before the row closes.

Creation, reparenting, deletion, general literal-multiplicity editing and richer
inherited/redefined selection are unsketched, open interaction obligations.
The sketch does not waive them or freeze the old renderer exclusions.

Astra reviewed the revised desktop/mobile preview and conflict pixels. The
remaining 24px multiline spacing discrepancy was corrected from 31px to 34px
(at least 1.4em). Current renders and font-supplier evidence are retained
privately; this is initial-review readiness, not capability acceptance.
