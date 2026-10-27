# Bounded native reference probes

These small Java probes call the installed pinned SysML Pilot2025-09 interactive API. Compile with the existing jupyter-sysml-kernel-0.52.0-all.jar into an ignored work directory, then run with that directory plus jar on the Java classpath. Use an absolute sysml.library path. No model-supplied code runs.

- ReferenceSemanticProbe: arguments library, model, JSON output. Parses/links selected model and inventories ActionUsage / SendActionUsage / AcceptActionUsage / fork/join / six successions. Sender is resolved through FeatureReferenceExpression.getReferent. It is an inventory, not a simulator.
- ReferenceVizProbe: arguments library, model, fully qualified selected element, view mode (e.g. ACTION), output prefix. Retains original generated PlantUML, inserts only !pragma layout smetana into a separate layout copy, and emits actual SVG/PNG with bundled PlantUML. Default native SVG can be an error image if dot is unavailable. Inspect the output and warnings. Graphical conformance is not established by a successful render.
- ReferenceEvalProbe: arguments library, accepted timing model, JSON output. Evaluates actual MaxTimeConstraint at1799/1800/1801; saved checks compare independently expected true/true/false and separate strict-English expectations. It is a bounded experiment, not arbitrary source computation or behavioral simulation.

The first successful outputs live in examples/engineering-reference-extension/validation and rendered. Probe APIs may emit deprecated Java/logging warnings; successful output is independently checked. Generated UUID links/evaluation IDs are not byte-stable or original source identifiers. Private initial failure logs remain in work/diagram-reference-expansion-20261002.
