# Central-fill pharmacy structural reference drafts

These are bounded structural derivatives of the CentralFillPharmacy demonstration model distributed by [usnistgov/DiscreteEventLogisticsSystems at commit 7b09a59fc7e900177524f06f8a42dcc3d3c1aced](https://github.com/usnistgov/DiscreteEventLogisticsSystems/tree/7b09a59fc7e900177524f06f8a42dcc3d3c1aced). The associated report, [*Formalizing ISA-95 Level 3 Control with Smart Manufacturing System Models*, NIST GCR 19-022](https://doi.org/10.6028/NIST.GCR.19-022), was written by Leon F. McGinnis of the Georgia Institute of Technology under NIST award 70NANB15H234. The report acknowledges access to actual central-fill pharmacies; these selected views do not establish deployment or endorsement of this derivative work.

The source README identifies MagicDraw 18.5 SP1 and SysML 1.4. The retained source ledger records the exporter and profile namespace. Derived v2 text and historical native TREE artifacts use the existing SysML v2 Pilot 2025-09 / kernel 0.52.0 toolchain. This is a scoped transcription, not a complete language migration.

| View | Report figure | Selected roles | Owned parts | Referenced resources | Supplementary direct roles |
|---|---|---:|---:|---:|---:|
| [DemoCFP](DemoCFP/engineering-reading.md) | 6-3 | 4 | 4 | 0 | 5 |
| [HSFillSystem](HSFillSystem/engineering-reading.md) | 6-13 | 7 | 6 | 1 | 8 |
| [HFFillSystem](HFFillSystem/engineering-reading.md) | 6-24 | 8 | 7 | 1 | 10 |

The 19 selected roles are the retained source-diagram selection. A reference role is a declared feature of the selected definition; its resource is not an owned component. In the high-speed and high-flexibility views, VTS is a referenced resource. Optional A-frame, XSKU and manual-fill roles have multiplicity 0..*; dispensing fingers and robotic dispensing systems have multiplicity 1..*. Counts are model multiplicities, not measured equipment inventories or throughput claims. Unnamed conveyor roles retain explicitly identified derived aliases.

Each folder supplies:

- `model.sysml`, the selected 4/7/8-role v2 projection, and `semantic-ledger.json`, its structured source IDs, types, bounds, ownership distinctions and omissions.
- `engineering-reading.md`, explanatory `candidate.svg` and `candidate.png`, and editable presentation geometry in `candidate.drawio`. These containment readings do not depict product or control flows. Draw.io is not lossless SysML interchange.
- `supplementary-full-direct-properties.sysml`, the separately scoped 5/8/10-role projection. Its hash and scope are recorded in the ledger; it is not the selected source-diagram view or a whole-class conversion. Leaf types are identity-only declarations.
- Historical `native.facts.json`, `native.puml`, `native.layout.puml`, `native.svg` and `native.png` from the selected v2 TREE view. The layout PUML adds the explicit Smetana layout directive. These retain a distinct native-tool label and do not establish complete graphical conformance. Native PNG metadata embeds the same bounded generated PUML and generic PlantUML/Java/locale details; it contains no original source XML or private review paths.
- The complete `SOURCE-LICENSE.md` notice, retained in each derivative folder.

Original source archives, raw XML/layout fragments, report rasters, private browser logs and original parser receipts remain local and are not distributed. Source/layout hashes and IDs in the ledger identify the historical inputs; they do not ship those inputs or authenticate source truth or an engineer decision. No fresh comparison against the original archive, parser run, browser rendering, editor round trip or simulation is claimed by this package.

The explanatory SVG accessibility titles now say "owned parts and referenced resources" in place of "direct parts and shared references". Their descriptions, visible labels and geometry are unchanged. The candidate PNGs retain the historical bytes; they were not freshly rendered from these modified SVG files. Historical render evidence therefore does not bind the new SVG bytes.

Run the dependency-free package consistency check from the repository:

```sh
python3 scripts/check_pharmacy_source_safe.py
python3 -m unittest discover -s tests -p 'test_pharmacy_source_safe.py'
```

The check compares the released model declarations, ledger, retained native facts, explanatory SVG and draw.io for role identity, ownership and cardinality; verifies the supplementary model's recorded hash and direct-role agreement; and checks complete license notices and the file allowlist. Tests include rejected mutations. A pass establishes agreement within these supplied derivatives. It is not independent original-source verification, a fresh SysML parse, pixel/render validation, behavior execution or engineering acceptance.

The historical extraction and rendering scripts and their private evidence are not shipped as a public regeneration workflow. Independent source comparison requires obtaining the pinned original archive from the upstream repository and matching its version, selected IDs and author figures. Regenerating native TREE views additionally requires the existing pinned parser and renderer toolchain. The public checker needs neither private data nor those tools.

The [upstream license](https://github.com/usnistgov/DiscreteEventLogisticsSystems/blob/7b09a59fc7e900177524f06f8a42dcc3d3c1aced/LICENSE.md) permits copying and derivatives with its entire notice, acknowledgment and a modification notice. NIST is acknowledged as the source; retain the full per-folder notice. Do not infer contractor copyright status solely from NIST hosting.

Modification notices: 2026-10-03, selected directly owned source-diagram structural roles transcribed into bounded v2 definitions, with English readings and editable explanatory layouts. 2026-10-27, source-safe packaging excludes raw source and private receipts, clarifies provenance and historical evidence, changes explanatory SVG accessibility titles to distinguish owned parts from referenced resources, and adds local consistency checks. The engineer retains acceptance and presentation selection. These remain reference drafts.
