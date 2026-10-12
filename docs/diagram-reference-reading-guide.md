# Selecting and validating matched engineering views

Read the engineering question before choosing a diagram grammar. Freeze the source version, selected element IDs and exclusions before drawing. Use a real source model and its author diagram; do not infer missing engineering from a textbook figure, a prettier graph or a later unrelated model.

The [central-fill pharmacy projections](../examples/pharmacy-source-view-reference/README.md) add a professional structural reference to the existing TMT/APE library. Three bounded source-diagram slices preserve 4/7/8 directly-owned roles (19 total), type identity, aggregation and multiplicity. The full source classes contain 5/8/10 roles; those are different scopes. Native v2 TREE output and explanatory containment readings are both supplied and explicitly classified.

For behavior, choose the reader's task: event lookup, outgoing transitions by active state, tracing a message exchange, or following parallel work. Compare different grammars against the same frozen ledger. An overview may group actions, but account for every selected source flow as internal or as a traced inter-group relationship; retain a complete view and named details. Do not claim the overview is a complete formal diagram or a proven behavioral abstraction.

For message scenarios, compare reader organizations as well as glyphs: a permission/status board, an actor responsibility network and an authority-provenance view answer different questions. Keep the complete global message order and source comments available as named support. A selected fragment must name its omitted context; show initial/final conditions where relevant and never imply completeness with an empty comments heading. Preserve permission versus occurrence, earlier versus later authority, and separate source-comment conditions without promoting them into formal guards.

Give every annotation an owner. Port names, source and destination identities, event/guard/effect text and object/control distinctions should be recoverable without remembering shape conventions or colors. Distinguish a model flow from a thin explanatory label leader. Preserve undirected source connectors; if an illustration adds publication-derived direction, state that status. Crossings must not imply junctions.

Historical electrical schematics offer useful design inspiration for monochrome trace continuity, named destinations and crossing/junction distinctions. [IEEE315-1975](https://standards.ieee.org/ieee/315/515/) is a historical source, not a current conformance claim for these views. Use the principle rather than copying copyrighted figures or treating a state transition as an electrical conductor.

Validation has separate gates:
- Parse/link with the repository's pinned SysML v2 toolchain and run the required repository suite.
- Extract native facts and native visualization in one parser session; compare source role/endpoint/ownership/counts independently.
- Reject meaningful mutations: swapped sender/receiver, wrong return state, lost parent exit, changed multiplicity/aggregation, reordered asynchronous messages, extra join completion or a source comment promoted to an executable guard.
- Assert expected source-linked graphics and label counts before measuring geometry; a blank graph can have zero collisions. Verify required actor, bundle, endpoint and condition regions in the exported PNG as well as the SVG DOM. Check direct SVG-image and inline/export routes separately when they serialize namespaces differently.
- Measure actual font boxes, endpoints, callout-to-callout intersections, trajectory-to-body intersections, crossings, line-to-label collisions and clipping. Restore each reported defect as a negative control, then inspect the actual PNG at the intended reading scale. Whole-canvas thumbnails are not evidence of legibility.
- When transferring between executors, use supported Library materialization and verify byte count, SHA256 and identity metadata on the consuming executor.
- Verify SVG, PNG, text, ledger, model and editable artifact carry the same selected scope. Resolve supplementary references from both the packaged and review folders; check the actual target bytes/hash and role counts. A path-exists check cannot establish the intended scope.
- Record edit/save/reopen, simulation and full conversion as separate gates. Parser acceptance, a draw.io file, a hash or a successful browser render does not establish those outcomes.

Apollo-style spatial mission illustrations should begin with editable vehicle/trajectory primitives and a source ledger. A later coarse SysML model can be a separate counterpart; it is not the semantic source of a richer historical illustration. Optional generated imagery may decorate a proven view, not define formal meaning.

Deliver the image, English reading, source/model/version links, editable artifact, mapping and receipts. Show original, previous and alternatives at matched scope; retain the original and previous draft. Report limitations and let the engineer select the presentation. Do not declare a style winner or faster comprehension without review.

## Engineering research references

[The xPPU/Wireless additions](../examples/industrial-project-reference/README.md) provide two distinct engineering research references. Count scenarios and archive revisions within their project, not as new projects. Select xPPU for direct composition/role/type/count questions; select Wireless RobotController for reference versus ownership, inherited/private features, port kind and undirected endpoint questions.

Pin the original native archive and keep UML, notation/DI or binary layout, applied stereotypes, external profiles and author diagram IDs together. “v2” in a filename is not evidence of SysML v2. Match the selected static rendering to the actual archive revision. Do not execute a legacy HTML report to view its static diagrams.

Preserve source visibility during transcription. If inherited private features cannot link, retain the failed evidence and declare a bounded view-context projection; never silently widen visibility or present the view type as the complete source class. Record unchanged original owners, inheritance and full/proxy/nested-port semantics separately. Inventory constraints before declaring which are omitted or evaluated.

Carry source-specific rights with derivatives: the xPPU model-derived subtree is GPL3; its author publication figure is separately CC BY4.0. Wireless derivatives carry the complete NIST notice/disclaimer. Corresponding originals remain available from pinned source links and the ignored review bundle. Formal v2 text, actual pilot TREE and modern source-model explanatory readings have distinct labels. User acceptance and native editor round-trip remain separate gates.

Do not place inherited boundary-port labels inside an owned component. Trace every port annotation to its source owner and depicted port; use a distinct leader style and do not count leaders as system connectors. Check every numbered connector label against the endpoint ledger. Distinguish a generic engineering reference model from an evidenced physical installation; structural role slices do not establish operational breadth.

For a complete selected operational activity, use [NIST electronics MakeCoupler](../examples/industrial-project-reference/nist-electronics-makecoupler/README.md). Retain distinct call instances even when they invoke the same behavior. ControlFlow ordering does not imply ObjectFlow data transfer; retain unwired and untyped pins, and distinguish native SysML 1.x models from explanatory drawings and v2 transcriptions. Many source called activities are placeholders, so a complete diagram inventory does not establish execution.
