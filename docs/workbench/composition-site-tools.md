# Physical-composition site adapter

This increment addresses the active physical capability's agent/manual editing
obligation. The smallest supporting change is a host registration around the
existing local controller. It adds no engineering semantics, diagram renderer,
artwork, database or account system. The original saved SVG/DejaVu reader remains
the displayed model. Full MCP access, remote authorization, MCP Apps and both
actual application journeys remain required capability gates.

The adapter follows the documented
[site-tool contract](https://learn.chatgpt.com/docs/webmcp): feature-detect
`document.modelContext.registerTool`, register narrow inputs and call existing
application operations. Unsupported browsers retain the normal controls.
Registration, synthetic callback testing and real host execution are distinct
claims. The page never substitutes `navigator.modelContext` or advertises a
registered callback as a connected Codex session.

## Interaction and model authority

`cse_get_context` returns the visible saved revision, project/view/UI-session
identities, native selection and occurrence, fixed editing target, retained form
values (including the selected restoration revision), current viewport state, pending exact request,
saved history and independently retained
configuration findings. It also reads the latest published head without
refreshing the displayed model. An intervening publication can therefore be
visible as a different head; the native expected-revision check remains decisive.

This is the [shared controller snapshot](composition-provider.md), also consumed
by the MCP client context publisher. Subscriber failures cannot alter findings
or acknowledgement. A loading snapshot can identify a newer revision while
`ready` remains false; actions still require its ready guarded context.

Every UI-changing call supplies the exact returned guard: project, view, UI
session, saved revision, commit, bundle digest, interaction generation, selected
engineering UUID, occurrence ID, editing UUID and editing occurrence. Navigation revision, mode and
scroll offsets additionally bind the current viewport. A changed selection, draft,
gesture or session invalidates the old guard. An in-flight action or active
pointer gesture refuses a competing command. Selection can inspect a different
element while preserving the fixed editing target. It cannot replace required
review scope or turn inherited membership into native ownership.

Preparing new values refuses to overwrite any human draft, checked change or
unconfirmed save. `cse_preview_current_edit` can instead check the visible values
on their original target without replacing them. Existing preview/save/refresh/
discard functions are shared with the visible controls; the adapter supplies no
independent engineering verdict. A preview is unsaved, and configuration
`fail`, `unknown` or `unsupported` findings retain their own meaning.

| Tool | Concrete effect |
|---|---|
| `cse_get_context` | Read visible selection, draft, history and saved native findings; observe the latest head. |
| `cse_select_element` | Select/reveal the exact UUID and occurrence; retain edits and scope. |
| `cse_list_inspection_occurrences` | Read a bounded, revision-bound page of frames, native declarations or retained roles; preserve full required review scope. |
| `cse_set_view_mode` | Fit the complete saved SVG overview, or reveal the selection at 100%; retain model, layout and all draft state. |
| `cse_preview_rename` | Put a declared name into the selected target's form and check the existing native rename. |
| `cse_preview_create_definition` | Preview a new definition under the fixed selected owner, with exact name/short ID, checked placement and original-kit candidate diagram. |
| `cse_preview_multiplicity` | Check explicit finite lower/upper bounds on the selected native part usage through the same visible form controller; retain source identity and required scope. |
| `cse_preview_layout` | Put finite bounds into that frame's form and check the existing layout operation, including incident endpoints. |
| `cse_preview_restore` | Check whole-project snapshot restoration as a new monotonic revision. |
| `cse_preview_current_edit` | Check retained owned-definition creation, rename, multiplicity, layout or restoration fields exactly as displayed. Creation and other forms cannot consume each other's drafts. |
| `cse_save_change` | Save/retry the exact request ID already checked in this tab. |
| `cse_discard_change` | Explicitly discard unsaved values; refuse an unconfirmed save. |
| `cse_refresh_project` | Read saved state while retaining original draft targets and exact unknown requests. |
| `cse_lookup_receipt` | Read an exact prior request's durable receipt without applying it. |

Context, inspection paging and receipt lookup have a read-only hint. Other tools describe their UI or
durable side effects. All use the existing authenticated loopback boundary;
returned context excludes bootstrap access, cookies, CSRF values and server-side
repository paths. Model and label content remains untrusted data.

The [role inspector](composition-role-inspection.md) distinguishes a native
declaration from each retained context occurrence. Unresolved roles return a
null native UUID and cannot become semantic edit targets. Unframed rows refuse
layout before changing form values. The fixed draft captures UUID and occurrence,
including when inspection moves to another occurrence of that same UUID.
Draft kinds remain separate; a refused preview retains a visible discard path.

Rename input is the name itself, including any spaces, punctuation or literal
quotes. The shared native operation supplies source quoting; a delimiter entered
as part of the input remains a literal character in the name. The existing form,
site callback and source/project CLIs use this same decoded-name contract.
Text that the form would alter, including CR/LF, is refused before changing the
draft. Saved-view font and layout refusals apply before publication; see
[native names](composition-native-names.md).

Navigation uses the [saved reader's viewport API](composition-navigation.md).
Ordinary refresh retains a manually panned readable viewport, including when
the selection is elsewhere. An explicit return to a different retained editing
target reveals that target. Overview refits after resize or refresh. The camera
does not enter SysML, saved layout or Git history. Actual host support remains
unqualified by these local callbacks.

## Save and recovery outcomes

A save returns `committed` only with the native durable receipt. A failed
following read cannot revoke that acknowledgement. `unconfirmed` retains the
exact request in tab session storage for retry, including after reload. An old
UI guard cannot be reused in the new page session. An acknowledged request can
also be looked up after losing the tool response, using its original full
request rather than creating another request ID.

The shared provider awaits exact-intent persistence before sending apply. A
preparation/storage failure returns `not_sent` for that attempt and preserves an
earlier unconfirmed outcome. Receipt acknowledgement also matches project and
the native canonical request digest. Temporary cleanup failure cannot revoke a
known commit; a retained entry can be recovered and retried without duplication.

The new `CompositionProject.lookup_receipt(request)`, CLI `receipt --request …`
and authenticated `POST /api/receipt` share the same read-only lookup. It
validates the exact typed request and digest against a single captured published
history. A successful lookup returns its observed commit/revision and either
the original receipt or null. Null means absent at that captured head; it does
not prove that a concurrent save cannot publish later. Request-ID/payload reuse
is an explicit error. An unavailable receipt read returns `unconfirmed` through
the site adapter, never evidence of a refused or absent save.

## Required assembled evidence

Native HTTP tests cover exact-payload lookup, later-head lookup, absent lookup,
unchanged Git objects, session/CSRF checks and request reuse. Real Chromium
interaction checks use a synthetic `document.modelContext` host API to exercise
registration and callbacks against the real native project. Their scope must
be labelled accordingly: they cannot prove discovery, transport, safety review
or execution inside the actual Codex/ChatGPT host.

Acceptance includes alternating human/tool preview and save, guarded selection,
retained drafts, native refusal, stale external CLI edits, lost save responses,
reload/retry, failed receipt reads, monotonic restoration and matching durable
source/identity/layout state. Current browser evidence must bind the adapter,
controller and backend source bytes. Refresh matched desktop/mobile views and
font-supplier checks without changing the existing SVG/iconography conventions.

These are tested local paths within an incomplete capability. Remaining
physical operations and actual application journeys stay active in the parity
matrix; this adapter does not reduce their target support.
