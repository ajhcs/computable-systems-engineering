# Portable engineering visual specification

This specification records reusable presentation choices and proposed checks. It is suitable for implementation documentation, subject to engineering review. It does not claim implemented support, verified behavior or accepted engineering meaning.

## Decision status

Selected directions are the palette below, Inter titles, Space Grotesk for most other text, drafted front/profile/orthographic exterior cues, square-corner content-fit framing and useful information partitions. Oblique relief and compact silhouettes are unselected alternatives. Illustration cues do not establish physical geometry, dimensions, counts, containment or allocations.

White, paper and faint-tint box bodies remain open. Numerical sizes, spacing and weights are conditional recommendations. Universal line, texture and color meanings remain unselected. A scoped preference for orange `#894b25` on violet tint `#e0dae6` does not establish a universal body fill or engineering semantic role.

## Palette

| Family | Shade | Base | Tint |
| --- | --- | --- | --- |
| Signal blue | `#27456f` | `#32588e` | `#d2dae6` |
| Brick red | `#7f362f` | `#a3453c` | `#ebd6d4` |
| Amber | `#825d19` | `#a77720` | `#ece1ce` |
| Instrument green | `#315e43` | `#3f7956` | `#d5e2da` |
| Cyan blue | `#2e6371` | `#3b7f91` | `#d4e3e7` |
| Violet | `#58436f` | `#71568e` | `#e0dae6` |
| Tangerine | `#894b25` | `#b06030` | `#eedcd1` |
| Berry red | `#753c53` | `#964d6b` | `#e8d8de` |

Neutrals are paper `#eeeeea`, light `#dededb`, middle `#b6b7b5` and ink `#25282d`. White `#ffffff` is a body option, not another palette family. Essential labels need opaque contrasting fields and distinctions that do not depend on color alone.

## Typography

Use Inter for titles and Space Grotesk for most other text. Normal-width regular and bold faces are available; universal weight roles and numerical sizes remain open. The identified WOFF2 faces use SIL Open Font License 1.1. Package metadata is @fontsource 5.3.0, with Inter v20 and Space Grotesk v22 metadata. Include the applicable upstream copyright and license notices when redistributing font files; no binaries are included here.

| Family | Weight | Face SHA-256 |
| --- | --- | --- |
| Inter | 400 | `8909904ab6c872eb994093482a88a28eca2cd95912d7b6fecd72103b0dc07edc` |
| Inter | 700 | `6f56409fd3d64bb85f7d070bce20749db2d66b6d63cec586cc22d1c761be2491` |
| Space Grotesk | 400 | `65fd17fcbd2e2f522940b5f67ead3d23329e02891aa5495e74d11a499c0b0673` |
| Space Grotesk | 700 | `35f8aec56cfd5cbfdb03cc68733a54a0b05bb3617ffcd5fd332badc0b045ca55` |

Measure actual loaded glyphs. Preserve codepoints, scientific symbols, subscripts and units; explicitly qualify any supplement and report unsupported coverage. Do not force text width, stretch, tracking or fitting transforms. Wrap or resize the content region. Preserve legitimate notation rotations. Uniform viewer zoom is a separate presentation operation.

## Framing and open body choices

Use one content-fit frame with meaningful partitions. Header, body and footer cells are useful when each carries information. Decorative nested frames must not imply engineering containment. Native notation and model-owned compartments take precedence. Retain a reworked purple option; there is no universal purple exclusion.

Illustrative plain containers are 420 × 240 and 400 × 180 CSS px, with 2 px borders, square corners and optional 8 px or 7 px side keys. These dimensions are examples, not required defaults. A 1.5 px divider is proposed only for useful partitions.

Open bodies are white `#ffffff`, paper `#eeeeea`, or faint tints: violet `#f6f5f8`, blue `#f3f5f8`, tangerine `#faf5f3`, green `#f3f7f5`. The faint proposal uses 6% of an existing base over white: `floor((1-alpha)*255 + alpha*baseChannel + 0.5)` per sRGB channel, with alpha 0.06. It adds no palette family. Common quantity and index text uses ink `#25282d`; keep essential text, numbers and symbols visually distinct from the body.

## Conditional ranges

These recommendations assume a 1600 × 1100 CSS px authored sheet at zoom 1. They are presentation units, never physical engineering dimensions. Retain the applicability and exception for each range.

| Parameter | Range | Starting value | Unit | Applicability and exception |
| --- | --- | --- | --- | --- |
| page title | 32–48 | 40 | px | 1600px native sheet, title; Content fit and delivery scale |
| node title | 24–32 | 28 | px | Native engineering-node title; Long labels: wrap/resize, preserve meaning |
| body | 20–24 | 22 | px | Native labels and body text; Narrow screens scroll/reflow; do not silently shrink |
| annotation | 18–20 | 18 | px | Secondary nonessential context; Never hide essential meaning in unreadable text |
| padding | 20–32 | 24 | px | Plain presentation box interior; Ports/labels/notation may need more |
| related gap | 12–24 | 16 | px | Related plain content items; Measured labels may require larger gaps |
| group gap | 32–64 | 40 | px | Distinct visual groups; Source routing/containment takes precedence |
| label clearance | 8–16 | 12 | px | Label to essential route/terminal; Long text, branches, print scale |
| bend clearance | 16–32 | 24 | px | Distance from bends/terminals to nearby obstacles or labels; never a route-to-endpoint gap; Endpoint connection gap is zero; preserve source attachment side/order and node boundaries |
| container width | 320–560 | 400 | px | Simple untyped presentation container; Notation-specific nodes and content fit override |
| line weight | 1.5–3 | 2 | px | Opaque essential strokes on native sheets; Source notation or deliberate emphasis may differ |
| title leading | 1.15–1.3 | 1.2 | ratio | Multiline Inter title; Glyph/content measurement |
| body leading | 1.35–1.5 | 1.4 | ratio | Multiline Space Grotesk body; Dense symbolic notation may need an explicit exception |

