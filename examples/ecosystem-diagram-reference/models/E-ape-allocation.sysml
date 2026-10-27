package ApeAllocation {
 port def ControlContract { doc /* Source UML Interface _16_6_1_244503e7_1263493734875_132468_15222; operations excluded from selected allocation view. */ }
 part def Logical {
  doc /* controlContract is an explicit representative usage of source UML Interface ASMLCS_Control_if, not a recovered source-owned port. */
  port controlContract : ControlContract { doc /* Source _16_6_1_244503e7_1263493734875_132468_15222 representative usage; not source-owned port. */ }
  port imData { doc /* Source _16_6_1_244503e7_1263493581062_706108_15145; source public port, implicit UML multiplicity [1]. */ }
 }
 part def Lan { port fpCtrlLan { doc /* Source _16_6_1_244503e7_1263495171687_871359_16235; source public port, implicit UML multiplicity [1]. */ } port fpImcsLan { doc /* Source _16_6_1_244503e7_1263495509640_910005_16475; source public port, implicit UML multiplicity [1]. */ } }
 part def Protocol { port ccs { doc /* Source _16_6_1_3831050f_1263583514718_266101_19151; source public port, implicit UML multiplicity [1]. */ } port tcpIp { doc /* Source _16_6_1_3831050f_1263583499203_313131_19135; source public port, implicit UML multiplicity [1]. */ } }
 part AllocationView {
  part logical : Logical;
  part lan : Lan;
  part protocol : Protocol;
  allocation EA01 allocate logical.imData to protocol.tcpIp { doc /* source XMI _16_6_1_3831050f_1263583532875_901339_19165 */ }
  allocation EA02 allocate logical.controlContract to protocol.ccs { doc /* source XMI _16_6_1_3831050f_1263583574796_723624_19192 */ }
  allocation EA03 allocate logical.imData to lan.fpImcsLan { doc /* source XMI _16_6_1_3831050f_1263583418312_3805_19081 */ }
  allocation EA04 allocate logical.controlContract to lan.fpCtrlLan { doc /* source XMI _16_6_1_3831050f_1263583452296_216920_19094 */ }
 }
}
