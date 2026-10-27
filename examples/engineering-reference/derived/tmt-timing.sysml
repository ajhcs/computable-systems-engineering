package TMTTimingDerived {
  private import ScalarValues::*;
  doc /* Derived 2026-10-01 from February 2017 TMT archive, SysML 1.4; not original v2 source. Selected Figures 7/8 requirement/constraint/bindings. Opaque simulation code and real evidence are not executed. */
  requirement <REQ_2_APS_0017> alignmentMaintenanceTime {
    doc /* Source imported requirement _2ca33d85-e793-40fa-9f3a-b3c90e37fd87__17_188f7b22-cc8f-4e5c-b35c-8e3fc63198fb. Original TMT_ID REQ-2-APS-0017. APS must support on-axis alignment in less than 30 minutes at a single elevation angle when all optics satisfy the alignment maintenance specifications. The English strict boundary is preserved as narrative; the source mathematical constraint below uses <=. No automated satisfaction of this whole requirement is asserted. */
  }
  constraint def MaxTimeConstraint {
    doc /* Source _18_0_2_baa02e2_1429562376319_87817_151513; owned rule _18_0_2_baa02e2_1429562376320_828902_151514 has body p1<=maxTime. Values are in seconds; original ports are Real. */
    in p1 : Real;
    in maxTime : Real;
    p1 <= maxTime
  }
  part def PEAS {
    attribute tFinal : Real {
      doc /* Source _18_0_4_baa02e2_1438808102180_452510_161842. Maintenance FinalDiffTime sets tFinal=t1-t0; the JavaScript implementation is not transcribed/executed. Unit: second. */
    }
  }
  part def MaintenanceAlignmentMaximumTime {
    doc /* Source _18_0_5_c0402fd_1464026223074_50206_149810. The paper depicts a refine relationship; that particular link is not verified in this selected archive. */
    attribute maintenanceAlignmentTimeLimit : Real default := 1800.0 {
      doc /* Source _18_0_5_c0402fd_1464026223153_484492_149834. Unit: second, class default in February 2017. */
    }
    constraint maintenanceAlignment : MaxTimeConstraint;
    bind maintenanceAlignment.maxTime = maintenanceAlignmentTimeLimit;
  }
  part scenario {
    part peas : PEAS;
    part maintenanceMaximum : MaintenanceAlignmentMaximumTime;
    bind maintenanceMaximum.maintenanceAlignment.p1 = peas.tFinal;
  }
}
