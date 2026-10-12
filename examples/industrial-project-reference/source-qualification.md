# Two engineering research references: source qualification

Review candidates; engineer acceptance remains pending. Repository: /workspace/repos/builderbob/computable-systems-engineering on BuilderBob, origin https://github.com/ajhcs/computable-systems-engineering.git, unchanged HEAD b01ef01698450e5a47cc20f957fe93a09e9744b4. All acquisition, author-PDF rasterization, coding, parsing, rendering and tests ran on BuilderBob. Windows consumed exact Library bytes for image inspection.

| Project | Selected source and match | Why this reference |
|---|---|---|
| TUM xPPU | x-PPU/Models commit c3aedf66f3e9695e6a7751ae62d17c64b1bc373c, Papyrus Scenario15; Overview BlockDefinition diagram _IETdwBHREeaen93uATCTQQ; Bougouffa et al. chapter12 Fig.12.12, printed360/PDF26. | Seven direct composite modules of PPU establish clear owner/role/type/multiplicity examples. Containment and relationship organizations answer distinct questions over the same selected facts. |
| NIST Wireless Factory | rcandell/wireless-factory-sysml commit 3be053a2dcdb3245754739d0440c442a3b617dad; wireless.xml.zip; RobotController IBD _18_5_3_6410209_1526678072572_334874_14867. Exact static report JPEG has the same ID; paper Fig.12(b), PDF12. | Six references, a private inherited transceiver, four ports and seven undirected connectors exercise distinctions that ordinary box/arrow graphs lose. The topology and endpoint ledger retain the same selected endpoints. |

These are two distinct engineering research references. xPPU is a physical laboratory demonstrator; Wireless Factory is a generic engineering model, not evidence of a physical installation. Scenario variants are one xPPU project. Wireless Factory is distinct from NIST's central-fill pharmacy. Neither source establishes a commercial deployment claim. The selected structural slices do not close complex operational breadth.

## xPPU qualification and rights

