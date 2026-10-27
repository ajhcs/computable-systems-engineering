package TMTExposureDerived {
  private import ScalarValues::*;
  doc /* Source-linked transcription of TMT February 2017 SysML 1.4 activity Take SH Exposure, source _17_0_2_3_41e01aa_1377716303952_671385_42761, matching 2017 paper Figure 4. This is a selected derivative, not a new engineering design or a complete migration. */
  item def SH_Take_exposure_Cmd {
    doc /* Original Signal _17_0_2_3_41e01aa_1377706340501_676597_37166; Integer attribute dit _18_0_4_baa02e2_1439589630400_217011_150200. Units are not supplied by the selected type. */
    attribute dit : Integer;
  }
  item def SH_Take_exposure_Ack {
    doc /* Original Signal _17_0_2_3_41e01aa_1378924275075_915265_43256 has no owned payload attribute in this archive. Paper prose describes an image payload; no image field/type is invented here. */
  }
  part def PEASContext {
    doc /* New lexical context for the selected derivative; the reusable source Activity is transcribed as one nested action usage so its original onPort is accessible in the PEAS context. The original reusable Activity is in Cmd_SH; its onPort references PEAS2SHOut. Complete PEAS architecture, interface contracts, other calls and simulation implementations are omitted. */
    port PEAS2SHOut {
      doc /* Original untyped Port _17_0_2_3_41e01aa_1382548607674_333485_74722. No destination component or new interface contract is asserted. */
    }
    action takeSHExposure {
      in attribute dit : Integer {
        doc /* Original in-default Parameter _18_0_4_baa02e2_1437598234574_12301_170362, parameter node _18_0_4_baa02e2_1437598234583_903659_170363 and ObjectFlow _18_0_4_baa02e2_1437598422630_384460_170544 to send argument p _18_0_4_baa02e2_1437598400072_462138_170530. Constructor argument replaces this selected pin flow; no payload unit/bounds are invented. */
      }
      action sendCommand send new SH_Take_exposure_Cmd(dit) via PEAS2SHOut {
        doc /* SendSignalAction _17_0_2_3_41e01aa_1383810481906_821693_75583. */
      }
      action awaitAck accept SH_Take_exposure_Ack {
        doc /* AcceptEventAction _17_0_2_3_41e01aa_1383810483618_843330_75595; signal event _17_0_2_3_41e01aa_1383810507094_725092_75617. No receive port was specified on this original action. */
      }
      fork exposureFork;
      join exposureJoin;
      first start then exposureFork;
      first exposureFork then sendCommand;
      first exposureFork then awaitAck;
      first sendCommand then exposureJoin;
      first awaitAck then exposureJoin;
      first exposureJoin then done;
    }
  }
}
