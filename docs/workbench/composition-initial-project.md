# Start a physical model

Status: initial native source builder, local Git initialization/recovery, CLI and
direct/site startup controls under development qualification within physical
composition. The walkthrough remains a proposal. The supplied MCP startup
provider has a local official-SDK reference path; production data tools, actual
application/hosted acceptance and complete physical capability closure remain open.

The existing editor opens an already saved project. The engineer needs to create
the first native root and its view directly or through Codex, then continue in
that same editor. This is a physical-authoring obligation, not a separate
project-management platform.

## Shared state and command

An initial session has a prospective project UUID, root UUID and view ID, and
no saved revision or engineering projection. Its initial expected revision is
exactly zero. It must not supply a simulated saved model to the existing editor.
After durable creation, the normal saved revision starts at one.

The typed `initialize_physical_project` request has exactly these fields:

| Field | Meaning |
|---|---|
| `operation` | `initialize_physical_project`. |
| `request_id`, `project_id` | Canonical request UUID and the explicitly granted prospective project UUID. |
| `expected_revision` | Integer zero, excluding Boolean false. A saved project's first revision is one. |
| `root_element_id` | Distinct prospective engineering UUID, retained while editing names and during recovery. |
| `root_kind` | `definition` or `usage`: ordinary native part definition or namespace/package-owned part usage. |
| `new_name`, `short_id` | Decoded declared name and optional nonempty short ID. Native serialization supplies source spelling. |
| `namespace_name` | Decoded model-package name or null for the unnamed root namespace. Empty text is not an implicit namespace decision. |
| `view_id` | Granted prospective physical view ID. It is not a filesystem path. |
| `expected_bundle_sha256` | Null for a draft preview; the exact checked bundle digest for first save and receipt recovery. |

Preview returns the same typed request with its candidate digest filled in.
Save rebuilds and independently checks the candidate against that digest. A
generator or source change before first publication refuses with
`candidate_changed`; it cannot silently save different preview bytes. An
already published retry checks its immutable source blobs and manifest without
regenerating source or rerunning the current generator.

The initial usage has no explicit typing, native default multiplicity `1..1`
and `is_composite: false`. Its namespace/package owner is not a physical parent.
These facts must be visible. No selected configuration, installed presence, behavior,
requirements or accepted review scope is inferred. A source/diagram check is
separate from an engineering review; configuration review starts unconfigured.
Reference roots, richer initial architectures, later package/root/view editing
and other physical gaps remain separately inventoried obligations.

The engineer enters model meaning: root kind/name, optional short ID and package.
UUIDs, storage paths, metadata-package names and host implementation choices stay
outside the primary form. The operator selects the trusted local storage target;
application callers supply only granted project identities.

## Native source and original diagram

Use native name serialization, independently parse the complete candidate, and
compare its exact intended root facts and source bindings. Definitions have no
usage multiplicity. The default root usage has no explicit type or physical
owner/composite relationship. It does not assert installation. Composite owned
usages remain the existing nested-creation operation.

The existing renderer requires a package-owned `cseViews` record. Keep the
engineering declarations in `model.sysml` and the source-bound view record in
`views.sysml`, in a deterministically named presentation package. That package
holds view metadata; it does not become a physical component. Avoid collision
with explicitly authored top-level long and short names, including fallback
suffixes. Preserve an explicitly global root's
native unnamed namespace instead of moving the root into a new package to make
the diagram render.

Both source files, the complete registry and companions form the saved model.
An initial view has one level-zero occurrence and no invented ownership edge.
Use the same original [SVG/iconography renderer](composition-svg-fidelity.md),
masters, exact neutral swatches, DejaVu fonts and native-size navigation.
Unsupported source names or glyphs refuse the candidate with retained input;
they must not be rewritten into another name or rendered using substitute fonts.

## Initial persistence and recovery

The legacy import path retries after successful publication, but an interrupted
directory initialization before its first head remains an open import-recovery
obligation. The separate initial-authoring path uses staged publication.

