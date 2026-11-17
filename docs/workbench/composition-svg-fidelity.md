# Physical-composition SVG and iconography fidelity

The saved engineering kit is an acceptance input for this capability. Visual
fidelity is checked in its operation-level parity cells before the capability
can close. It is not a later styling phase.

Use the [design-kit workflow](../../skills/generate-engineering-diagrams/references/design-kit.md),
[readable presentation](../../skills/generate-engineering-diagrams/references/readable-presentation.md)
and [original palette](../../assets/engineering-library/palette.pdf).
[Source pins](composition-kit-source.json) identify the preserved Revision G
helpers and guidance. The original masters and helpers remain intact; adaptations
are presentation copies with source-bound text and recorded provenance.

| Requirement | Current implementation and verification |
|---|---|
| Exact SVG masters | Catalog-pinned rectangle, pattern, figure-heading, crossing-gap and legend masters; output `kit-usage.json` records selected hashes and content-fit adaptations. |
| Typography | Exact DejaVu Sans and Mono TTF files, native advances, 28-unit component names, 24-unit references and at least 1.4em baseline spacing; Chromium checks actual glyph suppliers. A physical-view adapter adds fixed Latin/Greek/Cyrillic/symbol metrics from the original fonts while delegating original ASCII behavior unchanged. |
| Swatches and textures | Exact saved IDs, checked contrast and opaque label backing; an authored local key explains presentation choices without inventing model properties. |
| Relationship notation | Unarrowed native ownership; retained endpoint identities; independent routes have at least 15 units of visible-ink separation. Shared-parent fanout and marked nonconnecting crossings have explicit treatments. |
| Local key | Original ruled legend master with fitted heading/body cells, authored text and reserved space; routes and frames cannot intrude. |
| Readable navigation | The same complete SVG supports overview and native-size scrolling on desktop and narrow screens. Revealing a frame from the inspection tables preserves a 12px document margin for its visible ink. Navigation cannot change model or saved geometry. |
| Saved artifacts | Exact sources, identity registry, companions, used original masters and fonts accompany the SVG; reconstruction checks reject changed bytes or revisions. |

Astra's 2026-11-17 review found missing independent-route clearance enforcement
and an unframed appearance key. Both are repaired in the shared renderer.
`tests/test_composition_view.py` includes independently expected clearance
boundaries, crossing exceptions, the saved legend and refusal/save/reopen cases.
Local Chromium evidence and source pins are retained in the private work area;
the parity ledger distinguishes those checks from actual application acceptance.

This does not establish complete kit or workbench coverage. Component placement,
full drawing identification tables, other export formats and remaining existing
appearance compatibility remain open obligations. Actual Codex and ChatGPT
journeys remain separate required evidence. The initial
[walkthrough](composition-walkthrough.md) remains an interaction proposal; its
kit-usage record is not proof of a connected application.

The [physical host contract](composition-host-contract.md) carries these same
requirements into MCP Apps. Original-font loading, actual displayed glyph
suppliers and exact raw saved SVG bytes require separate evidence. A host that
cannot render the original fonts must report an unsupported view. The private
SDK experiment exercises this boundary; production component integration,
candidate-font coverage and actual-host acceptance remain open.
