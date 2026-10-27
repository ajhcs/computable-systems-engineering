// Derived from NIST CentralFillPharmacy model, pinned commit 7b09a59fc7e900177524f06f8a42dcc3d3c1aced.
// Changed 2026-10-03: bounded direct structural v1-to-v2 transcription. NIST acknowledged; SOURCE-LICENSE.md retained.
// Referenced leaf part definitions are identity-only scope declarations; their engineering details are NOT converted.
package PharmacyStructuralSlices {
  part def 'PuckBaggerSystem' { doc /* SOURCE-ID _18_5_3_3920140_1524684598313_160586_16029. Identity-only external type slice; not an empty complete definition. */ }
  part def 'CapWS' { doc /* SOURCE-ID _18_5_3_3920140_1524161356878_544194_17936. Identity-only external type slice; not an empty complete definition. */ }
  part def 'ExceptionWS' { doc /* SOURCE-ID _18_5_3_3920140_1524161347422_701648_17934. Identity-only external type slice; not an empty complete definition. */ }
  part def 'TakeAwayConveyor' { doc /* SOURCE-ID _18_5_3_3920140_1524684935715_451618_16151. Identity-only external type slice; not an empty complete definition. */ }
  part def 'VialDispenseSystem' { doc /* SOURCE-ID _18_5_3_3af018f_1571499201272_879613_20106. Identity-only external type slice; not an empty complete definition. */ }
  part def 'HSDispenseFinger' { doc /* SOURCE-ID _18_5_3_3920140_1525023159261_238207_20713. Identity-only external type slice; not an empty complete definition. */ }
  part def 'PuckConveyorSystem' { doc /* SOURCE-ID _18_5_3_3920140_1525023113072_621197_20597. Identity-only external type slice; not an empty complete definition. */ }
  part def 'VTS' { doc /* SOURCE-ID _18_5_3_3920140_1524150634956_746972_14050. Identity-only external type slice; not an empty complete definition. */ }
  part def 'HSFillSystem' {
    doc /* SOURCE-ID _18_5_3_3920140_1524683849396_707232_15345. Direct properties only; all omissions are in semantic-ledger.json. */
    public part 'pBSys' : PharmacyStructuralSlices::'PuckBaggerSystem'  {
      doc /* SOURCE-ID _18_5_3_3920140_1532524885026_574131_24126. Source role: pBSys; unchanged source role; aggregation composite. */
    }
    public part 'capWS' : PharmacyStructuralSlices::'CapWS'  {
      doc /* SOURCE-ID _18_5_3_3920140_1550524403060_222373_25314. Source role: capWS; unchanged source role; aggregation composite. */
    }
    public part 'xWS' : PharmacyStructuralSlices::'ExceptionWS'  {
      doc /* SOURCE-ID _18_5_3_3920140_1550524419700_363709_25344. Source role: xWS; unchanged source role; aggregation composite. */
    }
    public ref part 'takeAwayConveyor' : PharmacyStructuralSlices::'TakeAwayConveyor'  {
      doc /* SOURCE-ID _18_5_3_3af018f_1568123780655_213885_28016. Source role: takeAwayConveyor; unchanged source role; aggregation none. */
    }
    public part 'vDWS' : PharmacyStructuralSlices::'VialDispenseSystem'  {
      doc /* SOURCE-ID _18_5_3_3af018f_1568127163256_528710_28684. Source role: vDWS; unchanged source role; aggregation composite. */
    }
    public part 'finger' : PharmacyStructuralSlices::'HSDispenseFinger' [1..*] {
      doc /* SOURCE-ID _18_5_3_3af018f_1568154046810_693419_33288. Source role: finger; unchanged source role; aggregation composite. */
    }
    public part 'puckConveyor' : PharmacyStructuralSlices::'PuckConveyorSystem'  {
      doc /* SOURCE-ID _18_5_3_3af018f_1570121073930_557791_31648. Source role: (unnamed); derived alias for unnamed native role; aggregation composite. */
    }
    public ref part 'VTS' : PharmacyStructuralSlices::'VTS'  {
      doc /* SOURCE-ID _18_5_3_3af018f_1571522802951_195557_22823. Source role: VTS; unchanged source role; aggregation none. */
    }
  }
}
