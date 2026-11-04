# Mechanical and drawing-annotation candidates

This is a review set of **62 original, editable monochrome SVGs**: 61 requested concepts and one additional abstract gear-pair candidate. The [index](index.json) records each icon's category, treatment, intended meaning, limitations, source keys, and relative file path. Individual artwork is in [icons](icons/). Each file has a 35 × 35 mm intrinsic frame, a `0 0 160 160` viewBox, unique accessible title and description IDs, and no embedded raster, link, caption, page border, or background. IDs and annotation words are synthetic examples.

The set covers 4 motion, 8 mechanism, 6 component, 5 actuation, 6 force, 5 structure, 7 manufacturing, 5 assembly, and 16 drawing/document candidates. The two gear entries intentionally distinguish an orthographic physical wheel from a locally devised schematic pair of pitch circles. Categories do not imply that the corresponding device exists, operates, or meets a specification.

## How to read the set

The 35 technical illustrations use the accepted local contour/feature/support weights of 2.4 / 1.4 / 0.8 SVG units. Centerlines use `8 2 1.5 2`; no hidden edges are needed here. The remaining works are 23 simplified schematics, two interface pictograms, and two mathematical notations. Their glyph arrows use a consistent 2.0-unit stroke; arrowheads and text are editable SVG geometry/text. Every visible drawing stroke and glyph is black. The equal frames are for review, not a common physical scale.

The section marker identifies the resulting hatched view as **A–A**; the separate cutting-plane marker locates the cut and shows its viewing direction. Detail **A**, the numbered item balloons, datum **A**, revision **A**, and footnote **1** are examples of different annotation jobs. They are not records of an approved drawing. Dimension **L**, tolerance **± t**, and scale **1:n** are unbound placeholders, not measured values or a claim of an actual drawing scale. `ALL EXCEPT B` is illustrative text, not a standardized exception symbol.

The moment diagram uses the particular convention of rightward **r**, upward **F**, and counterclockwise positive **M** as viewed on the page. The torque diagram likewise marks counterclockwise positive in its shaft-face view. Torque is a moment; the different pictures emphasize a shaft and a force applied at a lever arm. Arrows are explanatory and are not evidence of actual motion, applied load, equilibrium, performance, or analysis. Features are reduced for legibility; teeth, links, contacts, cut sections and assemblies do not define manufacturable geometry, fits, load ratings or working procedures.

## Provenance and boundaries

Source keys in the index refer to these primary or local references:

- `local-palette` — the accepted [orthographic line specification](../../palette/sections/orthographic-illustrations/line-spec.json) and [its explanation](../../palette/sections/orthographic-illustrations/README.md). Used for frame, hierarchy and local drawing discipline; the icon geometries are newly drawn.
- `nasa-drawing` — [NASA GSFC Engineering Drawing Standards Manual, X-673-64-1F Rev. 001 (1994)](https://s3vi.ndc.nasa.gov/ssri-kb/static/resources/NASA%20GSFC-X-673-64-1F.pdf), especially §§3.2–3.5 and 8.6.3. Used to understand line roles, detail and section identification, and item-balloon purposes. The manual is a historical NASA practice, not a blanket approval of these examples.
- `iso-lines` — [ISO 128-2:2022, basic conventions for lines](https://www.iso.org/standard/83355.html), abstract. Used only for the scope of lines, leaders and references; the full standard and its detailed rules were not checked.
- `iso-dimension` — [ISO 129-1:2018, presentation of dimensions and tolerances](https://www.iso.org/obp/ui?_escaped_fragment_=iso%3Astd%3Aiso%3A129%3A-1%3Aed-2%3Av1%3Aen), scope and dimension-line terminology. It does not by itself define the application or interpretation of tolerances. The placeholders here have no application to an actual feature.
- `asme-views` — [ASME Y14 standards listing](https://www.asme.org/codes-standards/y14-standards), which identifies Y14.3 for orthographic and pictorial views. Used for the distinction in subject matter; no full Y14.3 conformance review was performed.
- `asme-dimension` — [ASME Y14.5, Dimensioning and Tolerancing](https://www.asme.org/codes-standards/find-codes-standards/dimensioning-and-tolerancing), public scope. Used to bound the datum/tolerance candidates; the full standard and edition-specific requirements were not evaluated.
- `nasa-torque` — [NASA Glenn, Torque (Moment)](https://www.grc.nasa.gov/WWW/K-12/airplane/torque.html). Used to distinguish a force and its moment arm and to recognize torque as a moment. The sign convention here is explicitly local.

These are local candidates, **not verified ASME, ISO, NASA, GD&T, or other formal symbols**. Do not substitute them for the notation and edition required by a real drawing. The sources are references for concepts and scope; they do not authenticate any depicted part or endorsement of the set.

## Rebuild and verification

From this directory:

```sh
python3 generate.py
python3 check.py
python3 mutation-checks.py
mkdir -p proofs/tmp
  XDG_CACHE_HOME="$PWD/proofs/cache" TMPDIR="$PWD/proofs/tmp" \
  python3 render-proof.py
```

The generator uses the Python standard library. The proof command uses the locally installed librsvg 2.62.4 and Pillow; no runtime dependency was added to the project. [Four contact sheets](proofs/) show every icon at its actual 35 mm frame rendered at 150 dpi, with labels outside the artwork. The [raster and ink-bounds receipt](proofs/rsvg-check.json), [checker mutation results](proofs/mutation-checks.json), and [review notes](proofs/REVIEW.md) report the limited checks and preserved initial findings. The renderer is not a native drawing editor. Physical printing, expert symbol recognition, independent engineering review, standards compliance, and editor round trips remain untested.
