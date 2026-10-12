package APECompositionDerived {
  doc /* Derived 2026-10-01 from APE-ReferenceModel.mdzip 288a863025498a4d8bc8e945cfec640e6a90268c, SysML 1.6. The original is a professionally reverse-engineered and simplified reference of the real APE instrument, not certified as-built hardware. New v2 structural transcription of Figure 10 scope only. Apache-2.0 notices retained. */
  part def Segment {
    doc /* Source _15_0_baa02e2_1204997460087_185642_9681. Physical values omitted from this composition view. */
  }
  part def PositionActuator {
    doc /* Source _15_0_baa02e2_1204997471931_475271_9705. */
  }
  part def Mount {
    doc /* Source _16_6_1_38390512_1265838951058_526030_71009. */
  }
  part def ActiveSegmentedMirror {
    doc /* Source _15_0_bf10301_1202464929960_949157_5982. Three composition links directly from ASM. Do not move actuators inside Segment: the selected source model does not encode that allocation. */
    private part seg : Segment[61] {
      doc /* Source _15_0_baa02e2_1204997510902_964101_9752, lower=upper=61, composite. */
    }
    private part pact : PositionActuator[183] {
      doc /* Source _15_0_baa02e2_1204997513668_221125_9807, lower=upper=183, composite. */
    }
    private part mount : Mount {
      doc /* Source _16_6_1_38390512_1265838967762_750737_71036 is unnamed. mount is a new derived identifier; default multiplicity 1 is implicit in original. */
    }
  }
}
