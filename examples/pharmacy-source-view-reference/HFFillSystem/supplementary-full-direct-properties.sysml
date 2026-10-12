// Derived from NIST CentralFillPharmacy model, pinned commit 7b09a59fc7e900177524f06f8a42dcc3d3c1aced.
// Changed 2026-10-03: bounded direct structural v1-to-v2 transcription. NIST acknowledged; SOURCE-LICENSE.md retained.
// Referenced leaf part definitions are identity-only scope declarations; their engineering details are NOT converted.
package PharmacyStructuralSlices {
  part def 'ToteBaggerSystem' { doc /* SOURCE-ID _18_5_3_3920140_1525049509017_128480_23335. Identity-only external type slice; not an empty complete definition. */ }
  part def 'AFrame' { doc /* SOURCE-ID _18_5_3_3920140_1525040787435_995128_22974. Identity-only external type slice; not an empty complete definition. */ }
  part def 'XSKU' { doc /* SOURCE-ID _18_5_3_3920140_1525040799549_506146_22976. Identity-only external type slice; not an empty complete definition. */ }
  part def 'ManualFillSystem' { doc /* SOURCE-ID _18_5_3_3920140_1526911472057_451021_16717. Identity-only external type slice; not an empty complete definition. */ }
  part def 'PharmacistStnTote' { doc /* SOURCE-ID _18_5_3_3920140_1525040835556_581625_22980. Identity-only external type slice; not an empty complete definition. */ }
  part def 'ToteConveyorSystem' { doc /* SOURCE-ID _18_5_3_3920140_1525041769648_590502_22983. Identity-only external type slice; not an empty complete definition. */ }
  part def 'RoboticDispSystem' { doc /* SOURCE-ID _18_5_3_3920140_1526911455197_337071_16715. Identity-only external type slice; not an empty complete definition. */ }
  part def 'TakeAwayConveyor' { doc /* SOURCE-ID _18_5_3_3920140_1524684935715_451618_16151. Identity-only external type slice; not an empty complete definition. */ }
  part def 'HFFillSystemController' { doc /* SOURCE-ID _18_5_3_3920140_1570835310915_658048_23549. Identity-only external type slice; not an empty complete definition. */ }
  part def 'VTS' { doc /* SOURCE-ID _18_5_3_3920140_1524150634956_746972_14050. Identity-only external type slice; not an empty complete definition. */ }
  part def 'HFFillSystem' {
    doc /* SOURCE-ID _18_5_3_3920140_1525033306441_211111_22594. Direct properties only; all omissions are in semantic-ledger.json. */
    public part 'toteBagSys' : PharmacyStructuralSlices::'ToteBaggerSystem'  {
      doc /* SOURCE-ID _18_5_3_3920140_1525091185146_459437_24296. Source role: toteBagSys; unchanged source role; aggregation composite. */
    }
    public part 'autoUofU' : PharmacyStructuralSlices::'AFrame' [0..*] {
      doc /* SOURCE-ID _18_5_3_3920140_1525091400756_151052_24552. Source role: autoUofU; unchanged source role; aggregation composite. */
    }
    public part 'xSKU' : PharmacyStructuralSlices::'XSKU' [0..*] {
      doc /* SOURCE-ID _18_5_3_3920140_1525091419588_337508_24623. Source role: xSKU; unchanged source role; aggregation composite. */
    }
    public part 'manualFillSystem' : PharmacyStructuralSlices::'ManualFillSystem' [0..*] {
      doc /* SOURCE-ID _18_5_3_3920140_1526999402276_416783_17078. Source role: manualFillSystem; unchanged source role; aggregation composite. */
    }
    public part 'pharmacist' : PharmacyStructuralSlices::'PharmacistStnTote'  {
      doc /* SOURCE-ID _18_5_3_3920140_1526999439531_564345_17149. Source role: pharmacist; unchanged source role; aggregation composite. */
    }
    public part 'toteConveyor' : PharmacyStructuralSlices::'ToteConveyorSystem'  {
      doc /* SOURCE-ID _18_5_3_3920140_1570890926644_882340_25483. Source role: (unnamed); derived alias for unnamed native role; aggregation composite. */
    }
    public part 'roboticDispSystem' : PharmacyStructuralSlices::'RoboticDispSystem' [1..*] {
      doc /* SOURCE-ID _18_5_3_3920140_1570893902845_101145_26779. Source role: roboticDispSystem; unchanged source role; aggregation composite. */
    }
    public ref part 'takeAwayConveyor' : PharmacyStructuralSlices::'TakeAwayConveyor'  {
      doc /* SOURCE-ID _18_5_3_3920140_1570895881593_935066_27688. Source role: takeAwayConveyor; unchanged source role; aggregation none. */
    }
    public part 'hFFillSystemController' : PharmacyStructuralSlices::'HFFillSystemController'  {
      doc /* SOURCE-ID _18_5_3_3af018f_1571498179856_739614_19804. Source role: hFFillSystemController; unchanged source role; aggregation composite. */
    }
    public ref part 'VTS' : PharmacyStructuralSlices::'VTS'  {
      doc /* SOURCE-ID _18_5_3_3af018f_1572369083244_629213_25523. Source role: VTS; unchanged source role; aggregation none. */
    }
  }
}
