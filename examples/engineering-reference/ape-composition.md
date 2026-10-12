# ESO APE reference: ownership and multiplicity

APE is a real ESO instrument. Its public SE2/MBSE Challenge model is professionally reverse-engineered and simplified, not a certified as-built design.

**Original triple:** [Cookbook section 5.3.5, page 21](https://mbse.gfse.org/documents/SE2PracticesAndGuidelines.pdf#page=21), [Figure 10, page 22](https://mbse.gfse.org/documents/SE2PracticesAndGuidelines.pdf#page=22), and [pinned APE native model](https://github.com/Open-MBEE/OpenSE-Cookbook/blob/288a863025498a4d8bc8e945cfec640e6a90268c/Models/APE-ReferenceModel.mdzip). The Cookbook is January 2011; the September 2023 archive declares MagicDraw 2022x v7 / SysML 1.6. This is a traced element/concept match across revisions, not an identical export. Diagram ID: `_15_0_baa02e2_1204997376379_43454_9637`, ASM_ProductTree.

**Simplified reading:** ActiveSegmentedMirror composes 61 Segment instances, 183 PositionActuator instances and a Mount. Diamonds belong to the whole. seg and pact have exact lower/upper cardinalities 61 and 183. The original Mount role is unnamed with implicit multiplicity one; mount is a new identifier in the v2 transcription.

English explains three actuators per segment: 61 x 3 = 183. The selected formal product tree owns all 183 directly under the mirror. Moving three inside each Segment would add ownership/allocation absent from that selected structure. Keep engineering explanation distinct from explicitly modeled ownership.

**New artifacts:** [composition](rendered/03-ape-composition.png), [editable view](rendered/03-ape-composition.drawio), [derived v2](derived/ape-composition.sysml), [original-notation fragment](source/ape-composition.xml), [trace ledger](source/projection.json). Exact block/property/association IDs, original visibility, cardinalities and selected omissions are recorded.

Physical quantities, interfaces, navigation icons and photographs are omitted. Their omission does not imply absence from the system. The 2011 powerConsumption label evolved to power in the newer snapshot, so attributes are not mixed. Photographs are not copied. The four blocks and three composition relationships remain in a new layout.

The v2 fragment retains private seg/pact ownership and cardinalities. It adds no actuator-to-segment connections or behavior. Validation does not certify these quantities for the physical instrument. [Apache-2.0 attribution](notices/README.md) applies.

Documentation attribution: Robert Karban, Tim Weilkiens, Rudolf Hauber, M. Zamparelli, Rainer Diekmann and Andreas Hein, as listed in Cookbook page 2; model provenance is the ESO/GfSE/INCOSE SE2 MBSE Challenge team.
