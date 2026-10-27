# TMT and APE: selected engineering-reference derivatives

This source-safe pack pairs original public authority links with four bounded
readings, separately authored v2 transcriptions and simplified editable views.
It contains no original model XML or local reserialized source slices, generic source-record projections, opaque
action implementations, source PDFs, figures or photographs. Original authorities
remain external; raw comparison inputs and historical evidence stay local.

| Selected question | Reading | Presentation | v2 derivative |
|---|---|---|---|
| Maintenance lifecycle and composite Abort | [TMT maintenance](tmt-maintenance.md) | [PNG](rendered/01-tmt-maintenance.png), [draw.io](rendered/01-tmt-maintenance.drawio) | [SysML](derived/tmt-maintenance.sysml) |
| Narrative versus formal timing boundary | [TMT timing](tmt-timing.md) | [PNG](rendered/02-tmt-timing.png), [draw.io](rendered/02-tmt-timing.drawio) | [SysML](derived/tmt-timing.sysml) |
| Direct ownership and multiplicity | [APE composition](ape-composition.md) | [PNG](rendered/03-ape-composition.png), [draw.io](rendered/03-ape-composition.drawio) | [SysML](derived/ape-composition.sysml) |
| Boundary and nested optical port | [APE optical](ape-optical.md) | [PNG](rendered/04-ape-optical.png), [draw.io](rendered/04-ape-optical.drawio) | [SysML](derived/ape-optical.sysml) |

The [curated view facts](source/view-facts.json) are reviewed derivative assertions
for those questions. They are not an independent source oracle or serialized
native records. [Adaptation deltas](source/adaptation-deltas.json) keep declared
interpretations visible. [Source notices](notices/README.md) apply throughout this
pack, its extension, presentation variants and native-composition examples.

Original TMT is SysML 1.4 / MagicDraw 18.0 at February 2017 pin
87832a1657ccab023a90a6acfd0dff02d60e2b46. Original APE is a professionally
reverse-engineered and simplified reference model, not certified as-built, at
2023 pin 288a863025498a4d8bc8e945cfec640e6a90268c (SysML 1.6 / MagicDraw 2022x
v7). Neither originated in v2. These derivatives claim no endorsement, complete
migration, native editor round-trip, simulator or engineering acceptance.

Run `python3 scripts/engineering_references.py --check` and
`python3 scripts/check_engineering_references.py` from the checkout for public
curated-contract and cross-representation checks. These do not read original
XML or claim independent original-source validation. The optional explicit
`python3 scripts/check_original_reference_sources.py --source-root <local-examples-root>`
checks the identity/parsing of six local reserialized source slices against
historical comparison digests; these are selected fragments, not original archive bytes. It performs no acquisition and fails if required
local inputs are absent. Its result is separate from public derivative checks.

Run `python3 scripts/render_engineering_references.py` only to generate local candidate
geometry; any changed pixels need actual supported rendering and inspection.
Existing saved parser/render receipts are historical evidence for their exact
unchanged inputs, never a fresh pass for changed bytes. Draw.io remains editable
presentation, not lossless SysML interchange. Private/rejected historical drafts
are not part of this pack.
