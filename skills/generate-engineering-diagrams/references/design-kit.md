# Engineering design kit workflow

For a new diagram, start from the
bundled [palette PDF](../../../assets/engineering-library/palette.pdf) and
[editable overview](../../../assets/engineering-library/palette.svg). Inspect
the pages relevant to the selected view before composing it: pages 1–4 show
shape and texture specimens, 9 port treatments, 12 connection labels, 19
line weights, 20 typography, 28–29 drawing tables and navigation, 30 routing and clearance, and 37–38 color
swatches. These examples guide presentation; they do not assign engineering
semantics. A user-supplied standard or required formal notation takes priority.

1. Freeze the source model and semantic ledger, then search the
   [component catalog](../../../docs/component-library.md) using the
   [agent workflow](component-agents.md). Inspect exact IDs and their source,
   treatment, context and SVG. Prefer a suitable existing element or child to
   a new shape. Distinguish an editable specimen sheet with sample content
   from the artwork or slot intended for use. For example,
   `palette-rectangle-grey-dots` supplies a dotted rectangle specimen;
   `palette-src-labels-redesign-labelslanes-connection-labels-boxed` and
   `palette-src-labels-redesign-labelslanes-connection-labels-inline` show
   connection-label treatments. These do not automatically become formal
   symbols or relationships.
2. Select fonts and roles from
   [typography-spec.json](../../../assets/engineering-library/tokens/typography-spec.json)
   and exact color IDs and hex values from
   [color-swatches.json](../../../assets/engineering-library/tokens/color-swatches.json).
   The kit names DejaVu Sans for reading and DejaVu Sans Mono for identifiers;
   check the actual files, glyph coverage and licenses used. The kit's
   reference sizes are tied to its sheet and stroke scale; fit the diagram at
   its intended reading size. Do not substitute the distinct legacy alpha.6
   Inter/Space Grotesk and palette 03 without identifying the choice.
3. Use a presentation copy of the matching asset or its suitable child.
   Content-fit resizing, replacing specimen text with source-bound labels,
   route or line-length adjustment, recoloring with exact kit swatches, and
   reuse of patterns or glyphs are allowed when they preserve notation,
   endpoint direction and source meaning. Keep the original master intact.
   Record selected component IDs, source hashes and the edits in the output;
   bind each instance to its source model identity. Explain a necessary new
   element or an exception where no suitable asset exists.
4. Use a kit text box, boxed label or annotation treatment where suitable so
   text has a clear owner. Formal notation may require open labels. Keep label
   backing opaque and contrasting over textures where needed. Textures may
   provide decorative separation or emphasis without encoding a third
   engineering property; declare their local role. If a texture represents a
   model property, bind and key that property explicitly. Never invent an
   engineering category from a pattern, color or icon.
   For drawing metadata, inspect the document components before selecting a
   generic rectangle. The saved `palette-refined-documents-documents-page1-title-block`
   provides ruled identification cells; its `revision-block`,
   `navigation-figure-heading-1` and `navigation-legend` companions supply the
   matching revision table, compact heading and key. Fit their fields to the
   actual content, retain the source rules and record adaptations. Do not stretch
   a plain paragraph box across the canvas as a substitute for these tables.
5. Inspect rendered pixels at the intended size: actual fonts, clipping,
   contrast, text/route collisions, annotation ownership, endpoints and
   crossings. Compare the same source IDs and relationships, and retain
   editable sources and asset/selection records. Report unsupported styling or
   renderer capabilities; choosing an asset does not itself make it supported
   by a particular native renderer. Native editor round-trip and engineering
   acceptance remain separate checks.
