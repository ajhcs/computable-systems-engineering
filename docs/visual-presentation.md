# Opt-in visual presentation

This experimental slice renders one checked documentary function tree from the existing native-bound `CSE-VIEWS/1.0` contract. It adds presentation, not engineering meaning or behavioral verification. Existing model checking and JSON context commands keep their defaults.

## Generate and revise

```sh
python3 scripts/sysml_present.py examples/sysml/views/sample-handling.sysml --view FT --output work/tree-paper --body paper --target-width 1200
```

Use the CLI help for the current flags. The output directory must be new. The native parser and view checks must pass before any diagram is emitted. A function tree is an explicit documentary decomposition; it is not an activity sequence, allocation, native port network or simulation. The full native element identity and exact parent link accompany each displayed action name.

Edit the authoritative SysML and regenerate into another new directory. Do not patch exported SVG to change the engineering model. The output includes editable SVG text, an offline HTML reader, a semantic ledger, presentation parameters and a manifest. An actual graphical editor edit/save/reopen is a separate qualification.

The complete [portable design specification](visual-design-spec.md) and `assets/diagram-style/design-tokens.json` preserve broader selected directions, conditional ranges and open choices. They are design inputs, not a runtime support matrix or the smaller `--profile` schema.

## Selected direction and provisional parameters

The bundled profile retains Graphite and signal palette03 and Inter titles with Space Grotesk body text. Its eight color families and four neutrals are reusable presentation values. They establish no global relation, status, risk, type or acceptance semantics. Orange on violet is an optional scoped presentation pairing, not a semantic classification.

White, paper and faint-tint bodies remain explicit provisional alternatives. The proposed tint is 6% violet base over white, rounded per sRGB channel; it is not a ninth palette family. The function-tree defaults of 36-unit titles, 22-unit labels and 2 display-pixel lines are named slice-specific proposals. They do not override formal notation, source geometry or another view family's requirements.

This slice refuses unsupported characters outside printable ASCII plus middle dot. The declared font files have broader ranges, but those ranges are not claimed as exercised glyph coverage. No forced tracking, text length, stretching or text-fitting transforms are applied. The target must retain essential label size; use a larger output/native scrolling for a wider model.

## Reusable boundaries

`verifier.visual_style` validates profile data, embeds exact font bytes/notices, computes opaque-field contrast and converts a proposed display stroke width to native coordinates. `verifier.visual_projection` consumes the published parsed inventory after existing checks, retains model identities and parentage, and emits ordinary vector boxes, exact text and separate parent paths. Shared routes and crossings do not become junctions.

A narrow first slice does not implement physical glyph semantics, RF/data/material hatches, circuit connectivity or formal port notation. Source-qualified line patterns, contact side/order, arrows, texture classes and values stay with their domain adapters. The broader draft-profile and crispness studies are references for later qualification, not permission to infer those relationships from styling. No private worked reference art is shipped as a production renderer.

## Checks and limits

Run `python3 scripts/check.py --require-sysml` with the existing pinned parser installed and Java21 available. New focused suites cover malformed profiles, invalid native bindings, hierarchy defects, source preservation, deterministic output and edit/regeneration.

Contrast uses opaque sRGB fields and unrounded ratios; this slice requires at least4.5:1 for its text fields. This is a bounded numerical check, not a complete accessibility or readability verdict. [W3C contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) explains why actual size and antialiasing also matter. Inspect native and target-width pixels, loaded font identities, clipping, overlap and endpoints in the actual browser. Display widths are CSS pixels, not calibrated print dimensions.

The output manifest identifies supplied model bytes, profile, producer and font assets. Hashes identify inputs, not genuine engineering acceptance, authenticated decisions or a protected runner. Parse success and documentary structure do not establish semantic truth or completeness. Parent visual acceptance, installed-client activation, other diagram families, calibrated print and reader-comprehension claims remain separate.

## Fonts and rights

The four unchanged Latin WOFF2 faces come from `@fontsource/inter@5.3.0` and `@fontsource/space-grotesk@5.3.0`. Exact files, declared ranges, hashes and source-package identities are in `assets/diagram-style/fonts/manifest.json`. Original OFL notices are retained alongside the files and embedded in standalone font CSS. No font modifications or independent binary-revision decoding are claimed. The repository MIT license does not replace these notices.
