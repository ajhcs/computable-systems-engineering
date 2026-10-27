// NIST source-derived selected topology; full notice accompanies this derivative.
// Explicit view-lifted inherited features. Source owner/hierarchy is in semantic-ledger.json.
// FullPort/ProxyPort/NestedConnectorEnd execution equivalence and full class inheritance are not asserted.
package WirelessRobotControllerSelected {
  port def iRF {}
  port def iXcvr {}
  port def iApp {}
  // Source type _18_5_3_4100178_1530286637742_187262_30316
  part def IKApp {}
  // Source type _18_5_3_4100178_1530286663159_613364_30381
  part def PathPlannerApp {}
  // Source type _18_5_3_4100178_1530286707117_776005_30446
  part def CollisionDetectApp {}
  // Source type _18_5_3_4100178_1530326212145_301884_17915
  part def StatesPublisherApp {}
  // Source type _18_5_3_4100178_1531609594857_802529_28663
  part def EEControlApp {}
  // Source type _18_5_3_4100178_1531609289390_348707_28131
  part def ArmControlApp {}
  part def Transceiver {
    // _18_5_3_4100178_1527439177867_744395_51342; legacy ProxyPort
    port rf : iRF [1..1];
    // _18_5_3_4100178_1527439336289_370866_51781; legacy 
    port xcvr : iXcvr [1..1];
  }
  // Selected source IBD context; a view type, not a replacement of the source class.
  part def RobotControllerSelectedView {
    // _18_5_3_4100178_1528246125416_795172_18482; source owner Wireless Device; private; PartProperty
    private part xcvr : Transceiver [1..*];
    // _18_5_3_4100178_1530286637762_402623_30319; source owner RobotController; public; ReferenceProperty
    ref part 'inverse Kinematics' : IKApp [1..1];
    // _18_5_3_4100178_1530286663203_516173_30384; source owner RobotController; public; ReferenceProperty
    ref part 'path Planner' : PathPlannerApp [1..1];
    // _18_5_3_4100178_1530286707141_516588_30449; source owner RobotController; public; ReferenceProperty
    ref part colDetect : CollisionDetectApp [1..1];
    // _18_5_3_4100178_1530326212176_39574_17918; source owner RobotController; public; ReferenceProperty
    ref part rStates : StatesPublisherApp [1..1];
    // _18_5_3_4100178_1531610070889_770225_29565; source owner RobotController; public; ReferenceProperty
    ref part eEControlApp : EEControlApp [1..1];
    // _18_5_3_4100178_1531610427908_349019_29907; source owner RobotController; public; ReferenceProperty
    ref part armControlApp : ArmControlApp [1..1];
    // _18_5_3_4100178_1528052652158_864306_44377; source owner Wireless Device; legacy FullPort
    port ant : iRF [1..1];
    // _18_5_3_4100178_1531347992299_198851_25687; source owner Device; legacy FullPort
    port DataPort : iApp [1..1];
    // Source connector _18_5_3_4100178_1528247576760_386908_20123; original owner Wireless Device; undirected
    connect xcvr.rf to ant;
    // Source connector _18_5_3_4100178_1530326485493_9830_18619; original owner RobotController; undirected
    connect rStates to xcvr.xcvr;
    // Source connector _18_5_3_4100178_1531349792679_717551_26838; original owner RobotController; undirected
    connect colDetect to xcvr.xcvr;
    // Source connector _18_5_3_4100178_1531611125055_71645_31072; original owner RobotController; undirected
    connect xcvr.xcvr to 'path Planner';
    // Source connector _18_5_3_4100178_1531611131074_332407_31096; original owner RobotController; undirected
    connect xcvr.xcvr to armControlApp;
    // Source connector _18_5_3_4100178_1531611138584_840155_31120; original owner RobotController; undirected
    connect xcvr.xcvr to eEControlApp;
    // Source connector _18_5_3_4100178_1531611143139_164723_31144; original owner RobotController; undirected
    connect xcvr.xcvr to 'inverse Kinematics';
  }
}
