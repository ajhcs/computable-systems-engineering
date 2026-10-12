// Derived from NIST CentralFillPharmacy model, pinned commit 7b09a59fc7e900177524f06f8a42dcc3d3c1aced.
// Changed 2026-10-03: bounded direct structural v1-to-v2 transcription. NIST acknowledged; SOURCE-LICENSE.md retained.
// Referenced leaf part definitions are identity-only scope declarations; their engineering details are NOT converted.
package PharmacyStructuralSlices {
  part def 'VTS' { doc /* SOURCE-ID _18_5_3_3920140_1524150634956_746972_14050. Identity-only external type slice; not an empty complete definition. */ }
  part def 'HFFillSystem' { doc /* SOURCE-ID _18_5_3_3920140_1525033306441_211111_22594. Identity-only external type slice; not an empty complete definition. */ }
  part def 'SortSystem' { doc /* SOURCE-ID _18_5_3_3920140_1527522589685_489006_23809. Identity-only external type slice; not an empty complete definition. */ }
  part def 'HSFillSystem' { doc /* SOURCE-ID _18_5_3_3920140_1524683849396_707232_15345. Identity-only external type slice; not an empty complete definition. */ }
  part def 'DemoCFPController' { doc /* SOURCE-ID _18_5_3_3af018f_1564408726766_986848_16924. Identity-only external type slice; not an empty complete definition. */ }
  part def 'DemoCFP' {
    doc /* SOURCE-ID _18_5_3_3920140_1525033071601_357473_22464. Direct properties only; all omissions are in semantic-ledger.json. */
    public part 'VTS' : PharmacyStructuralSlices::'VTS'  {
      doc /* SOURCE-ID _18_5_3_3920140_1527522921619_948042_24158. Source role: VTS; unchanged source role; aggregation composite. */
    }
    public part 'toteSystem' : PharmacyStructuralSlices::'HFFillSystem'  {
      doc /* SOURCE-ID _18_5_3_3920140_1527522926217_269995_24188. Source role: toteSystem; unchanged source role; aggregation composite. */
    }
    public part 'sortSystem' : PharmacyStructuralSlices::'SortSystem'  {
      doc /* SOURCE-ID _18_5_3_3920140_1528313927664_843373_19107. Source role: sortSystem; unchanged source role; aggregation composite. */
    }
    public part 'puckSystem' : PharmacyStructuralSlices::'HSFillSystem'  {
      doc /* SOURCE-ID _18_5_3_3af018f_1570121058815_561458_31618. Source role: puckSystem; unchanged source role; aggregation composite. */
    }
    public part 'demoCFPController' : PharmacyStructuralSlices::'DemoCFPController'  {
      doc /* SOURCE-ID _18_5_3_3af018f_1571402400561_299057_16621. Source role: demoCFPController; unchanged source role; aggregation composite. */
    }
  }
}
