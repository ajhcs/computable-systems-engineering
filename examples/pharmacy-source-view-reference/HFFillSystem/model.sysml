// NIST CentralFillPharmacy source acknowledged; SOURCE-LICENSE.md retained intact.
// Changed 2026-10-03: bounded author-diagram view projection from v1 to current v2.
// This is NOT complete class conversion. Omitted native members remain inspectable in the ledger.
// Leaf definitions are identity-only scoped declarations, not complete empty engineering definitions.
package PharmacySourceDiagramSlices {
  part def 'ToteBaggerSystem' { doc /* SOURCE-ID _18_5_3_3920140_1525049509017_128480_23335. Identity-only external type projection. */ }
  part def 'AFrame' { doc /* SOURCE-ID _18_5_3_3920140_1525040787435_995128_22974. Identity-only external type projection. */ }
  part def 'XSKU' { doc /* SOURCE-ID _18_5_3_3920140_1525040799549_506146_22976. Identity-only external type projection. */ }
  part def 'ManualFillSystem' { doc /* SOURCE-ID _18_5_3_3920140_1526911472057_451021_16717. Identity-only external type projection. */ }
  part def 'PharmacistStnTote' { doc /* SOURCE-ID _18_5_3_3920140_1525040835556_581625_22980. Identity-only external type projection. */ }
  part def 'ToteConveyorSystem' { doc /* SOURCE-ID _18_5_3_3920140_1525041769648_590502_22983. Identity-only external type projection. */ }
  part def 'RoboticDispSystem' { doc /* SOURCE-ID _18_5_3_3920140_1526911455197_337071_16715. Identity-only external type projection. */ }
  part def 'VTS' { doc /* SOURCE-ID _18_5_3_3920140_1524150634956_746972_14050. Identity-only external type projection. */ }
  part def 'HFFillSystem' {
    doc /* SOURCE-ID _18_5_3_3920140_1525033306441_211111_22594. Only 8 direct properties depicted by source diagram _18_5_3_3920140_1525090963217_762798_23919. Bounded view projection; not complete class conversion. */
    public part 'toteBagSys' : PharmacySourceDiagramSlices::'ToteBaggerSystem'  {
      doc /* SOURCE-ID _18_5_3_3920140_1525091185146_459437_24296. Source role: toteBagSys; unchanged source role; aggregation composite. */
    }
    public part 'autoUofU' : PharmacySourceDiagramSlices::'AFrame' [0..*] {
      doc /* SOURCE-ID _18_5_3_3920140_1525091400756_151052_24552. Source role: autoUofU; unchanged source role; aggregation composite. */
    }
    public part 'xSKU' : PharmacySourceDiagramSlices::'XSKU' [0..*] {
      doc /* SOURCE-ID _18_5_3_3920140_1525091419588_337508_24623. Source role: xSKU; unchanged source role; aggregation composite. */
    }
    public part 'manualFillSystem' : PharmacySourceDiagramSlices::'ManualFillSystem' [0..*] {
      doc /* SOURCE-ID _18_5_3_3920140_1526999402276_416783_17078. Source role: manualFillSystem; unchanged source role; aggregation composite. */
    }
    public part 'pharmacist' : PharmacySourceDiagramSlices::'PharmacistStnTote'  {
      doc /* SOURCE-ID _18_5_3_3920140_1526999439531_564345_17149. Source role: pharmacist; unchanged source role; aggregation composite. */
    }
    public part 'toteConveyor' : PharmacySourceDiagramSlices::'ToteConveyorSystem'  {
      doc /* SOURCE-ID _18_5_3_3920140_1570890926644_882340_25483. Source role: (unnamed); derived alias for unnamed native role; aggregation composite. */
    }
    public part 'roboticDispSystem' : PharmacySourceDiagramSlices::'RoboticDispSystem' [1..*] {
      doc /* SOURCE-ID _18_5_3_3920140_1570893902845_101145_26779. Source role: roboticDispSystem; unchanged source role; aggregation composite. */
    }
    public ref part 'VTS' : PharmacySourceDiagramSlices::'VTS'  {
      doc /* SOURCE-ID _18_5_3_3af018f_1572369083244_629213_25523. Source role: VTS; unchanged source role; aggregation none. */
    }
  }
}
