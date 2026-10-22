# Synthetic remote sample station

A fictional water-quality sample logistics station demonstrates how one shared SysML model can support a concept, CONOPS, documentary operational scenarios and bounded computational checks. All needs, obligations, numerical limits, allocations, policies and components are invented demonstration choices. Nothing here establishes analytical validity, water treatment, contamination control, public-health suitability or real engineering acceptance.

Open [the offline gallery](generated/index.html), [the compact overview](generated/overview.svg), or the [full function tree](generated/function-tree/index.html). Edit [station.sysml](station.sysml) and regenerate; SVG and HTML are derived views, not competing engineering records.

The operator presents a labeled container to the intake panel. The receipt register records a provisional intake disposition and returns a receipt. A receipt can explicitly state **held, identity unresolved**; it never authorizes release. The operator reconciles an unreadable label before a corrected receipt. A courier later matches the pickup manifest and obtains the custody record. A custodian suspends intake before inspection; equipment repair and authorization to resume operation require separate evidence.

The concept considers a staffed local register and an offline station with local receipts and later synchronization. The example explores the second candidate without claiming a real selection. `Station` owns three candidate component usages: intake panel, receipt register and holding rack. No connector topology or item flows are invented. Component sizing, offline synchronization, label-authority policy, refrigeration, power budget and environmental limits remain qualitative gaps.

| Artifact | Meaning and limits |
| --- | --- |
| [station.sysml](station.sysml) | Authoritative shared concept/CONOPS/documentary-scenario source; three needs, three use cases, thirteen functions, three candidate components and three computable clauses. |
| [scope.json](scope.json) | Predeclared synthetic native-clause inventory; hash-bound, not authenticated engineer approval. |
| [semantic-ledger.json](semantic-ledger.json) | Explicit native composition, fictional documentary allocations, typed requirement traces and omitted semantics. Trace links are not satisfaction proofs. |
| [view-profile.json](view-profile.json) | Documentary function/sequence coverage: levels 0–2 and nominal/recovery/maintenance exchange lists. No timing is invented for these human exchanges. |
| [finite-scenarios.json](finite-scenarios.json) | Separately authored finite abstraction with typed inputs, atomic effects, data availability, explicit external waits, terminal states and completion sets. No SysML-to-executable conversion. |
| [finite-scope.json](finite-scope.json) | Independent artifact inventory for the finite review. Deleted or unclassified scenarios cannot pass this scope. |
| [finite-mapping.json](finite-mapping.json) | Checked finite-to-native ID/kind alignment. Additional finite hold/pause obligations elaborate documentary use cases; they do not equal the sampled native deadlines. |
| [generated/quantity-reading.json](generated/quantity-reading.json) | Exact display arithmetic for declared integer ticks, scale and clock units. No physical model or new arithmetic verifier. |

The native sampled monitor checks a requested intake receipt within two seconds and an elapsed-duration observation of at most four seconds within the same response window. The duration property is a bounded integer domain `0..20`, scale `1`, unit `second`; it is an observation, not an elapsed clock inferred by the model. The event monitor separately correlates overlapping container IDs with receipt IDs within an inclusive two-second deadline. The successful fixture deliberately responds to W002 before W001 and discharges W001 exactly at its deadline. This tests correlation rather than positional pairing.

| Supplied synthetic behavior | Expected result |
| --- | --- |
| `evidence-pass.json` | All three native clauses pass within the finite supplied window. |
| `evidence-late.json` | W001 responds at 2.1 seconds; event deadline fails. |
| `evidence-incomplete.json` | Incomplete capture returns unknown, never required success. |
| `evidence-no-receipt.json` | Boolean sampled response remains false; required receipt fails. |

The finite nominal case produces a typed receipt from available identity data and permits pickup only when the label is readable and service is not requested. The recovery case starts unidentified, enters a hold, allows external label correction at that hold, then produces identity data before recording a receipt. The maintenance case closes intake and requires an inspection record; its terminal state explicitly defers operational release. Data availability is checked, not payload truth or identity correctness. Explicit waits allow input change but promise neither arrival nor fairness. Required progress means some completion path exists from each reachable state, not that every schedule completes. Pointwise requirement consistency remains distinct from scenario execution.

`build.py` reruns native shape checks for all three skills, native positive/negative trace review, sampled variable-influence generation, finite positive/negative/capped reviews, scope deletion/unclassified controls and typed mappings. Event influence generation remains unsupported and visible in the report; generated influence witnesses are synthetic and are neither observed behavior nor FLIP coverage.

From the repository root, after installing the pinned parser with the documented repository installer:

```sh
python3 examples/engineering-gallery/water-sampling/build.py --output /workspace/path/to/fresh-gallery
python3 examples/engineering-gallery/water-sampling/build.py --check
```

The first command requires a fresh output directory. The second checks the tracked `generated/` build: source and engine hashes, exact generated-file inventory and hashes, and recomputed reports against predeclared expected outcomes. Source or engine edits require a fresh build, review and replacement of the generated artifact set. Outputs have no hidden timestamps or worktree-specific absolute paths. `build-manifest.json` identifies supplied bytes and dependencies; it is not an enforcing trust boundary.

Diagram readings follow the repository distinction between decomposition and ordered exchanges: the tree shows parentage only, and sequence lines show documentary message endpoints/order only. All formal content is source-derived; no raster image generation was used. SVG geometry is editable, but source changes belong in SysML before regeneration. Native editor edit/save/reopen, independent visual acceptance, physical feasibility, usability and stakeholder acceptance are separate gates. The local draft checker is not a protected runner.

Optional actual-browser rasterization adds a source-bound 1200 × 420 PNG for repository previews. It uses an existing Chromium installation and records its binary hash; no browser or library is installed. On the reviewed BuilderBob host:

```sh
python3 examples/engineering-gallery/water-sampling/render-preview.py \
  --output examples/engineering-gallery/water-sampling/generated \
  --browser /workspace/cache/builderbob/global-tools/browsers/chromium_headless_shell-1200/chrome-headless-shell-linux64/chrome-headless-shell \
  --library-path /workspace/cache/builderbob/global-tools/browser-deps/sysroot/usr/lib/x86_64-linux-gnu
```

Native `build.py` and `--check` do not require a browser. When the optional PNG is present, `--check` also checks its receipt, SVG and PNG digests. The rendering receipt proves which supplied bytes were rasterized; independent human pixel review remains separate. See the repository [gallery method](../../../docs/gallery-method.md) for official terminology and claim boundaries.
