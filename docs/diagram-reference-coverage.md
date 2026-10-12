# Diagram-generation reference coverage

Updated 2 October 2026. This work builds a source-grounded diagram reference skill/library. The engineer retains new system-model authoring and accepted engineering intent. Derivatives transcribe selected human-engineered sources; they do not introduce new requirements, operational facts, allocations, thresholds or simulation claims.

## Coverage and source gates

[SysML 2.0 §9.2.20/Table 34](https://www.omg.org/spec/SysML/2.0/Language/PDF#page=545) defines eight standard view families, while allowing additional user-defined views. Requirements, packages and definition/usage selections can be filtered General views; a matrix can be a Grid presentation.

| Standard family | Source-grounded reference | Current gate / next evidence |
|---|---|---|
| General | accepted APE composition and TMT timing; candidate APE Fig25 use cases | Accepted simplified presentations; actual pilot TREE retains selected composition on parsed v2. Match use-case relations before conversion. |
| Interconnection | accepted APE nested optical ports | Actual pilot INTERCONNECTION renders, but omits essential nested context/port labels: complete-reference fidelity fails. Retain original records and partial ProxyPort mapping. |
| Action Flow | TMT Fig4 Take SH Exposure; next Fig3 Broad Band Phasing | Fig4 exact fork/join/payload structure visually matched to February archive. Source-linked v2 parses; installed pilot ACTION rendered. Fig3 requires a separate exact revision/loop/guard check. |
| State Transition | accepted TMT maintenance lifecycle | Actual pilot STATE renders but omits composite Abort and Maintenance entry: complete-reference fidelity fails. Accepted source-style presentation retains them. |
| Sequence | TMT Fig6 maintenance duration analysis driver | Three asynchronous source messages, six actual native endpoint chains and four local order successions verified in the sixth untimed slice. Source min values are LiteralStrings; maxima have no value expressions. Duration mapping remains deliberately unexecuted. |
| Geometry | no selected defensible source yet | Do not invent shape/dimensions. Select an original model with verifiable geometry semantics and a compatible native renderer. |
| Grid | candidate APE allocation Fig60 with59/61; Flux Analysis79–82 | Match row/column identities and formal allocations/bindings to 2023 archive; preserve 2011 changes. Matrices must not imply missing allocations. |
| Browser | hierarchy already in accepted original model slices | Model-derived navigational tree/text outline can be scoped to source IDs. Native standard Browser rendering remains unverified. |

The [SysON2026.9 matrix](https://docs.obeosoft.com/syson/v2026.9.0/user-manual/key-features.html) marks the first four families partial and the latter four unsupported. SysON, Eclipse, Docker and Graphviz dot were not found in the checked installed command paths. No new paid tool, license or service is requested.

## Pinned-tool evidence

Keep accepted Pilot2025-09 / kernel0.52.0 and archive digest unchanged. Do not silently switch to a 2.1-beta-targeting release. Its installed interactive service advertises TREE, INTERCONNECTION, STATE, ACTION, SEQUENCE and MIXED; advertised modes are not proof of conforming output.

The default SVG probe returned a Graphviz error image although its result kind was SVG. Reject error-placeholder pixels. The actual installed pilot generated an ACTION PlantUML model view for Take SH Exposure; bundled PlantUML rendered SVG/PNG using the explicitly recorded Smetana layout fallback, with no new dependency. Inspect those pixels and renderer warnings. Generated UUID links are not stable original source IDs.

Retain three separate labels: original SysML v1 source, source-linked derived v2 model, and actual pinned-pilot visualization or simplified presentation. draw.io/XML validity does not establish native v2 graphical conformance.

## Validation contract

For each slice, check original pin/hash, source IDs/types/ownership/endpoints, matched publication figure and prose, explicit omissions/deltas, and source-to-v2 semantic correspondence. Run native syntax/linking/static validation and positive/negative source-fidelity checks. Inspect actual generated SVG/PNG; detect error placeholders, clipping, lost labels/glyphs and mismatched endpoints. A native edit/save/reopen round-trip is a separate result and remains unrun until an actual compatible editor is used.

Use numerical boundary checks only where source predicates, units and interpretation are known. Accepted TMT timing retains < versus <=. New exposure dit is Integer without a unit/bound in the selected type; no time limit is invented. Simulation requires a named engine, identified semantics, inputs and independently expected trace; none is currently claimed.

## Matched visual comparison

The supplied five directions are Technical Ledger, Instrument Record, Quiet Precision, Research Folio and Engineering Standard. Their source specimens/specification were materialized and hash-verified on BuilderBob. Originals remain private inspiration, with no redistribution grant.

The first ten-view composition/lifecycle checkpoint is extended to the planned twenty matched views across all four accepted slices, plus four dark-print light counterparts. After source gates pass, Technical Ledger and Engineering Standard provisionally cover the new Action/Sequence slices (four additional views); no shortlist winner is asserted. Freeze model IDs, all semantic text, coordinates, glyph types and canvas. Change presentation tokens only; retain structured text alternatives. Gate on semantic tuple equality, contrast, text/glyph bounds and measured narrow/wide/print/dark exports before scoring the supplied100-point rubric. No human-reading superiority or winner is claimed without review. Expand the shortlist to new families only after their source/v2 gates pass; eventually complete the specified20-view comparison without presenting it as all possible SysML diagrams.

The first actual native-view assessment is retained in examples/engineering-reference-extension/validation/native-view-assessment.json. Successful pixel generation and complete selected graphical fidelity are separate results. Actual native timing-expression evaluation passed three known boundary inputs; it is not behavior simulation.
