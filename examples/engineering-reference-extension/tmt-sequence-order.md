# TMT APS: analysis-driver signal exchange order

Saved parser/native/render reports describe historical checks on their exact inputs; this packaging change does not rerun them or independently validate original sources. Public current checks establish reviewed-derivative correspondence only.

[Herzig et al.,2017 Figure6 / section2.5, page7](https://www.omgsysml.org/TMT-APS_AO4ELT17_AnalyzingBehavior_final.pdf#page=7) shows an analysis driver sending Abort, Maintenance Alignment and Abort to PEAS. The English also discusses 60s and2000s intervals. [Pinned original model](https://github.com/Open-MBEE/TMT-SysML-Model/blob/87832a1657ccab023a90a6acfd0dff02d60e2b46/TMT.mdzip), February27,2017, SysML1.4 / MagicDraw18.0, archive SHA256 eb54c3105e4d894bb06378476f364bbf5cdb3bfad4cbf55f10fefacf6cad515f, supplies exact messages, events, represented properties and local event order. Interaction _18_0_5_baa02e2_1458099293885_800041_152044; diagram _18_0_5_baa02e2_1458099293891_41550_152049. Exact publication export commit is unverified.

**Selected engineering question:** Who sends which signal, and in what local order? All three original messages are asynchSignal. Each goes from analysisDriver to peas, and each lifeline's coveredBy sequence establishes Abort, Maintenance Alignment, Abort order. The two Abort messages are distinct events; sorting message IDs or native XML declaration order would get this wrong.

The selected source contains three DurationConstraints. Their minima contain LiteralString values60s or2000s, while their maximum Duration nodes have observations without value expressions. The paper's duration drawing/prose does not establish a completed v2 typed/units mapping for those native expressions. The original raw comparison evidence remains local, including all six min/max Duration records and their referenced observations. No original record serialization is bundled; this reference deliberately excludes timed assertions. No exact60/2000-second schedule, infinity assumption, bound reconciliation or simulation is invented.

**Derived v2:** A selected occurrence contains analysisDriver and private peas, named event occurrences, three typed messages, and four local event-order successions. Native participant implementations/types and the complete analysis context are omitted. Original Signal Maintenance Alignment gets the legal derived identifier MaintenanceAlignment. Original public analysisDriver and private peas property visibility is preserved. This is a selected event-order transcription, not a complete UML asynchSignal execution-equivalence mapping.

The pinned pilot implements these message constructs as FlowUsage with typed payloads and sourceEvent/targetEvent subsetting chains. Actual linked inspection resolves six endpoint chains to the correct participants/events, all three payload types and four local successions. Generic getSourceFeature/getTargetFeature accessors are empty for these message events; inspect their actual subsetting chains rather than manufacture a native validation pass.

**Views:** The [v2 derivative](derived/tmt-sequence-order.sysml),
[curated derivative facts](source/sequence-facts.json) and actual native pilot below
remain available. The earlier source-style SVG/PNG/draw.io family and its style
variants remain local because their footer refers to retained source XML. A
corrected presentation requires fresh supported rendering and pixel inspection;
no fresh rendering pass is claimed. Original native authority remains the pinned
external archive, with raw comparison evidence local.

The [actual native pilot Sequence PNG](rendered/pilot-tmt-sequence-order.png) preserves three directed exchanges but uses derived message-usage labels initialAbort/maintenance/finalAbort and omits the displayed payload signal names and source duration constraints. Original generated PlantUML is retained; Smetana is explicit only in the separate rendering copy. A successful render is not full graphical conformance.

Parser/static/linking pass has no findings and zero compiled CSE obligations. Historical original-source comparison stays local. Public derivative/native endpoint/order/payload checks are available, with mutations for reversed order, changed message sort, wrong native target or payload, invented timer and widened private visibility. These checks do not establish instrument behavior or complete v1/v2 migration. [Source notices](../engineering-reference/notices/README.md) apply.