The supporting initialization path builds and fsyncs a complete initial bare Git repository
in an owned sibling staging directory, then publishes it with a supported atomic
no-replace operation. Fsync the parent directory before acknowledging creation.
Every destination it newly publishes must have a complete first revision.
An unrelated existing directory, symlink or project must never be adopted,
replaced or deleted. Unsupported publication facilities refuse explicitly.
The trusted parent must already exist and support the required directory
operations; a final parent symlink refuses before staging or publication.

Retry the exact typed request. Before publication, retry may rebuild an owned
attempt. After publication, receipt lookup returns the original revision without
creating another project or commit, including after later edits. Concurrent
identical requests converge on one receipt; different requests cannot overwrite
the winning project. A possible publication followed by a failed acknowledgement
remains unconfirmed until exact lookup/retry establishes its durable outcome.
Receipt recovery must fsync the publication parent again before acknowledging
durability; visibility of a matching Git head alone does not prove that flush.

Initial receipt identity must bind the typed request independently of regenerated
source formatting. Preserve legacy import digests and existing project history.
No automatic rollback, history rewind or cleanup of unrelated storage is allowed.
Any remaining crash window must be explicit and fail closed.
Legacy import still has its older interrupted-initialization gap. This new
initializer does not close that separate import-recovery obligation.

An initial receipt lookup under an accessible trusted parent may observe an
absent target and return null commit, revision zero and null receipt. That
observation reserves nothing. Unreadable, corrupt or timed-out history is an
unconfirmed outcome; it must not become a definite refusal merely because its
receipt could not be read. A matching receipt requires its exact first source
blobs, hashes, registry root identity and checked bundle to remain available.

The CLI uses `prepare-initial --request <draft.json>` to return native candidate
sources, registry and the checked request, without creating the target.
`initialize --request <checked.json>` publishes or recovers that request;
`receipt --request <checked.json>` observes it. All commands retain the existing
`--project` trusted local target argument. Save the returned checked request
exactly before dispatch, including its request ID and candidate digest. Existing
inspection, edits, history, restoration and exports then use that same project.

The local initial browser entry uses `composition_workbench.py --initial` with
retained `--project-id`, `--root-element-id`, `--view-id` and the trusted target.
The engineer's form contains native root meaning, not those internal IDs or a
storage path. No revision-zero projection is manufactured. Preview and creation
share the CLI's native operation; original candidate font readiness gates first
dispatch. A validated matching first receipt explicitly opens the existing
saved-model controller, reading its current revision. The startup server refuses
saved-model routes before that handoff and checks the project/root/view grant.

The default local browser retains intent in per-tab, same-origin `sessionStorage`.
Same-origin reload and restart on the same origin are recoverable boundaries.
Fresh/closed tabs and changed ephemeral ports need the original checked request
or an independently opened saved-project route; this adapter does not promise
cross-origin or cross-application intent persistence. A supplied host must provide
explicit intent storage and a saved-controller handoff without replacing global
browser storage or network APIs.

Intent storage may be synchronous or asynchronous. The controller awaits its
read before enabling actions, orders captured writes, and confirms the exact
checked intent before dispatch. Failed preparation returns `not_sent` for that
attempt while retaining any earlier dispatched/unconfirmed outcome. Failed
receipt-state retention cannot turn a matching durable acknowledgement into
an unsaved operation.

Closing the initial controller prevents new transport calls and saved-editor
handoffs. A write already preparing an intent may finish, but that attempt
returns `not_sent` and restores any earlier unresolved dispatch state. Site-tool
registration stops on closure; a registration already in flight is retired when
it resolves. Hosts without working unregistration report cleanup unavailable,
and retained callbacks refuse operations from the closed controller.
Retain a raw-form snapshot independently of the mounted inputs so unmounting
cannot corrupt that correction or discard an already-dispatched durable
acknowledgement. Receipt processing after closure writes retained state without
accessing the removed form.