A separate large-graphic profile at 1600 CSS px width proposes 3–6 px strokes, starting at 4; compact padding 12–16 px, starting at 14; and standard padding 18–24 px, starting at 20. Illustrative title sizes are 28, 32 and 44 px; body sizes are 20, 22 and 24 px. This profile applies to large graphic samples. Do not combine it with the general-sheet profile into a universal range or silently change typed notation.

## Lines, textures and notation

Solid, dashed, dotted, dash-dot, spotted, striped-band and color-channel samples are available visual directions. Universal relation mappings are unselected. At the large-graphic reference scale, illustrative strokes are solid 4 px; dashed 4 px with array `26 12`; dotted 6 px with array `0 17`; and dash-dot 4 px with array `26 10 2 10`. Dotted samples require an explicitly qualified cap treatment. Preserve native notation instead of imposing these arrays globally.

Textures are exploratory decoration in nonessential regions. Preserve declared equipment hatches, material stipple and other semantic patterns. Decorative textures do not establish material properties or relation types.

- The authoritative engineering model determines element identity, ownership, type, applicability, units, thresholds and obligations.
- Preserve declared relation direction and kind, port identities, endpoint attachments, side and order, multiplicity and cardinality.
- Keep junctions distinct from independent crossings; do not infer a junction from a visual intersection.
- Use arrowheads only where declared direction or sequence warrants them. Preserve composition-diamond ownership, control versus object flow, fork/join and state-exit semantics.
- Preserve declared resistor, transistor, switch and other specialized notation; a decorative pictogram is not a typed model element.
- Actual connections meet their declared contacts. Clearance applies to labels and obstacles. Preserve explicitly nonattached marks and documented gaps without inventing links.
- Do not create model containment, allocations or counts from boxes, facets, fasteners, icon marks or visual groupings.
- Unknown or ambiguous meaning remains explicit. An illustration does not become a formal systems model through styling.

Public diagram-family descriptions include system context/interconnection, composition/hierarchy, functional flow, activity, state machine, sequence, electrical/electronic schematic, concept illustration, traceability matrix and physical geometry. These labels are not a support matrix. Each supported family needs an explicit admitted model contract, notation rules and tests. Unsupported families remain unsupported.

## Crispness method

Compare baseline and candidate at the same canvas, browser renderer, device-pixel ratio and display scale. Compute effective painted widths through scene, element, pattern and instance transforms; raw stroke attributes alone are insufficient. Inspect text bounds, clipping, overlaps, arrows, dashes, hatch density, connections and crossings at the delivery scale.

Preserve editable vectors and text with qualified embedded fonts. Generate higher-resolution rasters by fresh vector rendering. Curves and diagonals use normal antialiasing; do not impose a universal crispEdges override. Thicker or thinner strokes do not universally improve sharpness. Thumbnail fit factors cannot establish equal text size, and nominal CSS pixels per inch do not calibrate a monitor or printer.

## Proposed acceptance checks

The following are integration proposals. Their inclusion does not report execution or engineer acceptance.

- **Model projection:** Check identity, ownership, endpoint kinds, topology, notation, units, cardinalities and text against the admitted model.
- **Meaningful refusal tests:** Use synthetic negative fixtures for wrong endpoints, missing required inputs, altered model inputs and unsupported notation. Required unknown, errored or incomplete checks cannot yield overall success.
- **Typography:** Check actual loaded faces, glyph coverage, codepoints, subscripts, metrics, font notices and absence of silent fallback.
- **Layout and contrast:** Check clipping, collisions, label and port clearances, contact attachment, arrowheads and measurable contrast at intended scales. Do not use color alone for essential meaning.
- **Artifact generation:** Regenerate from trusted model data; inspect native vectors and fresh raster exports. If offline viewing is delivered, test it without network resources and verify saved source identity.
- **Repository integration:** Run required scoped and repository regressions on the assigned integration base. Preserve existing public interfaces and reject execution of code embedded in model data.
- **Review and acceptance:** Keep semantic review, visual review, engineering acceptance and physical qualification separate. Hashes identify bytes rather than authenticate decisions.
- **Reuse rights:** Use synthetic fixtures, original reusable artwork or explicitly permitted attributed derivatives. Include required licenses with redistributed fonts and assets.

Where relevant, separately qualify graphical-editor edit/save/reopen, print and grayscale behavior, monitor scale, accessibility and representative reader comprehension. Numerical passes and visual preference do not establish physical correctness or engineering acceptance.

## Reuse boundary

This specification includes presentation tokens and generic engineering rules. It embeds no source figures, models, artwork, font binaries or evidence records and grants no rights to omitted material. Use synthetic fixtures, original reusable artwork or explicitly permitted attributed derivatives for implementation examples.
