# Readable engineering presentations

Use this guidance when choosing visual encodings, organizing text or revising a diagram after review. For a new view, start with the [design kit](design-kit.md): choose its typography roles, exact swatches, suitable components and texture treatments for the selected view. A supplied project standard and required formal notation take precedence.

## Give each visual channel a job

Declare the local role of color, shape and texture in the selected view. Preserve formal glyph meaning before adding styling. Texture can be decorative separation or emphasis; it need not encode a third engineering property. If it encodes engineering information, bind it to an explicitly supported property and provide a key. Do not mechanically pair every color with its own pattern or imply material meaning.

For example, color may identify a responsibility group while shape retains element kind and a pattern marks an explicitly supported scope boundary. Derive entry and exit classifications from supported relations, not from node position or the absence of an outgoing arrow. Keys are view-specific; do not silently transfer one view's texture meaning to another.

Use a contrasting label backing over patterned areas where needed, and check actual text/background combinations, including shading. Distinguish decorative surface treatment from semantic texture in the record.

## Make text belong to something

Give metadata, counts, units, annotations and keys an identifiable owner. Use the kit’s suitable text box, boxed label or annotation treatment by default where it provides one, with content-fit padding and clear association to the owning element or route. Required formal notation can call for open labels; use alignment, proximity or a distinct leader where appropriate. A maintenance description belongs with equipment details, a layer count with that layer's heading, and an allocation-direction key with its matrix. Do not leave them looking like unrelated subtitles or floating instructions.

Rank text by its usefulness to the reader's task. Separate title, section/axis labels, element names, identifiers and supporting evidence. Use a small, deliberate set of sizes, weights and repeated insets. Inspect the longest labels with the actual rendered fonts. Font readiness alone does not prove the selected font supplied the glyphs.

Place connector labels near the specific segment they describe. Keep a consistent
frame-to-route gap for comparable horizontal and vertical labels; check the whole
label frame against both its own route and nearby unrelated routes. At a branch,
associate the label with its branch rather than a shared trunk. A boxed annotation
is not a model node. Preserve its distinct annotation typography and source-bound
relationship. Fix ambiguous placement by moving the label and, where needed, its
checked route; do not add an apparent engineering connection as a leader.

Keep long provenance, implementation notes and migration discussions beside the clean figure. Preserve source links and readable text alternatives. A caveat that materially changes how to read the depicted scope should remain visible or clearly attached; moving notes must not hide a source gap.

For standalone review drawings, include a compact visible identification block:
view or drawing ID, presentation revision, source publication and figure/page,
selected scope and established status. Distinguish a reconstruction's revision
from the historical source date. Keep full citations and source hashes in bound
companions. Multiple sheets need their own sheet numbers and a consistent drawing
identity. Never fill an approval or review field with an inferred authority.

Use the kit's document tables for that block: labeled cells for identifiers,
revision and source fields, with compact rows for selected scope. Keep the
figure heading fitted to its title and group the key and identification into
separate aligned tables where space permits. Preserve the kit's outer rules,
finer internal rules and repeated cell insets. Check the longest cell content
with the actual fonts; wrap within the cell rather than enlarging every field
into a full-width banner. Repeat only the identification needed to read a
detached detail sheet.

## Design for the delivered reading size

Select the intended screen scale or printed page before accepting the layout.
Measure the smallest required labels after the actual export scale is applied;
native SVG font size alone is insufficient. Also inspect arrowheads, gaps,
textures and line separation at that scale. Use the kit's role sizes and stroke
relationships consistently rather than stretching text or shrinking a crowded
diagram to meet a page count.

Retain a full-view overview for context. If an overview or original/reconstruction
comparison cannot carry readable detail, supply separate reading sheets and
overlapping detail views made from the same native SVG. Identify each viewport
and its position in the overview, indicate cropped continuations, and link back
to the complete drawing. Verify that every required label and relationship can
be inspected; a crop must not silently hide an endpoint or imply a new boundary.
Record paper dimensions, viewport transforms, projected text sizes and coverage
with the outputs. Such thresholds are declared drafting targets, not a claim of
an external standard or reader acceptance.

For native-scale browser views, provide readable scrolling and an explicit
overview control. A thumbnail may support navigation but should not be the only
reading view. Preserve the original-versus-reconstruction comparison alongside
the detailed sheets when source fidelity is the review question.

## Prefer readable names with traceable identifiers

For cryptic identifiers, show a source-reviewed human-readable name first, with the exact technical name beneath when it helps identification or traceability. Keep a one-to-one alias map and apply it consistently to row and column headings. A display alias does not rename the model or change a port's type, ownership or allocation. Do not guess an acronym expansion or introduce capabilities merely to make a label sound natural.

## Align quantities and preserve matrix semantics

For task/time comparisons, fixed columns and continuous row bands can help the reader track from task to role, quantity and plotted interval. Preserve units, chart precision, start offsets and allocation meaning; improved alignment is not a new scheduling rule or staffing verdict.

For matrices, keep readable axis names, cell meanings and the key together. Preserve direction, diagonal/not-applicable distinctions and what an empty cell actually means. Count unique relationships separately from mirrored cells. A blank cell does not prove physical impossibility.

## Review the result

Compare the revised view against the same scoped source/model identities. Check aliases, independent texture assignments, meaningful units and relationship direction before measuring layout. Then inspect actual pixels and font identities, clipping, text/edge collisions and ownership of annotations. Keep readable scrolling on narrow screens rather than shrinking formal labels. Geometry and contrast checks do not establish faster comprehension or user acceptance.

## Technical documents

For engineering documents, manuals and drawing sets, use [technical document guidance](../../../docs/technical-documents.md). Use a compact print hierarchy, complete labels and consistent units. Keep process logs and note inventories in linked evidence.
