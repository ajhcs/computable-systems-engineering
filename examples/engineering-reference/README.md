# Real engineering references: originals and simplified readings

**Local review draft; no engineer endorsement or acceptance is claimed.** Start with original formal models, the authors' English engineering documentation, and original diagrams. This source-grounded set is separate from the rejected invented examples under `examples/diagram-reference`. Their performance pilot does not apply here.

TMT APS is an actual telescope-development engineering case by Herzig, Karban, Trancho, Dekens, Jankevicius and Troy (JPL/Caltech, TMT, No Magic), independently catalogued by [NASA](https://software.nasa.gov/software/NPO-50126-1). APE is a real ESO instrument whose MBSE Challenge reference was professionally reverse-engineered and deliberately simplified; it is not an as-built model.

| Engineering question | Matched reading | New view | Derived v2 |
|---|---|---|---|
| How does a composite maintenance state proceed and abort? | [TMT behavior](tmt-maintenance.md) | [PNG](rendered/01-tmt-maintenance.png) / [draw.io](rendered/01-tmt-maintenance.drawio) | [SysML](derived/tmt-maintenance.sysml) |
| How do English, a timing predicate, and a measured property relate? | [TMT timing](tmt-timing.md) | [PNG](rendered/02-tmt-timing.png) / [draw.io](rendered/02-tmt-timing.drawio) | [SysML](derived/tmt-timing.sysml) |
| What belongs to the whole, and how many? | [APE composition](ape-composition.md) | [PNG](rendered/03-ape-composition.png) / [draw.io](rendered/03-ape-composition.drawio) | [SysML](derived/ape-composition.sysml) |
| How does an optical connector reach a nested port? | [APE context](ape-optical.md) | [PNG](rendered/04-ape-optical.png) / [draw.io](rendered/04-ape-optical.drawio) | [SysML](derived/ape-optical.sysml) |

Original TMT is SysML 1.4 / MagicDraw 18.0 at the February 2017 pin. Original APE is SysML 1.6 / MagicDraw 2022x v7 at the 2023 pin. Neither originated as v2. Read the original links first; `derived/` contains new, separately validated v2 transcriptions, not complete migrations or execution-equivalence claims.

`source/projection.json` enumerates retained and omitted IDs within each selected scope, including direct members. `source/*.xml` are selected, reserialized original-notation fragments with vendor presentation removed. Their unresolved external references remain references; these are not standalone native models. Use the linked unmodified native archives as original formal authority. New SVG/draw.io geometry carries source IDs. [Notices](notices/README.md) preserve attribution and conditions.

Original paper/Cookbook figures and photographs are linked, not bundled. Private renderings used for critical comparison remain in ignored `work/authentic-sysml-sources`. The new diagrams redraw selected licensed model elements; they are simplified model-derived views, not native Cameo exports or full graphical-conformance claims. Draw.io is editable presentation, not lossless SysML interchange.

From the checkout: `python3 scripts/engineering_references.py` checks pinned archives in the ignored source directory and rebuilds projections; `--check` checks saved bounded contracts without rewriting them. `scripts/render_engineering_references.py` emits geometry; optional `scripts/raster_engineering_references.cjs` rasterizes with installed Playwright/Chromium and supports nonmutating `--check`. Native editor round-trip and simulation remain unrun.
