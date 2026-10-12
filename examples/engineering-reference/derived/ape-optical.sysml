package APEOpticalDerived {
  doc /* Derived 2026-10-01 from 2023 APE reference archive, SysML 1.6; related to 2011 Cookbook Figure 20, not its exact export. Source connector structure and original ProxyPort records are retained in the source trace. Plain v2 ports are a partial transcription; interface contracts, conjugation and full proxy-port semantics are not translated. 2011 figure port arrow glyphs are not transcribed as item flows. */
  part def LensGroup1 {
    port in_oif {
      doc /* Source _15_1_bf10301_1210764986103_615550_6670. Original untyped SysML 1.6 ProxyPort. Derived plain v2 port retains the endpoint identity, not a complete proxy-interface semantic mapping. */
    }
  }
  part def OptoMechanicalBench {
    part lg1 : LensGroup1 {
      doc /* Source _15_1_baa02e2_1210774914160_880510_12061. Original visibility private; made public in this derived v2 fragment to resolve its nested connector end. */
    }
  }
  part def APE {
    port object_oif {
      doc /* Source _15_1_bf10301_1210680977392_846759_11441. Original untyped SysML 1.6 ProxyPort; derived plain v2 port omits complete proxy-interface semantics. */
    }
    part omb : OptoMechanicalBench {
      doc /* Source _15_0_3c00182_1203339836217_958479_4963. */
    }
  }
  part def APE_Telescope :> APE {
    doc /* Source _16_5_4_359f051f_1260448562906_634594_24892. Source nested connector _16_6_1_382e050d_1263291033453_363731_11568 reaches omb.lg1 through its NestedConnectorEnd propertyPath. */
    connect object_oif to omb.lg1.in_oif;
  }
  part def NasmythAdapter {
    port FoV_oif {
      doc /* Source _15_1_baa02e2_1212914971437_912712_9360. Original untyped SysML 1.6 ProxyPort. Derived plain v2 port retains the endpoint identity, not a complete proxy-interface semantic mapping. */
    }
  }
  part def UnitTelescope {
    part ada : NasmythAdapter {
      doc /* Source _15_1_baa02e2_1212914157343_515859_8565. Original visibility private; made public in this derived v2 fragment to resolve its context connector end. */
    }
  }
  part observatoryContext {
    private part ut3 : UnitTelescope;
    private part ape_t : APE_Telescope {
      doc /* Source _16_5_4_359f051f_1260449554968_992972_24991 redefines the original ape property. The 2011 figure labels this ape. */
    }
    connect ut3.ada.FoV_oif to ape_t.object_oif {
      doc /* Source _16_6_1_382e050d_1263290942250_179892_11452. Connector is not a directional item flow; telescope-light direction comes from the separate English narrative. */
    }
  }
}
