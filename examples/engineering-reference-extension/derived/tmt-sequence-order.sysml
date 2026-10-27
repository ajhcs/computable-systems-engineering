package TMTSequenceOrderDerived {
  doc /* Selected message order from original SysML1.4 TMT Interaction _18_0_5_baa02e2_1458099293885_800041_152044, matching paper Figure6. Duration constraints deliberately remain source-only: min values are LiteralString 60s/2000s while maxima lack value expressions. This is not a timed scenario or simulation. */
  item def Abort { doc /* Source Signal _18_0_4_baa02e2_1435196367610_837152_180594. */ }
  item def MaintenanceAlignment { doc /* Source Signal _18_0_4_baa02e2_1437066483571_319242_152444; original name Maintenance Alignment. */ }
  occurrence maintenanceMessageOrder {
    doc /* New selected interaction occurrence; full analysis context and participant implementations omitted. MessageUsage does not assert a complete UML asynchSignal execution-equivalence mapping. */
    part analysisDriver {
      doc /* Lifeline _18_0_5_baa02e2_1458099294143_628657_152079 represents public original property _18_0_5_baa02e2_1454128060627_462855_170075. Selected type implementations omitted. */
      event occurrence initialAbortSent;
      then event occurrence maintenanceSent;
      then event occurrence finalAbortSent;
    }
    private part peas {
      doc /* Lifeline _18_0_5_baa02e2_1458099294144_32845_152081 represents private original property _17_0_2_3_41e01aa_1389728908413_724070_61695. Original visibility retained. */
      event occurrence initialAbortReceived;
      then event occurrence maintenanceReceived;
      then event occurrence finalAbortReceived;
    }
    message initialAbort of Abort from analysisDriver.initialAbortSent to peas.initialAbortReceived {
      doc /* Source asynchSignal Message _18_0_5_baa02e2_1458099294136_642396_152078; event pair 152086 / 152087. */
    }
    message maintenance of MaintenanceAlignment from analysisDriver.maintenanceSent to peas.maintenanceReceived {
      doc /* Source asynchSignal Message _18_0_5_baa02e2_1458099294136_802828_152076; event pair 152089 / 152090. */
    }
    message finalAbort of Abort from analysisDriver.finalAbortSent to peas.finalAbortReceived {
      doc /* Source asynchSignal Message _18_0_5_baa02e2_1458099294136_95702_152077; event pair 152092 / 152093. */
    }
  }
}
