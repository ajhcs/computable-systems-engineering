# Connector palette rules

These are proposed local design-system conventions for the palette. The engineer selects the meanings that apply to a particular diagram; the shapes alone do not establish conformance to an external notation.

## Reference weights and patterns

At the palette's 300 × 180 symbol-card scale, use **s = 2.5 SVG units** for a primary connector and card outline. Scale the whole symbol proportionally. Shape outlines use 3 units (1.2s); fine annotation leaders use 1.5 units (0.6s) and gray so they do not look like additional connections. The tracer and striped, tiled, and hashed line treatments have their own intentional internal geometry.

The dotted connector uses complete circles of diameter **2s = 5**, on a center-to-center pitch of **4.8s = 12**. The illustrated run is symmetric, with both endpoint dots complete. The simple dashed connector uses **6s = 15** for each dash and **4s = 10** for each gap, a **3:2** dash-to-gap ratio. Its illustrated run starts and ends with complete dashes and uses butt caps. For a different run length, fit whole repetitions with balanced unused space rather than leaving clipped end marks.

Junction dots have diameter **3.6s = 9**. The nonconnecting-crossing examples interrupt one line by **6s = 15** between butt-ended segments. At a straight crossing the other stroke occupies s of that interval, leaving a total of 5s of white clearance, split evenly to either side. Use explicit gaps or bridges; do not rely on a plain crossing to communicate connectivity.

## Proposed connection meanings

- **T junction:** an unmarked T connects its three segments in this local convention. The T with a dot has the same connection; its dot explicitly marks the join.
- **Shared bus:** taps join one common physical or logical resource. **Connection bundle:** separately identified interfaces follow a common route without becoming one connection.
- **Ports:** an opaque white square is centered on the component boundary. At the 300 × 195 port-card scale its nominal size is **12s = 30 units**, its border is s, and its interior arrow uses **0.88s = 2.2 units**. An arrow pointing toward the component means input; an arrow pointing away means output. Two arrowheads mean both directions for the depicted interaction, not simultaneous activity; a blank square leaves direction unspecified. The arrow rotates with the component edge. An exterior `P-##` identifies the port. A classification tab attached to the continuous interface route carries the kind icon and code; the port square shows direction and does not itself encode kind. A port containing multiple features with different directions may need a table or more detailed depiction.
- **Terminations:** an end bar marks the end of the drawing without asserting connection status; a cross means intentionally unconnected, not a fault; a tagged ring with terminal bar is a drawing endpoint. A filled junction dot is not reused as a termination.
- **Asymmetric endpoints:** unlike heads are presented separately; the endpoint shapes alone do not establish bidirectional flow.

## Labels, identities and boundaries

Keep texture out of critical text using a compact backing matched to the underlying fill. Hollow arrowheads need an opaque interior; select the opaque fill appropriate to the surrounding background. Fine annotation leaders are distinct from connection strokes and carry no junction dot.

Assign a stable, unique ID to each connection or port; repeat the same ID only when referring to that same item within its defined namespace. An off-page reference includes both its connection ID and destination sheet/zone, such as `IF-01` and `S2/B4`.

A routing corridor is a reserved region, not a connection. The examples use a 12-unit (4.8s) opening centered on each entering or exiting route; with a 2.5-unit route and 1.5-unit boundary, the nominal visible clearance at the gate is 4 units. Use at least 1.5s (3.75 units) edge-to-edge clearance from a route to the remaining boundary, and at least 6s (15 units) between distinct routes. The sampled checks on these drawings bound those gaps below by 3.95 and 17.4 units, respectively. These are drawing clearances, not physical installation requirements. Gaps in the dashed boundary identify the entry and exit points without creating junctions.

## Approved extension references

Pattern hatching uses a 1.2-unit stroke, and dimension and extension lines use 1.5 units in the illustrated scale. The optional 4-unit emphasis line needs a meaning selected for the particular drawing. Use the role sizes and weights in [typography-spec.json](typography-spec.json) at the 1430-unit sheet scale: 36 bold with a 2-unit underline for titles; 26 regular for subtitles; 28 bold for components; 24 regular for attributes and notes; 26 bold for values; and 24 regular DejaVu Sans Mono for identifiers. Mechanical dimension values use 24 regular. Reserve underlining for drawing or sheet titles. Maintain existing label clearance and keep compact legacy specimens at their fitted size until individually re-laid out.

A generic junction does not define summation, decision, sequencing or synchronization. Separate interface IDs identify separate routes; blank hub ports leave direction unspecified. Label functional and physical groupings and routing corridors explicitly, because dashed borders can resemble each other. Collapsed and expanded boxes depict view states; the static SVG is not an interactive control.

