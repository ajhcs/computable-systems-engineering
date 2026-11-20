---
name: generate-engineering-diagrams
description: Create or review a source-linked engineering diagram, or find and export reusable engineering components. Use for editable model views, formal notation, engineering SVGs and document artwork.
---

Produce the requested editable view from the supplied model and selected source revision. Identify what the reader needs to see, the model IDs, the intended display or print size and any expected interactions. For changes to system meaning, use [architecture](../develop-system-architecture/SKILL.md) and keep the engineer's decision explicit.

### Choose the applicable source and method

- For a project look, use the supplied reference or repository specimens and the [visual reference guidance](../../docs/technical-documents.md#select-the-visual-reference). Use the [engineering design kit](references/design-kit.md) for its exact masters, fonts, swatches and notation. Record source identities and content-fit adaptations. Use a [visual profile](../../docs/visual-profiles.md) for a repeatable project identity.
- For reusable graphics, use [component workflows](references/component-agents.md) and the [catalog](../../docs/component-library.md). Search a bounded set, inspect exact IDs and source contexts, and keep model bindings explicit. Export the requested SVG, Draw.io library or Kernspan adapter.
- For the saved native physical-composition editor, use the [workbench operation guide](../../docs/workbench/README.md#choose-a-physical-composition-operation). Keep candidate and saved revisions distinct and inspect the exact preview before any authorized save.
- For typography, labels, legends, tables or density, use [readable presentation](references/readable-presentation.md). For HTML/PDF and actual asset or font checks, use [document rendering](../../docs/document-rendering.md).
- For professional precedent or an example, see the [reference library](../../docs/reference-library.md) and the [synthetic station walkthrough](../../examples/engineering-gallery/water-sampling/README.md).

### Render, check and refine

Record the semantic ledger before drawing. Carry governing IDs and applicable ownership, direction, visibility, multiplicity, port kind, control/object flow, guards, events, effects, state transitions and units. Preserve the distinction between definition and usage, and between a default and a binding. Use [meaning and context](../../docs/meaning-context.md). Label the source version and the view type, including original and derived versions when both are shown. Build formal graph content from model records and notation. SVG and Draw.io exports are presentation views with source links. Keep the SysML model as the editable authority. Image generation can supply editorial artwork where requested.

Render a representative view early. Compare it with the selected reference and source at the actual reading size. Refine visible failures and re-render. Check labels, glyphs, contrast, clipping, routes and endpoints in the final pixels. Match keys to the quantities and units shown. Look for renderer error images even when a file exists. Compare the same model IDs across baseline and changed views. Retain a readable zoom or scroll mode when the intended viewport is narrow.

Run the pinned parser for v2 model changes and the relevant source-fidelity checks for the view. For interactive delivery, exercise the requested actions and inspect the resulting state. If edit/save/reopen is in scope, exercise that route in the intended editor and check the reopened source and view. For numerical or behavior claims, use [bounded analysis](../../docs/engineering-analysis.md) with the named engine, supported semantics, supplied inputs and independently expected results. A legible drawing and a native parse establish different facts.

Resolve the real skill path through symlinks, then use the parent of `skills/` as the runtime root for shared scripts. For native setup, use the [SysML runtime guide](../develop-system-concept/references/sysml.md). Keep user artifacts and the writable parser cache outside the installed plugin. Run `python3 <runtime>/scripts/check.py --require-sysml` for shared runtime or library changes when the pinned parser is available.

Deliver the view and editable source first. Give the source revision, material omissions and actual visual, native and interaction check outcomes. Use [artifact freshness](../../docs/artifact-freshness.md) for generated sets and [work review](references/work-review.md) for dependent changes or difficult failures. Report unavailable checks as unrun and preserve useful source findings.