The client compares checked source-file hashes, native serialized names,
qualified identity/owner, prospective registry and exact original SVG. It
preserves the compositor's wrapped name lines and spaces. First receipts must
match the retained request digest and checked bundle. Save, lookup and open
reject contradictory revision-one commits; later saved views cannot precede a
head already observed in that session. Saved HTML's revision, commit and native
projection must match the returned state before handoff.

The supplied `cse-initial-host-1` provider carries an immutable project/root/view
grant, request transport, intent storage and an explicit saved-controller
handoff. Its MCP adapter uses these native data-tool names:

| Provider operation | MCP data-tool contract |
|---|---|
| `initial_state` | `cse_read_initial_composition_state` |
| `initial_preview` | `cse_preview_initial_composition` |
| `initial_apply` | `cse_initialize_composition_project` |
| `initial_receipt` | `cse_lookup_initial_composition_receipt` |
| `initial_open` | `cse_open_initialized_composition` |

These names are exercised by the local reference server. They do not establish
production MCP deployment. The same SDK client then supplies the existing saved
controller; close the initial controller and its context subscription during
handoff. Actual Codex, ChatGPT and private remote authorization/durability need
their own execution evidence.

An initial lookup reporting absence does not cancel another identical attempt.
If a dispatched checked bundle cannot be regenerated and no matching receipt is
available, the conservative outcome remains unconfirmed. Preserve the original
request for manual resolution; a stronger service-side finalization protocol is
still required before claiming that all such outcomes can be resolved remotely.

## Connected interaction and acceptance mapping

| Path | Before / action / after | Realization and acceptance evidence |
|---|---|---|
| PC-START-DRAFT | No saved model; enter root meaning. | Prospective IDs remain fixed; real native source and original-kit diagram appear only after preview. |
| PC-START-PREVIEW | Preview the exact initial request. | One source-bound root, correct native owner, no manufactured configuration pass, no storage publication. |
| PC-START-SAVE | Create the checked model. | Persist exact sources/registry/view and return a matching durable revision-one receipt; open the same saved-model controller. |
| PC-START-REFUSAL | Invalid names/glyphs or another initial creation. | Preserve raw fields and IDs; no replacement or silent retargeting. Distinguish the unsaved draft from the current project. |
| PC-START-RECOVERY | Lose the reply, reload or restart compute. | Retain exact request before dispatch; recover its original receipt or retry exactly. No duplicate initial commit. |
| PC-START-CONTINUE | Inspect, manually edit, agent edit, restore and export. | The existing native operations retain the new root UUID and sources, real Git history, original artwork/fonts and revision-bound findings. |

The direct form, source/project CLI, guarded Codex site tools and supplied MCP
component must call the same builder and initial transaction. Startup context
must distinguish draft, checked candidate, unconfirmed outcome and saved project.
Selection in the resulting editor never replaces retained review scope.

Qualify both root kinds; named and unnamed namespaces; quoted/keyword names;
short IDs; literal comment delimiters; metadata-name collisions; invalid source
and glyphs; exact source/registry correspondence; process interruption before and
after publication; identical/different initial-request races; unrelated target
preservation; lost responses; restart/reopen; manual/agent parity; actual glyph
suppliers; native exports and the existing completed-operation regressions.
Actual Codex/ChatGPT and hosted private authorization/durability remain distinct
mandatory gates for the physical capability.

## Inspected precedent

Observed 2026-11-18: the official [SysON 2026.11 Projects Browser](https://doc.mbse-syson.org/syson/v2026.11.0/user-manual/features/homepage.html)
and its `homepage-new-project.png` screen separate blank, template and uploaded
project entry points. The [project-management flow](https://doc.mbse-syson.org/syson/v2026.11.0/user-manual/hands-on/how-tos/project-management.html)
describes a named blank project opening before models/representations exist.
This supports investigating a distinct initial state. CSE's selected scope here
is its first physical root and view; the precedent does not authorize templates,
imports, public sharing, vendor iconography or broader engineering semantics.
