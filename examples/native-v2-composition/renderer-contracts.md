# Parsed-v2 renderer contracts (preflight only)

No complete renderer is implemented for these families in this increment. The retained pilot views are tool-limit examples. Passing a structural preflight never establishes image fidelity, standard conformance, simulation, or timing.

A future renderer must consume linked native metamodel facts, with selected element ID/kind/owner and exact model/tool SHA-256. Each inventory below is an explicit audit object: `{"status":"resolved","value":[...],"evidence":["native element IDs", ...]}`. An empty list means inspected absence with element evidence; null/unknown is not absence. Required topology cannot be empty. Both unsupported and unresolved inventories must be present and empty. The Python preflight checks this envelope only; future adapters must additionally validate each typed fact and endpoint relation before rendering.

| Family | Required facts and boundaries | Current native gap |
|---|---|---|
| Action flow | Typed nodes; control and object flows; distinct endpoints/argument bindings; send-via reference chain and actual port kind; accepted payload types; fork/join pairing; guards. Source-untyped port stays untyped. No invented Ack fields. | Exposure pilot omits send-via annotation and the connected dit-to-payload object-flow glyph. |
| State transition | State hierarchy; initial nodes; transition endpoints; triggers, guards and effects; entry/exit annotations. Preserve composite Abort scope and Maintenance entry transition. | Pilot omits those selected hierarchy/transition/behavior facts. |
| Interconnection | Part ownership; ports and exact port kind; qualified endpoint chains; connectors; directions (explicit undirected is valid); visibility. Plain v2 port transcription cannot be called a preserved v1 ProxyPort. | Pilot optical view omits essential nested context and port labels. |
| Sequence | Participant/type identity (omission must be traced); message identity and payload type; sender/receiver event chains; participant-local order; explicit timing scope. Initial Abort, Maintenance Alignment and final Abort remain distinct exchanges. | Pilot shows usage names rather than the original payload names. Existing derivative is untimed; source duration records must remain source-only. |

Reject source-v1 redraws relabeled as v2, strings inferred from image labels, missing typed facts, unknown port kinds, dangling endpoints, invented guards/units/timeouts, and incomplete required inventories. Geometry/Grid/Browser remain outside these contracts. Future graphical output needs a separate model-to-primitives correspondence validator, negative mutations, and actual pixel inspection. No native fidelity claim may be borrowed from the composition TREE proof.
