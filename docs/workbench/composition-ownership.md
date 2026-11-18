# Native ownership in the physical workbench

Development status: active and unqualified. Physical composition remains the only
admitted capability. This operation does not close the capability or establish
actual Codex, ChatGPT or private Cloudflare acceptance. The qualified initial
project-authoring increment remains separate from this ownership work.

An ownership change moves one existing native part definition or usage and its
complete authored subtree. It retains engineering UUIDs. Changing a frame’s
position, changing a declaration’s owner and selecting a configuration role are
separate operations. Use the [original SVG fidelity requirements](composition-svg-fidelity.md)
for every saved, candidate and exported diagram.

## Sources and native destinations

Choose an existing part-definition/part-usage UUID, a particular native package,
or the unnamed root namespace and an explicit source file. Each destination is
`{kind, identity, file, bundle_sha256}`. `kind` is `PartDefinition`, `PartUsage`,
`Package` or `Namespace`. Part identities are persisted engineering UUIDs;
package/namespace identities are native resource fragments valid only for the
returned source bundle. They must be selected again after their bundle changes.
A qualified-name string alone is not a destination locator.

The source step moves the exact native declaration span and its internal comments.
Ordinary comments preceding that span stay at their original site. The preview
identifies changed files and this policy. Declaration form, short IDs, native
names, bounds and explicit typing remain unchanged. Original reference and alias
spellings are retained when their native bindings still agree. Reference tokens
may need qualification in the new context. Each reference is checked at its
mapped source span for its native feature, target and alias membership. A repair
qualifies the original alias when it remains accessible. A different alias with
the same spelling and target is insufficient. Hidden comments stay in place.
Nested semantic lists, such as explicit types, retain their order.

A provisional native binding probe repairs alias declarations before their
consumers. The candidate is refused after 32 repair rounds or when the original
binding cannot be preserved. Final sources undergo the complete native reparse
and semantic checks.

A semicolon-bodied destination becomes a body. This applies to part definitions,
part usages and packages: `part right : Container;` can become
`part right : Container { … }`. An existing body uses its native terminal anchor.
The implicit unnamed namespace has no closing brace: insertion uses the chosen
file’s EOF and is independently reparsed to prove actual ownership. Same-owner
file relocation is refused as a different operation.

Preserve ordinary versus reference `part` form. Native composition and enclosing
part-definition context are distinct. An ordinary usage under a package or root
namespace is noncomposite; a package nested inside a definition can retain that
enclosing definition for its members. Descendant context is checked throughout
the moved subtree. When the root’s native composite value changes, supply the
exact `{before, after}` boolean transition. Otherwise supply `null`.

Cycles, sibling/alias/short-ID collisions, stale locators, unsafe source boundaries,
unsupported affected references, native diagnostics and unexpected semantic
changes refuse the whole candidate. Retained configuration scope stays byte
identical and receives fresh complete findings. A failed correspondence is not
automatically rebound or accepted.

## Every affected physical view

Provide one explicit effect per affected physical view. Missing, duplicate,
extraneous or invalid effects refuse the entire operation.

| Action | Required fields and behavior |
|---|---|
| `reparent` | `view_id`, `action`, `parent_node`, `points`. The parent occurrence must be the exact native destination already visible outside the moved subtree. Preserve the incoming relationship occurrence ID; supply its checked route. Descendant levels update consistently. |
| `remove_occurrences` | `view_id`, `action`. Remove the captured subtree’s occurrences, incident routes and corresponding presentation entries from this view only. Keep the engineering declarations and UUIDs. An empty view is refused. |
| `preserve_structure` | `view_id`, `action`. Explicitly retain a root boundary or an affected descendant view whose structure does not change. A view root may have its native owner outside the drawing. |

