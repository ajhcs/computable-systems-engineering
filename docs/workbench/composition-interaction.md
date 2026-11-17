# Connected physical interaction in the local reference

This increment belongs only to physical composition. Its blocked acceptance case
was a browser action changing the same authoritative saved project as the CLI.
The supporting adapter is a single loopback process around `CompositionProject`;
it supplies no competing model, hosted account system or independent database.
Actual browser actions, raw project state and a fresh process must agree before
this increment is considered verified. The [site adapter](composition-site-tools.md)
now registers existing controller operations when the host API is present.
Cloudflare, remote project authorization, full MCP/MCP Apps and both actual
application journeys remain required capability gates.

The engineer has already received the trace-linked
[walkthrough](composition-walkthrough.md), requested Astra review and required
the original SVG/iconography kit. The current interface carries its separate
saved/pending names, explicit conflicts and retained configuration scope into
that implementation. The existing SysON selection/details precedent remains
applicable to these controls. Move/resize controls below are implementation
proposals within the authorized workbench scope; they do not establish new
engineering meaning or engineer acceptance.

## States and authoritative mappings

| State | Action and visible result | Authority and validation | Acceptance evidence |
|---|---|---|---|
| PC-LIVE-INSPECT | Select a saved frame; native properties and editing target identify that element | Exact saved reader embedded unchanged, registry UUID distinct from occurrence ID; project/view/session/revision context | Actual click/keyboard selection, definition/usage cases, source binding and real glyph checks |
| PC-LIVE-NAVIGATE | Fit the complete saved SVG in overview, then reveal a selected occurrence at readable size | Same reader navigation API in standalone HTML, direct controls and site callbacks. Camera state is transient; source/layout/history stay fixed | Complete bounds, 100% labels, pan-away refresh, resize/refit, fixed draft targets and locked gesture selection |
| PC-LIVE-RENAME | Enter a declared name, preview, then save explicitly | Existing native rename and full reparse; preview shares the transaction's candidate preparation; exact request UUID reused for save | Saved graph remains unchanged during preview; committed name and references update; identity survives |
| PC-LIVE-LAYOUT | Drag a frame, or enter bounds through a keyboard form; preview and save | `set_layout` changes the layout companion. Existing native endpoint/clearance/text checks decide validity. A dashed outline is unsaved UI feedback, not model artwork | Mouse move/resize and form edits; saved SysML/registry/scope bytes unchanged; invalid geometry refuses |
| PC-LIVE-CONFLICT | Another writer publishes before save; the old save conflicts | No automatic rebase or overwrite. Refresh shows current state and retains form values; another explicit preview creates a new request against the reviewed revision | Concurrent CLI edit, HTTP conflict, visible pending value and current native name; explicit re-preview succeeds |
| PC-LIVE-ACK | A save response is lost; retry the exact request, including after page reload | Pending save intent/request retained in tab session storage. Durable receipt lookup inside `transact` prevents duplication. A received receipt remains acknowledged even if subsequent refresh fails | Drop the HTTP response after publication, reload, retry; one new revision and the original receipt |
| PC-LIVE-RESTORE | Preview restoration of one whole saved revision and save it as a new revision | Existing `restore` primitive copies source/registry/companions; monotonic head never rewinds | Restore source and geometry, restore the later snapshot, reopen from a fresh process; stale commands remain stale |

Native ownership, selected/inherited configuration membership and geometric
position keep their existing meanings. A drag never reparents a declaration.
Existing literal quantities and unresolved-bound status remain visible in the
embedded saved view. Retained required-review scope is not replaced by selected
elements. A checked edit candidate or storage receipt does not turn a failed or
unknown configuration review into a pass.

Apply distinguishes a definite engineering refusal from an unconfirmed save
outcome. Storage exceptions after a possible publication, unreadable history
during retry and interrupted authentication cannot erase the pending request.
The adapter first attempts matching receipt recovery. If it cannot establish
that outcome, it returns `outcome_unknown`; the browser retains the exact retry
intent. Only a declared definite refusal clears that uncertainty. A following
reader/render error remains separate from an acknowledged commit.

The inspector is the same saved native artifact and original kit renderer;
this increment does not redraw its frames, fonts, textures or connectors in a
second frontend. The outer controls remain plain low-fidelity UI. Display aliases
remain distinct from the declared name. Fields are disabled while a checked
request is pending, so inspecting another element cannot retarget that request.

Incident routes retain their native endpoints when a frame is moved or resized.
The client proposes adjusted point lists; the engineering backend validates the
entire layout. Obstacle-aware routing and direct route editing are still open;
a proposed move with invalid clearance is refused, never silently published.

## Local transport

```sh
python3 scripts/composition_workbench.py --project work/private-composition.git --view-id PC_USAGE --connection-file work/private-composition-session.json
```

Use the private link in that exclusive-create, mode-0600 connection file. The
process binds only `127.0.0.1` and registers no service. Its fresh bootstrap
capability establishes an HttpOnly/SameSite cookie. Mutation calls require the
exact loopback Host and Origin, that cookie and a session CSRF value. No CORS
access or general filesystem route exists. This is a development boundary
under the same Unix authority, not hosted account/project authorization or a
protected engineering runner. Stop the process when finished; earlier connection
files are retained and cannot reopen a different new server session.

| Endpoint | Result |
|---|---|
| `POST /session` | Establish the private local browser session from its bootstrap capability |
| `GET /api/state` | One revision-bound state/reader pair and local session CSRF value |
| `GET /api/head` | Current published Git head for live refresh |
| `POST /api/preview` | Validate one exact typed rename/layout/restore request without writing project objects or reserving a revision |
| `POST /api/apply` | Apply that existing project operation and return its durable receipt; a following read error is separate and cannot revoke the receipt |
| `POST /api/receipt` | Read the exact prior request's original receipt at a captured published head; never applies or reserves a request |
| `GET /view.svg?commit=…`, `/view.json?commit=…` | Current saved drawing/bindings only when they match the requested commit; stale drawing requests conflict |

Preview is also available through `scripts/composition_project.py preview
--project … --request …`. It returns an unsaved source/record candidate, never
a transaction receipt. Applying always rechecks current state. A preview cannot
authorize changing source, engineering obligations or the selected revision.

## Open capability gates

This local connection does not complete creation, deletion, reparenting, property
editing, collapse/expand, referenced-resource presentation, inherited/redefined
configuration manipulation, all diagram occurrences, full drawing/export parity,
general undo/redo controls, private remote persistence or actual host adapters.
Whole-snapshot restoration is labelled accordingly. Initial-import interruption
recovery and the union-of-existing-support inventory also remain open. The parity
matrix keeps physical composition active until its complete workflow is proved.
