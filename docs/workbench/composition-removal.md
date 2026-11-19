# Physical composition removal

A diagram occurrence has a view ID and a node ID. A native declaration has a project UUID. The two removal commands have separate request types and share the same checked project transaction. A diagram removal can hide a graph branch while preserving the native parts, relationships and scope. A model deletion removes the captured native declaration and its admitted owned part descendants. Its preview accounts for every saved projection that binds one of those declarations.

## Inspect and prepare

Use `scripts/composition_project.py inspect-removal --project PROJECT --request REQUEST`. Supply `expected_revision` and `expected_bundle_sha256`, plus either `element_id` or both `view_id` and `node_id`. The result identifies the revision, captured declaration, native subtree, incoming references, owned members that require an explicit decision and affected projections.

For a native deletion, supply a `delete` request with `element_id`, `reference_effects` and `view_effects`. Each admitted source effect takes the captured codepoint locator and either a surviving part definition in `replacement_id` or `null` to remove that exact explicit typing. An incoming reference through an alias is visible even if its terminal target survives. The candidate rejects unsupported native member and reference effects. Documentary and analytical bindings require a typed disposition wherever they reference a removed member. The retained configuration record stays byte-exact and its findings are recalculated against the candidate.

For a presentation-only change, supply a `remove_occurrence` request with the captured `view_id`, `node_id` and `view_effects`. In either operation, each view effect includes `view_id`, `action`, `node_ids` and `edge_ids` exactly as inspected. Removing a view root requires an explicit `close_view` effect and removes its associated presentation companions. Surviving drawings preserve existing frame masters, style, layout and routes. The impact includes style templates that lose their last example and the authored legend entries that remain available for an engineer's presentation decision.

When the view is authored in a SysML `cseViews` documentation block, closing it edits that presentation record in the source file. The surrounding source, native declarations, and retained configuration scope stay intact.

Include `request_id`, `expected_revision` and `checked_bundle_sha256: null` in the initial preview request. Inspect the resulting source, scope and view effects. Submit its exact `checked_request` through `apply`. A lost response can be recovered with `receipt` or by repeating that exact request. Restoration writes a new revision and brings back the previous model and presentation.

## Workbench

Select a framed occurrence to inspect diagram removal or select a native part to inspect deletion. The workbench keeps the captured UUID and revision while displaying affected views, source locators, and owned members that require disposition. Choose each supported source effect and confirm each affected view. Review the exact checked candidate, its source and retained findings, then save separately. An authored key stays available for an explicit presentation edit if removal takes away the last instance of a template.

The loopback and supplied MCP provider share these controls and the native checked request. The local site-tool adapter exposes read, preview, acknowledge, save and receipt operations with the current project, revision and selection guard. Its preview and save use the same controller as manual actions. Tested registration uses a browser test double for the actual Codex site-tool host.

When the active view closes, the workbench surfaces the saved revision and the remaining physical views. Open one explicitly to continue in the same project. If the last view closes, source inspection, retained configuration findings, history restoration and exact retry remain available. The selected view belongs to the browser session. An MCP provider only offers view navigation when its project grant includes that support.

## Qualification

Initial and on-demand removal drawings are checked against the exact captured view ID, action, node and edge IDs, and SVG digest. A closing view must return no candidate drawing. A surviving view must return the expected drawing. Receipt lookup or retry must return the reviewed bundle digest before the browser clears intent. Saved and candidate graphs load the original font faces before showing their drawings. If the host prevents candidate font verification, checked source and findings remain available.

The local Chromium removal journey covers original SVGs, paired diagram and model edits, a changed retained finding, checked confirmation, active-view closure, lost-response recovery, and restoration at 1440 px and 390 px. The 390 px official SDK reference exercise also checked affected-view navigation, actual DejaVu glyph suppliers, the retained authored key, and exact restoration of both styled SVG exports.

The signed local assembly ran the packaged MCP Apps component and the workbench with a simulated site-tool host against one durable project. A native deletion survived loss of its save response and a Worker restart. The other surface recovered the exact receipt, closed an embedded view, and restored the original source, UUID, retained review and SVG. Actual Codex desktop, ChatGPT and private remote recovery remain required.
