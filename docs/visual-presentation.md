# Opt-in visual presentation

This experimental slice renders one checked documentary function tree from the existing native-bound `CSE-VIEWS/1.0` contract. It adds presentation, not engineering meaning or behavioral verification. Existing model checking and JSON context commands keep their defaults.

## Generate and revise

```sh
python3 scripts/sysml_present.py examples/sysml/views/sample-handling.sysml --view FT --output work/tree-paper --body paper --target-width 1200
```

Use the CLI help for the current flags. The output directory must be new. The native parser and view checks must pass before any diagram is emitted. A function tree is an explicit documentary decomposition; it is not an activity sequence, allocation, native port network or simulation. Without a label companion, the drawing leads with exact native action names and the human title “Function decomposition”. An explicit `--labels` companion supplies separately authored display wording bound to those exact native identities; it never renames the authoritative model. Internal view/node IDs and level tags are hidden by default; add `--show-ids` to display the view ID and place node metadata after each native name. Legitimate identifiers within native names are retained verbatim. Full IDs, native bindings, levels and exact parent links remain in the semantic ledger, source companions and manifest provenance in either mode. The subtitle “Documentary function hierarchy” labels this simplified presentation; the full claim limits remain in its companions and manifest.

Edit the authoritative SysML and regenerate into another new directory. Do not patch exported SVG to change the engineering model. The output includes editable SVG text, an offline HTML reader, a semantic ledger, presentation parameters and a manifest. An actual graphical editor edit/save/reopen is a separate qualification.

The complete [portable design specification](visual-design-spec.md) and `assets/diagram-style/design-tokens.json` preserve broader selected directions, conditional ranges and open choices. They are design inputs, not a runtime support matrix or the smaller `--profile` schema.


## Synthetic branching demonstration

```sh
python3 scripts/sysml_present.py examples/sysml/views/field-service-demo.sysml --view FT_DEMO --labels examples/sysml/views/field-service-demo.labels.json --output work/station-tree --body white --target-width 1600
```

This owned synthetic example declares one root function, three first-level functions and nine leaf functions. Its decomposition describes a service scope, without prescribing execution order, safety procedures, requirements or real equipment behavior. Its author supplied the readable labels explicitly. The native names, IDs, levels, bindings and parentage remain unchanged in `semantic-ledger.json` and exact SysML companions. The canonical `display-labels.json` companion and `presentation.json` record the separate wording. Unknown bindings, duplicate keys or elements, wrong views and unsupported glyphs are refused before output creation. Omitting a binding retains the exact native name; there is no inferred camel-case splitting.

Nodes wrap within a measured text region and fit their own content plus padding. Branch subtrees are balanced horizontally; leaf siblings stack in compact local groups. Child counts are derived from the documentary tree and occupy a useful separate cell. `--show-ids` adds metadata after the display label. Neither framing nor color creates a model-owned part or compartment.

| Design rule | Integrated behavior in this slice | Available or later work |
| --- | --- | --- |
| Square content-fit framing | Glyph-advance wrapping, bounded padding and height, no canvas-wide bars | Other notation-specific node shapes |
| Useful partitions and side keys | Derived child-count cell; optional ID/level cell; a single outer frame | Domain-owned compartments |
| Selected palette shade/tint roles | Explicit orange/violet, brick/cream and green/cool header pairs; readable ink labels | All eight families remain tokens; no universal status meanings |
| Inter and Space Grotesk | Embedded Inter title and Space Grotesk labels/counts, with pinned measured advances | Wider glyph qualification |
| Target-scale vector geometry | Editable text/SVG; declared display-pixel strokes; fresh vector raster export | Calibrated print and editor roundtrip |
| Line and hatch samples | Documentary decomposition routes only; shared trunks have explicit parents | Dashed relation semantics and typed materials/equipment textures |
| Drafted exterior illustrations | No invented physical geometry in this function view | Source-admitted physical glyph adapters |

White, paper and faint-tint leaf bodies remain provisional choices; the demonstration requests white explicitly. The profile resolves header fill, frame/accent and connector roles independently. Local defaults pair violet tint with tangerine shade, amber tint with brick shade, and cyan tint with green shade. Branch drops and local spines default to the frame/accent shade for traceability, while the shared fan-out stays neutral. These are retained contrasting-pair candidates and scoped implementation defaults, not newly invented universally approved combinations. Branch color is a local navigation role, repeated within each first-level branch. It is neither engineering status nor a selected universal palette mapping. Texture is deliberately absent: this function model declares no material or equipment classes that could give a hatch meaning.