[Official TUM demonstrator](https://www.mec.ed.tum.de/en/ais/forschung/demonstratoren/ppu/), [pinned repository](https://github.com/x-PPU/Models/tree/c3aedf66f3e9695e6a7751ae62d17c64b1bc373c), [English chapter12](https://doi.org/10.1007/978-3-030-13499-0_12), [chapter4](https://doi.org/10.1007/978-3-030-13499-0_4). Acquisitions retain exact URLs, byte counts and SHA256.

Native files remain unchanged: UML 344410 bytes, notation 2740102 bytes, DI105 bytes (empty XMI), plus .project. UML XMI20131001 with Papyrus Blocks namespace http://www.eclipse.org/papyrus/0.7.0/SysML/Blocks. A precise SysML minor version is not established. Actual applied Block stereotypes identify the selected classes; the whole UML document is not relabeled SysML. All external profile/ALF/Ecore references and original ISA88/OMAC/PackML behavior remain in original files, not reconstructed.

Full model inventory: 33 Block applications, 61 state machines,625 transitions,298 states,117 pseudostates,57 final states,344 properties,64 associations,52 operations,277 opaque behaviors and14 UML profiles. The selected PPU owns exactly seven composite properties, each UML multiplicity1..1. Overview notation depicts their eight classes and seven associations; property IDs are traced through association member ends, not falsely asserted as direct notation references.

Fig.12.11 printed359/PDF25 and chapter4 §4.3/Fig.4.17 PDF20 are broader physical/use-case context. Fig.12.12 includes many class compartments excluded from the bounded projection. The original embedded figure is decoded to PNG with its pixel content retained; full author pages are separately available. Its export revision is not proven to be the exact native commit; the selected classes, roles and compositions match.

Native model and its derivatives: GPL-3.0, full license included; this subtree is not repository MIT. Corresponding pinned source ZIP accompanies the private review bundle and offline viewer. Chapter12 and chapter4 are ©The Authors, CC BY4.0 with their stated third-party-image exceptions; inspected selected chapter12 figures have no exclusion credit. Figure extraction is marked and attributed. Native software GPL and publication CC BY are separate.

## Wireless qualification and rights

[Pinned repository](https://github.com/rcandell/wireless-factory-sysml/tree/3be053a2dcdb3245754739d0440c442a3b617dad), [English paper](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=926484), [data article](https://doi.org/10.6028/jres.123.018). Full upstream NIST notice/disclaimer is included with copies and derivatives.

Both wireless.xml.zip and wireless-v2.xml.zip contain83 members, including native semantic XML, proxy profiles and BINARY diagram-layout streams. “v2” is an archive revision, not SysML v2. The paper identifies SysML1.5; XML uses XMI20131001 and SysML20150709. The repository README describes MagicDraw18.4, paper18.5, main current export19.0v9, while the selected revision1 diagram retains18.5. Mixed tool/profile evidence is reported rather than collapsed to an invented exact original-export version.

Revision1 contains48 Block,16 ConstraintBlock,10 InterfaceBlock,12 FullPort,6 ProxyPort and156 NestedConnectorEnd applications;74 UML classes,75 ports,142 connectors/284 ends,123 associations,36 UML constraints. Revision2 adds one Block and revises layouts. The selected author diagram is matched to revision1. Its layout ID resolves to BINARY-3b6d1e3c-2a81-46aa-94d4-c55500999d21. A decoded parse copy adds a missing namespace declaration; exact original archive bytes remain preserved. The static author JPEG is extracted from html-report.zip; no legacy active report content executes, and that active HTML archive is excluded from the delivered bundle.

Selected topology: six public reference properties1..1; inherited private owned xcvr:Transceiver1..*; Transceiver rf:iRF proxy port and xcvr:iXcvr ordinary UML port; inherited boundary ant:iRF and DataPort:iApp full ports. All displayed port bounds1..1. Six connectors relate application references to the same xcvr.xcvr port; one relates xcvr.rf to ant. DataPort is displayed and unconnected. All seven nested endpoint paths resolve to the source partWithPort IDs. No flow direction is added. Device → Wireless Device → Controller → RobotController remains original inheritance.

Direct transcription of the inherited private xcvr failed pilot linking. The rejected model and12-error receipt are retained. The delivered formal RobotControllerSelectedView lifts displayed inherited features into a view context, preserves private visibility and endpoint topology, and records source owners/hierarchy in the ledger. It is not a replacement for the source class or proof of inheritance equivalence. Port definition identity is preserved; full/proxy/nested-end execution equivalence is not established. Source constraints are inventoried but not converted or evaluated.

Paper Fig.3 PDF6 and Fig.15 PDF15 are context, not additional completed views/projects. Combined PP/FT Limiting image is retained as research context only. Upstream software/documentation reuse notice is used; no blanket license is claimed for unrelated publisher material.

## Gates and remaining limits

Both bounded formal SysML v2 text models parse/link with the pinned pilot2025-09/kernel0.52.0. Native linked facts establish seven PPU compositions and18 Wireless features (7 roles,4 ports,7 connectors), including visibility, type, bounds and both linked endpoint paths. The xPPU TREE image is actual pilot output with an explicitly recorded bundled-Smetana fallback. Four modern SVG/PNG/draw.io readings are source-derived explanatory graphics, not formal-v2 graphical-conformance claims.

Independent checks reject16 meaningful mutations. Browser tests require expected source-linked primitive/label counts before checking font boxes, clipping, collisions and missing-graphic negatives. Actual rendered Library-consumed pixels are separately inspected. Draw.io is editable presentation, not lossless SysML interchange.

Native Papyrus/MagicDraw edit/save/reopen, external profile resolution, full-model conversion, complete graphical conformance, controller behavior/constraint simulation and user reading acceptance remain unrun/open. No source comments are resolved automatically.

Fraunhofer FUSION remains held out: source fetch, license and model/render match are unresolved. No restriction bypass, publication, deployment or new grant is performed.
