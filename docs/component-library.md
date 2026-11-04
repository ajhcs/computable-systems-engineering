# Engineering component library

CSE includes 1076 independently addressable presentation components: 341 original icons, eight saved mechanical variants, 556 extracted palette components and assemblies, 103 artwork-only variants, and 68 exact sRGB color swatches. Every entry has a stable ID, a descriptive name, an editable standalone SVG, its source location and digest, its treatment and approval status, and an explicit engineering context. Nested assemblies also list their separately available children.

Open the [complete palette PDF](../assets/engineering-library/palette.pdf), [editable overview](../assets/engineering-library/palette.svg), [component index](../assets/engineering-library/index.json), or [Draw.io library](../assets/engineering-library/integrations/drawio/cse-all.xml). The prior accepted artwork and all 341 primary SVGs retain their exact bytes. All pulley/spring alternatives are retained without selecting an exclusive default.

## Find and use a component

Run from the plugin root, or use absolute paths to its scripts:

```sh
python3 scripts/icons.py list --query pulley
python3 scripts/icons.py list --sysml PortUsage
python3 scripts/icons.py show mech-spring-variant-c
python3 scripts/icons.py export --format drawio --ids mech-pulley-variant-c --out /path/to/project/presentation
python3 scripts/icons.py export --format svg --query microscope --out /path/to/project/presentation
python3 scripts/icons.py export --format kernspan --all --out /path/to/project/cse-components
python3 scripts/icons.py check
```

Selection uses ranked names, IDs and declared engineering facets. `list` returns at most 20 records by default, with a maximum of 50 and a catalog-bound cursor. `show` returns full details only for an exact ID. See the [agent command and UI review](component-agent-review.md) for explicit-ID exports, selection JSON and accessible shortlists. Exported `components.json` retains that metadata. Use the source SVG in vector editors for geometry changes. Labels, placement and object properties are editable in Draw.io; each icon's vector illustration is embedded intact as an image cell.

## Modeling context

| Family | SysML v2 context | SysML v1 context | CSE activity |
| --- | --- | --- | --- |
| Physical/logical equipment | PartDefinition, PartUsage | Block, PartProperty | Architecture and diagrams |
| People and roles | Explicit operational participant modeled with PartUsage | Actor or part, as declared | CONOPS and scenarios |
| Physical/procedural actions | ActionDefinition, ActionUsage | Activity, Action | Scenarios and functions |
| Ports and classifications | PortDefinition, PortUsage, InterfaceUsage, FlowUsage | Port, InterfaceBlock, ItemFlow | Interface architecture |
| Connections and routing | ConnectionUsage, InterfaceUsage, FlowUsage | Connector, ItemFlow, Dependency | Explicit endpoints and relations |
| Mathematics and forces | AttributeUsage, CalculationUsage, ConstraintUsage | ValueProperty, ConstraintBlock | Measures and engineering analysis |
| Containers | Explicit PartUsage ownership or ViewUsage membership | Parts or packages | Decomposition and view scope |
| Controls, statuses, warning marks, document glyphs, colors | Presentation/annotation; no automatic semantic assignment | Presentation/annotation | Diagrams and evidence |

These are applicability mappings, with per-entry rationale, rather than automatic transformations. The library artwork is not registered as formal SysML syntax. A gear can illustrate a declared part; it does not create a type, usage or interface. A junction, fork, merge, shared bus and route bundle require different model facts even if drawings share a visual motif. Preserve model IDs, ownership, endpoint roles, polarity, lead count, direction and multiplicity when applying a component. Do not infer these from a caption or color.

This distinction follows the [SysML 2.0 specification](https://www.omg.org/spec/SysML/2.0). Flow applicability uses the final `FlowUsage` name; see the [OMG naming resolution](https://issues.omg.org/issues/SYSML2_-417). Local circuit notation, safety severity drawings and technical illustrations retain their source meanings and limitations; the library supplies no blanket IEC/ISO/ISA conformity claim.

## Draw.io

Use **File → Open Library from → Device** and select `cse-all.xml`, or select a smaller family XML under `integrations/drawio/`. Drag each entry onto a canvas independently. The tooltip contains its stable ID. Edit Data retains `cseId`, treatment, source approval status and the initially `unbound` model binding. Bind to an explicit model element in your project's semantic ledger before treating it as a model-derived view.

The exporter follows the [documented custom-library format](https://www.drawio.com/docs/reference/format-custom-shape-library/): `mxlibrary` containing JSON with XML graph models. The SVG is embedded, so no network image dependency is required. Draw.io presentation files do not provide lossless SysML interchange. Geometry changes remain editable in the separate SVG master.

## Kernspan and other renderers

The [Kernspan adapter](../assets/engineering-library/integrations/kernspan/README.md) supplies a searchable Rust/egui module, an aspect-preserving atlas and metadata for all components. It matches the inspected Kernspan API (egui 0.36.2, image 0.25). The current application has a fixed sample atlas rather than a generic SVG-library importer; this module is an integration component for its UI, not a claim that the released application already loads the library automatically.

Its picker/draw API supplies presentation identity. Native model creation remains an explicit `architecture_canvas::declaration` with owner, kind, type and multiplicity, followed by Kernspan preview/apply. Connections need exact endpoints; ports need an explicit interface and direction. No model changes occur when an icon is selected or drawn.

Standalone SVGs and the versioned JSON index support document generation and other vector renderers. The screen atlas is a derivative; it does not replace editable masters. Font-dependent technical labels declare their source font families. Other applications' native editor round trips require application-specific checks.

## Verification and sources

`icons.py check` checks per-component hashes, ID uniqueness, SVG references, modeling-context records and adapter freshness. Regression tests exercise corruption rejection, original-byte preservation, Draw.io SVG/metadata round trips and export selection. The full CSE suite qualifies compatibility with the pinned parser and existing shared analyses; no model is generated merely by loading this library.

[Extraction records](../assets/engineering-library/sources/extraction.json) describe component isolation and measured SVG bounds. [Original sources](../assets/engineering-library/sources/) retain attributed observations and engineering limitations. Private reference images, old source archives and workstation paths are excluded. Package checks, rendered review and native application acceptance are separate evidence.