`function_tree_roles` is an optional version-1 profile section containing a named pair catalog, `root_pair`, ordered `branch_pairs` and the neutral `shared_fanout` role. Each pair separately references `fill`, `frame` and `connector` as palette family/tone names. Equal frame/connector defaults preserve grouping without coupling their resolution. Header fill and frame must use different families; unknown references, unsupported tones, monochromatic header pairs and insufficient contrast are refused. Legacy version-1 custom profiles inherit the bundled explicit defaults. The resolved roles and per-node pair IDs accompany the output; they do not alter the semantic ledger or geometry.

| Local pair | Header fill | Frame/accent | Connector default |
| --- | --- | --- | --- |
| Orange on violet | Violet tint `#e0dae6` | Tangerine shade `#894b25` | Tangerine shade `#894b25` |
| Brick on cream | Amber tint `#ece1ce` | Brick shade `#7f362f` | Brick shade `#7f362f` |
| Green on cool | Cyan tint `#d4e3e7` | Green shade `#315e43` | Green shade `#315e43` |

All text fields require at least4.5:1 contrast. Header frames and connectors require at least3:1 against their actual header or paper fields, and frames must also pass on every provisional leaf body. These arithmetic gates supplement actual pixel review of the contrasting pairings; they do not select engineering meanings or guarantee visual acceptance.

Text layout uses `fonts/metrics.json`, measured from the pinned WOFF2 faces with Canvas `measureText` at 1000px and tied to each face SHA-256. Advances scale to the selected font size; normal glyph shapes and spaces are retained. This particular layout disables kerning and ligatures consistently in measurement and SVG, and requests geometric-precision text rendering to retain fractional advances at small sizes. It applies no letter spacing, fitting transforms or character substitution. Soft line breaks concatenate to the exact authored string, including spaces. Actual browser glyph bounds, face identity and target-scale clearance still need checking for each qualified candidate; advance sums alone are not visual acceptance.

## Selected direction and provisional parameters

The bundled profile retains Graphite and signal palette03 and Inter titles with Space Grotesk body text. Its eight color families and four neutrals are reusable presentation values. They establish no global relation, status, risk, type or acceptance semantics. Orange on violet is an optional scoped presentation pairing, not a semantic classification.

White, paper and faint-tint bodies remain explicit provisional alternatives. The proposed tint is 6% violet base over white, rounded per sRGB channel; it is not a ninth palette family. The function-tree defaults of 36-unit titles, 22-unit labels and 2 display-pixel lines are named slice-specific proposals. They do not override formal notation, source geometry or another view family's requirements.

This slice refuses unsupported characters outside printable ASCII plus middle dot. The declared font files have broader ranges, but those ranges are not claimed as exercised glyph coverage. No forced tracking, text length, stretching or text-fitting transforms are applied. The target must retain essential label size; use a larger output/native scrolling for a wider model.

## Reusable boundaries

`verifier.visual_style` validates profile data, embeds exact font bytes/notices, computes opaque-field contrast and converts a proposed display stroke width to native coordinates. `verifier.visual_projection` consumes the published parsed inventory after existing checks, retains model identities and parentage, and emits compact square boxes, losslessly wrapped text and documentary parent routes. A shared route is drawn once only for children with the same explicit parent; unrelated crossings never imply a junction. The common fan-out trunk is neutral, with scoped colored branch drops.

A narrow first slice does not implement physical glyph semantics, RF/data/material hatches, circuit connectivity or formal port notation. Source-qualified line patterns, contact side/order, arrows, texture classes and values stay with their domain adapters. The broader draft-profile and crispness studies are references for later qualification, not permission to infer those relationships from styling. No private worked reference art is shipped as a production renderer.

## Checks and limits

Run `python3 scripts/check.py --require-sysml` with the existing pinned parser installed and Java21 available. New focused suites cover malformed profiles, invalid native bindings, hierarchy defects, source preservation, deterministic output and edit/regeneration.

Contrast uses opaque sRGB fields and unrounded ratios; this slice requires at least4.5:1 for its text fields. This is a bounded numerical check, not a complete accessibility or readability verdict. [W3C contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) explains why actual size and antialiasing also matter. Inspect native and target-width pixels, loaded font identities, clipping, overlap and endpoints in the actual browser. Display widths are CSS pixels, not calibrated print dimensions.

The output manifest identifies supplied model bytes, profile, producer and font assets. Hashes identify inputs, not genuine engineering acceptance, authenticated decisions or a protected runner. Parse success and documentary structure do not establish semantic truth or completeness. Parent visual acceptance, installed-client activation, other diagram families, calibrated print and reader-comprehension claims remain separate.

## Fonts and rights

The four unchanged Latin WOFF2 faces come from `@fontsource/inter@5.3.0` and `@fontsource/space-grotesk@5.3.0`. Exact files, declared ranges, hashes and source-package identities are in `assets/diagram-style/fonts/manifest.json`. Original OFL notices are retained alongside the files and embedded in standalone font CSS. No font modifications or independent binary-revision decoding are claimed. The repository MIT license does not replace these notices.