The drawing-sheet example uses boxed fields and a zone grid. Its detail selection is at sheet 1 / C2 and its enlarged target at sheet 2 / B2, with reciprocal references. The typography example's separate off-page reference is a synthetic placeholder. See the individual study notes for source references and further limits.

## Figure text and notation keys

Keep explanatory prose, process commentary and reminders outside diagrams when labels and symbols already communicate the point. Retain identifiers, units, needed notation keys and any qualification essential to reading the view.

The matrix examples use an empty cell for a relationship not stated; it does not prove that a relationship is impossible. Shading marks the diagonal. The named references with the same ID identify the same continuation. Generic branching, merging and a shared route do not establish summation, sequencing or synchronization; those behaviors need a separate definition.

## Refined connection, container and drawing-sheet studies

Keep endpoint identities and direction visible. Separate connections remain separate at crossings; a crossing gap does not create a junction. Identify grouping boundaries and distinguish external elements from system contents. Drawing-sheet cross-references must resolve to the illustrated sheet and zone. The specific alternatives, source scope and local notation are recorded in the research notes.

## Routing and interface extensions

At the reference scale, keep separate connector ink at least 6s apart, labels at least 2s from connector ink, and adjacent port boxes and port-to-corner spacing at least 6s. Explicit joins and the immediate area of an intentionally gapped crossing are exceptions. A connection-label leader stops at least 2s short of the connector; an inline label leaves a straight connector gap with at least 2s padding at each side. A port-ID leader may touch its own port box. These are graphic clearances, not physical dimensions.

For fixed-endpoint orthogonal candidates, preserve endpoint, boundary, junction and clearance constraints first. Rank feasible candidates by fewer nonconnecting crossings, fewer bends, shorter Manhattan length, then lexicographically smaller vertex coordinates on the fixed half-s grid. Process stable, zero-padded connection IDs in ASCII order unless the order is explicitly locked. The policy ranks supplied candidates; it does not implement a router or prove a global minimum. See [routing-policy.json](routing-policy.json) for scope and failure cases.

The first local interface-kind glyphs use PWR, DAT, CTL, FLD, MEC and FNC as category codes. Interface and port identifiers remain separate from category codes and port direction. FNC is a dependency relation, with its arrow pointing from the dependent element toward the element it depends on; it is not assumed to be a physical transfer. Port arrays identify instances, a group does not imply a shared bus, [1..n] specifies an instance range and [0..1] specifies optional presence. COPY and SELECT are explicit illustrated block behaviors; a junction alone does not define them. Source notes and limits are in the accompanying interface-expansion study.

## Saved visual language

Classification tabs attach by their open side to a continuous connection, without creating a junction. Multiple tabs can share a route. FNC points from the dependent element to the element it depends on. The circular COPY node shows one input replicated to both outputs; SELECT shows one of two inputs selected by a separate selector. Detailed selector timing and fault behavior remain unspecified.

The neutral scale is white, 10%, 25%, 50%, 75% and black in encoded sRGB. Visibility changes foreground fill opacity to 100%, 75%, 50%, 25% or 10% for ghosting; outlines and text remain opaque. Gray dashed alignment guides are construction guides, not connections. The six layouts demonstrate edges, centers, baselines, columns, modular grids and radial arrangements.

The [controlled color palette](color-palette.md) contains 68 fixed sRGB swatches without assigned meanings. Each has a unique ID and specified text color; use an additional non-color cue when color conveys meaning. The proximity audit records 22 close pairs for review.

## Orthographic technical illustrations

Represent recognizable physical form through simplified, geometrically coherent views. Preserve identifying construction features and use drafting line conventions to distinguish visible geometry from supporting information.

Use one consistent projection per symbol. Omit decorative mechanical details. Make visible contours heavier than internal features and supporting lines. Use consistent frames without implying that the depicted objects share a real-world scale. Include technical annotations only when meaningful, and omit details that are unreadable at the intended display size. Limit detail to a primary shape, major physical features, one or two identifying details, and optional meaningful thin annotations.

For the accepted 35 × 35 mm illustration frame, use 0.525 mm visible contours and cut-wall outlines, 0.30625 mm internal features, and 0.175 mm dimension, extension, centerline and hidden-edge strokes. Use alternating long and short dashes for a centerline and short dashes for a necessary hidden edge. The [technical illustration specification](sections/orthographic-illustrations/line-spec.json) gives the local SVG values and pattern. These are palette values, not a claim of external-standard conformance. The four examples and their scope are in the [section notes](sections/orthographic-illustrations/README.md).
