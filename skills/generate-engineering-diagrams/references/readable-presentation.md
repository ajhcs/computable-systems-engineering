# Readable engineering presentations

Use this guidance when choosing visual encodings, organizing text or revising a diagram after review. Choose fonts, colors, panel layouts and texture mappings for the selected view rather than treating any one set as a universal default.

## Give each visual channel a job

Declare what color, shape and texture mean in the selected view. Preserve formal glyph meaning before adding styling. If texture carries engineering information, assign it a supported property that color or shape does not already encode. Do not mechanically pair every color with its own pattern. A view without a supported third property can remain untextured; subtle shading can separate surfaces without pretending to be another data category.

For example, color may identify a responsibility group while shape retains element kind and a pattern marks an explicitly supported scope boundary. Derive entry and exit classifications from supported relations, not from node position or the absence of an outgoing arrow. Keys are view-specific; do not silently transfer one view's texture meaning to another.

Keep patterned areas legible beneath labels, and check the actual text/background combinations, including shading. Distinguish decorative surface treatment from semantic texture in the record.

## Make text belong to something

Give metadata, counts, units, annotations and keys an identifiable owner. Use alignment, proximity, a field label, a panel header or a distinct leader as appropriate; enclosing every label in a box is not required. A maintenance description belongs with equipment details, a layer count with that layer's heading, and an allocation-direction key with its matrix. Do not leave them looking like unrelated subtitles or floating instructions.

Rank text by its usefulness to the reader's task. Separate title, section/axis labels, element names, identifiers and supporting evidence. Use a small, deliberate set of sizes, weights and repeated insets. Inspect the longest labels with the actual rendered fonts. Font readiness alone does not prove the selected font supplied the glyphs.

Keep long provenance, implementation notes and migration discussions beside the clean figure. Preserve source links and readable text alternatives. A caveat that materially changes how to read the depicted scope should remain visible or clearly attached; moving notes must not hide a source gap.

## Prefer readable names with traceable identifiers

For cryptic identifiers, show a source-reviewed human-readable name first, with the exact technical name beneath when it helps identification or traceability. Keep a one-to-one alias map and apply it consistently to row and column headings. A display alias does not rename the model or change a port's type, ownership or allocation. Do not guess an acronym expansion or introduce capabilities merely to make a label sound natural.

## Align quantities and preserve matrix semantics

For task/time comparisons, fixed columns and continuous row bands can help the reader track from task to role, quantity and plotted interval. Preserve units, chart precision, start offsets and allocation meaning; improved alignment is not a new scheduling rule or staffing verdict.

For matrices, keep readable axis names, cell meanings and the key together. Preserve direction, diagonal/not-applicable distinctions and what an empty cell actually means. Count unique relationships separately from mirrored cells. A blank cell does not prove physical impossibility.

## Review the result

Compare the revised view against the same scoped source/model identities. Check aliases, independent texture assignments, meaningful units and relationship direction before measuring layout. Then inspect actual pixels and font identities, clipping, text/edge collisions and ownership of annotations. Keep readable scrolling on narrow screens rather than shrinking formal labels. Geometry and contrast checks do not establish faster comprehension or user acceptance.
