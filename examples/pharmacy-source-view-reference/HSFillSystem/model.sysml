// NIST CentralFillPharmacy source acknowledged; SOURCE-LICENSE.md retained intact.
// Changed 2026-10-03: bounded author-diagram view projection from v1 to current v2.
// This is NOT complete class conversion. Omitted native members remain inspectable in the ledger.
// Leaf definitions are identity-only scoped declarations, not complete empty engineering definitions.
package PharmacySourceDiagramSlices {
  part def 'PuckBaggerSystem' { doc /* SOURCE-ID _18_5_3_3920140_1524684598313_160586_16029. Identity-only external type projection. */ }
  part def 'CapWS' { doc /* SOURCE-ID _18_5_3_3920140_1524161356878_544194_17936. Identity-only external type projection. */ }
  part def 'ExceptionWS' { doc /* SOURCE-ID _18_5_3_3920140_1524161347422_701648_17934. Identity-only external type projection. */ }
  part def 'VialDispenseSystem' { doc /* SOURCE-ID _18_5_3_3af018f_1571499201272_879613_20106. Identity-only external type projection. */ }
  part def 'HSDispenseFinger' { doc /* SOURCE-ID _18_5_3_3920140_1525023159261_238207_20713. Identity-only external type projection. */ }
  part def 'PuckConveyorSystem' { doc /* SOURCE-ID _18_5_3_3920140_1525023113072_621197_20597. Identity-only external type projection. */ }
  part def 'VTS' { doc /* SOURCE-ID _18_5_3_3920140_1524150634956_746972_14050. Identity-only external type projection. */ }
  part def 'HSFillSystem' {
    doc /* SOURCE-ID _18_5_3_3920140_1524683849396_707232_15345. Only 7 direct properties depicted by source diagram _18_5_3_3920140_1531318915516_26898_19112. Bounded view projection; not complete class conversion. */
    public part 'pBSys' : PharmacySourceDiagramSlices::'PuckBaggerSystem'  {
      doc /* SOURCE-ID _18_5_3_3920140_1532524885026_574131_24126. Source role: pBSys; unchanged source role; aggregation composite. */
    }
    public part 'capWS' : PharmacySourceDiagramSlices::'CapWS'  {
      doc /* SOURCE-ID _18_5_3_3920140_1550524403060_222373_25314. Source role: capWS; unchanged source role; aggregation composite. */
    }
    public part 'xWS' : PharmacySourceDiagramSlices::'ExceptionWS'  {
      doc /* SOURCE-ID _18_5_3_3920140_1550524419700_363709_25344. Source role: xWS; unchanged source role; aggregation composite. */
    }
    public part 'vDWS' : PharmacySourceDiagramSlices::'VialDispenseSystem'  {
      doc /* SOURCE-ID _18_5_3_3af018f_1568127163256_528710_28684. Source role: vDWS; unchanged source role; aggregation composite. */
    }
    public part 'finger' : PharmacySourceDiagramSlices::'HSDispenseFinger' [1..*] {
      doc /* SOURCE-ID _18_5_3_3af018f_1568154046810_693419_33288. Source role: finger; unchanged source role; aggregation composite. */
    }
    public part 'puckConveyor' : PharmacySourceDiagramSlices::'PuckConveyorSystem'  {
      doc /* SOURCE-ID _18_5_3_3af018f_1570121073930_557791_31648. Source role: (unnamed); derived alias for unnamed native role; aggregation composite. */
    }
    public ref part 'VTS' : PharmacySourceDiagramSlices::'VTS'  {
      doc /* SOURCE-ID _18_5_3_3af018f_1571522802951_195557_22823. Source role: VTS; unchanged source role; aggregation none. */
    }
  }
}
