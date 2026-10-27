// NIST CentralFillPharmacy source acknowledged; SOURCE-LICENSE.md retained intact.
// Changed 2026-10-03: bounded author-diagram view projection from v1 to current v2.
// This is NOT complete class conversion. Omitted native members remain inspectable in the ledger.
// Leaf definitions are identity-only scoped declarations, not complete empty engineering definitions.
package PharmacySourceDiagramSlices {
  part def 'VTS' { doc /* SOURCE-ID _18_5_3_3920140_1524150634956_746972_14050. Identity-only external type projection. */ }
  part def 'HFFillSystem' { doc /* SOURCE-ID _18_5_3_3920140_1525033306441_211111_22594. Identity-only external type projection. */ }
  part def 'SortSystem' { doc /* SOURCE-ID _18_5_3_3920140_1527522589685_489006_23809. Identity-only external type projection. */ }
  part def 'HSFillSystem' { doc /* SOURCE-ID _18_5_3_3920140_1524683849396_707232_15345. Identity-only external type projection. */ }
  part def 'DemoCFP' {
    doc /* SOURCE-ID _18_5_3_3920140_1525033071601_357473_22464. Only 4 direct properties depicted by source diagram _18_5_3_3920140_1527186291936_534515_20996. Bounded view projection; not complete class conversion. */
    public part 'VTS' : PharmacySourceDiagramSlices::'VTS'  {
      doc /* SOURCE-ID _18_5_3_3920140_1527522921619_948042_24158. Source role: VTS; unchanged source role; aggregation composite. */
    }
    public part 'toteSystem' : PharmacySourceDiagramSlices::'HFFillSystem'  {
      doc /* SOURCE-ID _18_5_3_3920140_1527522926217_269995_24188. Source role: toteSystem; unchanged source role; aggregation composite. */
    }
    public part 'sortSystem' : PharmacySourceDiagramSlices::'SortSystem'  {
      doc /* SOURCE-ID _18_5_3_3920140_1528313927664_843373_19107. Source role: sortSystem; unchanged source role; aggregation composite. */
    }
    public part 'puckSystem' : PharmacySourceDiagramSlices::'HSFillSystem'  {
      doc /* SOURCE-ID _18_5_3_3af018f_1570121058815_561458_31618. Source role: puckSystem; unchanged source role; aggregation composite. */
    }
  }
}
