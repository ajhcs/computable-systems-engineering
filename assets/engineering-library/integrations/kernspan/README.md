# Kernspan / egui adapter

Copy `cse_components.rs` and all `atlas*.png` pages beside a parent Rust module that imports `use eframe::egui;`, then declare `mod cse_components;`. The module uses the existing `image` PNG dependency. It targets the inspected Kernspan dependencies: egui 0.36.2 and image 0.25.

`Atlas::load(ctx)` loads the authored presentation atlas; `draw(ui, id, size)` paints one stable ID; `search(query)` returns independently selectable entries. Each square atlas cell preserves the source aspect ratio. The individual SVG files remain the editable master assets.

The adapter can be used by a UI picker. Selecting an icon returns a presentation identity, and must not directly mutate the model. For native architecture creation, supply explicit kind, owner, type, multiplicity and port/interface data to Kernspan's existing `architecture_canvas::declaration` and preview/apply route. Connectors require exact endpoint identities. Image shape and color do not supply these fields.

This is a reusable module, not a claimed built-in generic importer in Kernspan. No Kernspan repository or saved project is changed by this package.
