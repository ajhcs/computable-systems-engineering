# RobotController: what is referenced, and what is owned?

The selected author IBD contains six application references: robot-state publication, collision detection, path planning, arm control, end-effector control and inverse kinematics. Their dashed outlines denote references. The transceiver xcvr is an owned part inherited from Wireless Device, with multiplicity1..*. It is private in the source model; the projection retains that visibility.

Six undirected native connectors each relate one application reference to the xcvr port of the transceiver. A seventh connector relates the transceiver’s proxy rf port to the boundary ant full port. DataPort is a displayed boundary full port owned by Device and inherited through Wireless Device and Controller. It has no connector in this selected IBD. An unconnected displayed port is not permission to invent a connection. No arrow or sequence order is inferred.

The paper’s Fig12(b) and §5.5 explain the application roles. The exact static author-report image is named by the native diagram ID. XML inherits through Device → Wireless Device → Controller → RobotController; the full source includes other ports, associations, constraints and behaviors outside this view. Fig15 describes a larger multi-network scenario and is provided as context, not a completed model conversion.

The v2 text preserves selected feature names, reference/owned distinction, visibility, bounds, undirected endpoints. Its explicitly named SelectedView lifts inherited features into the view context; source owners and full inheritance remain in the original/ledger. A direct inherited-private transcription failed linking, so this projection does not claim full inheritance equivalence. Legacy full/proxy and nested-end stereotypes remain in the ledger and trace comments; their complete v2 execution meaning is unproved. There is no control simulation or commercial deployment claim.

Sources: [pinned NIST model](https://github.com/rcandell/wireless-factory-sysml/tree/3be053a2dcdb3245754739d0440c442a3b617dad), [author paper](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=926484), [NIST data article](https://doi.org/10.6028/jres.123.018).