Every retained box, route, frame/edge ID, authored style and local key stays fixed
except the explicitly supplied incoming route. Ownership does not autoroute or
re-layout the drawing. A valid imported source model with no cseViews record accepts an empty effect
list; a malformed declared record is refused. An unchanged root boundary keeps
its exact existing layout text, or its derived default without manufacturing
an authored layout. Every source-declared physical view and saved companion
must render coherently before publication. Repeated bindings within one physical
view remain a separate open obligation; occurrences across views and inspection
rows retain their existing distinctions.

## Shared command and durable save

The typed project request contains `operation: "reparent"`, `request_id`,
`expected_revision`, `element_id`, `destination`, `composition_transition`,
`view_effects` and `checked_bundle_sha256`.

Start preview with `checked_bundle_sha256: null`. Preview returns a
`checked_request` containing the exact resulting source/view bundle digest and its
canonical request digest. Save that exact returned request. Publication reparses
and checks the candidate again; a missing or different checked bundle is refused.
Preview does not reserve a request or publish a revision.

The existing Git receipt, concurrency, monotonic restoration and exact retry
rules apply. The original receipt remains recoverable after later edits. An
unavailable or absent receipt lookup does not establish non-publication; retain
the exact unknown request. A new expected revision cannot reuse a prior namespace
locator’s bundle binding. Review current context and explicitly select a current
destination before preparing another request.

## Interfaces under development

The source-only CLI accepts `ownership-context` with `--element-id`, bounded
`--offset`/`--limit` and optional `--affected-view`. `reparent` accepts explicit
`--destination` and `--view-effects` JSON files, optional
`--composition-transition` JSON, and the existing expected source/bundle digest.
Its output is an unsaved candidate. The saved-project CLI uses its existing
`preview`, `apply` and `receipt` commands with the shared typed request.

The local editor’s “Change native owner” inspector exposes paged destinations,
each affected view and exact owner/route consequences. Candidate inspection
fetches one affected SVG at a time and checks its bundle, request and SVG digests.
Confirm the exact candidate’s consequences before Save. Inspection selection
cannot replace a retained edit target. Browser reload retains an unknown save’s
complete checked request.

The local HTTP adapter adds bounded `/api/ownership-context`, `/api/source`
and one-view `/api/preview-view` reads. The source inspector reads exact saved or
checked candidate files in Unicode codepoint chunks, retaining CRLF and native
spelling. It verifies chunk and complete-file digests and clears stale responses
when the snapshot/file changes. The CLI already returns exact files through
project `inspect` and `preview`. The site adapter adds `cse_read_ownership_context`,
`cse_preview_ownership`, `cse_acknowledge_ownership_candidate` and
`cse_read_model_source`, while existing
save/receipt/restore tools use the same native project. The MCP client maps those
read transports around the shared controller. Production MCP server/component
integration and actual application journeys remain unqualified.

## Evidence and remaining gates

The ignored `work/workbench/composition-ownership-20261118` directory retains the
source-backed interaction variants, independent Astra reviews, native owner and
source-anchor probes, failed attempts and development results. R11 resolves the
reviewed walkthrough’s source-label and request-binding findings; it is a proposal,
not a saved-operation test.

`tests/test_composition_ownership.py` currently exercises native destinations,
composition/context changes, Unicode/comments/aliases across files, all-view
consequences, retained inherited-scope failure, bundle-bound locators, checked
Git save/retry, stale refusal, restoration and reopen. These targeted checks are
not assembled qualification. Direct manual/keyboard paths, broader adverse
controls, site/MCP equivalence, actual glyphs and exports, original-kit review,
required isolated regression, package smoke, and actual-host/private durability
remain required before the applicable parity cells can be proved.

## Assembled local qualification

The frozen source passed the full native regression across 95 suites and 1,472 reported cases, with four optional skips. The 70 Chromium journeys passed. The 390 px official MCP SDK reference journey exercised manual and keyboard ownership, checked source and artwork, exact replay after a lost response, and two restored native SVG exports. Astra independently verified the retained alias binding when another alias resolved to the same terminal type. The parity ledger records the scope and exact source and receipt digests.

Packaged CLI smoke, production MCP data tools, actual Codex and ChatGPT, and private Cloudflare restart recovery remain open.
