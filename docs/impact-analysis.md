# Declared dependency impact and recheck selection

Use `scripts/impact.py` to compare retained revisions, trace possible consequences
through explicit dependencies, and propose checks from an independently retained
scope. The program does not execute those checks. A `pass` means that graph
traversal and selection completed for the supplied declared graph. Required
review and engineer acceptance remain `not_evaluated`.

## Use

```sh
python3 scripts/impact.py fingerprint examples/impact/scope.json
python3 scripts/impact.py check \
  --before examples/impact/baseline.json \
  --after examples/impact/candidate.json \
  --scope examples/impact/scope.json --scope-sha256 HASH_FROM_FINGERPRINT --json
```

The synthetic example changes a source premise. The reason path reaches its
requirement, scenario and delivered view; the global syntax, scenario and view
checks are selected. The unrelated declared review remains unselected. Preserve
the scope and its independently supplied digest before editing the candidate.
A candidate cannot remove a retained check by removing its target.

For existing native workflow models, capture snapshots without copying embedded
JSON by hand:

```sh
python3 scripts/impact.py native-snapshot baseline.sysml --revision baseline > baseline-impact.json
python3 scripts/impact.py native-snapshot candidate.sysml --revision candidate > candidate-impact.json
```

Repeat model arguments for an explicitly supplied bundle. This path reuses the
current native parser, stable workflow IDs, exact qualified names and frozen
input capture. It hashes each represented element's documentary record and
parsed native binding, the model bundle and the workflow context. It refuses
failed or unstable native capture. It does not require documentary workflow
completeness to extract a snapshot; unresolved native bindings stay visible.

Native dependencies, omitted native meaning, undiscovered imports and external
source truth remain unresolved. Consequently native snapshots broaden selection
to every retained check and return `unknown` from impact analysis. This is a
useful changed-record/reason-path aid with conservative selection; it does not
claim complete native transitive analysis or selective native regression.

A direct documentary adapter is also available:

```sh
python3 scripts/impact.py workflow-snapshot workflow.json --revision baseline \
  --model-sha256 MODEL_HASH --directions directions.json > baseline-impact.json
```

`directions.json` maps an existing documentary relation kind to
`from_depends_on_to` or `to_depends_on_from`. These are explicit engineer-supplied
dependency interpretations. The adapter never chooses a direction from a label
such as `supports`. It extracts source-basis references, evidence targets and
composed-view elements. Unmapped relation kinds and ambiguous `affects` links
remain unresolved. The direct adapter defaults to `complete: false`;
`--declared-complete` records a caller declaration, without discovering or proving
completeness. Trade-study dependencies are outside this adapter.

## Record contract

An `impact-snapshot-1.0` record contains exactly:

- `revision`: `id` and SHA-256 of the represented model revision.
- `nodes`: stable IDs mapped to `kind`, nullable `native_name`, and content
  `sha256`. Documentary kind labels do not execute semantics.
- `dependencies`: stable edge IDs mapped to `kind`, `dependent` and `dependency`.
- `complete`: an explicit Boolean declaration about supplied dependency coverage.
- `unresolved`: bounded descriptions of omitted or unresolved dependencies.

All edges point from the dependent to its dependency. Supported kinds are
`uses`, `derived_from`, `evidence_for`, `view_of`, `checks` and `typed_by`. Each
means that revising the dependency can require reconsidering the dependent. An
`evidence_for` edge identifies evidence that may become stale when its target
changes; it supplies no evidence verdict. No connector, containment, flow,
requirement-satisfaction or temporal semantics are inferred.

An `impact-scope-1.0` record contains a nonempty `checks` map. Each check has
`targets` and a Boolean `global` flag. Targets may include historical identities
that are deleted from the candidate. Global checks always remain selected.
No command, code or shell expression is stored or executed in this record.

Nodes added, removed or modified are change seeds. Added, removed or retargeted
edges seed their endpoints from both revisions. The reverse closure uses the
**union of baseline and candidate edges**, so deleting a dependency does not
hide its historical consequences. Mixing revision edges is intentionally
conservative: a path can identify a possible impact even when its edges did not
all coexist in one revision. Every hop reports its originating revision.

A sorted multi-source breadth-first traversal returns one deterministic shortest
reason path per reached identity. `change_reasons` identifies the node or edge
revision that seeded each path. Dependency cycles are permitted and terminate.
Equal-length alternative reasons are not all enumerated. This is reachability,
not proof that a real engineering effect occurs.

Missing dependency endpoints, missing retained check targets in both revisions,
unresolved dependencies, a false completeness declaration, or exceeded work cap
return `unknown` and select **every retained check**. Partial reason paths remain
visible. Unsupported versions or dependency kinds, malformed records and a stale
scope digest return `error`. None of these outcomes is successful review.

The fixed maxima are 4,096 nodes, 16,384 edges per snapshot and 1,024 retained
checks. Files use the existing 1 MB regular-file reader and reject duplicate
JSON keys. The traversal work budget is at most 100,000 units; traversed edges
and stored path hops both consume it. This bounds long-chain reason storage as
well as traversal. CLI `--max-work` may reduce the cap. Input SHA-256 values
identify supplied bytes; they authenticate no engineer decision or trusted
execution boundary.

## Source-informed design and tested limits

This increment is an original stdlib implementation. No upstream source
expression was copied into the verifier, and no new runtime dependency is
required. The following pinned implementations informed the design; they are
not dependencies, endorsements or evidence of complete SysML support.

| Source | Concrete component inspected | CSE use and boundary |
|---|---|---|
| [DemaConsulting SysML2Tools, MIT, `c6aa735e75b06982cf8b1805c11c82cafeeabe3d`](https://github.com/demaconsulting/SysML2Tools/tree/c6aa735e75b06982cf8b1805c11c82cafeeabe3d) | [`QueryEngine.cs` lines 245–452](https://github.com/demaconsulting/SysML2Tools/blob/c6aa735e75b06982cf8b1805c11c82cafeeabe3d/src/DemaConsulting.SysML2Tools.Core/Query/QueryEngine.cs#L245-L452): uniform-cost BFS, incoming-reference closure, optional undirected connector walk; [`QueryResult.cs` lines 89–123](https://github.com/demaconsulting/SysML2Tools/blob/c6aa735e75b06982cf8b1805c11c82cafeeabe3d/src/DemaConsulting.SysML2Tools.Core/Query/QueryResult.cs#L89-L123): structured depth, relation and far-endpoint identity. | Retain structured reason hops and cycle-safe shortest distances. CSE uses explicit declared direction, both revisions and independent recheck scope. It does not import connector roll-up or imply equivalent native coverage. |
| [ftsrg sysmlv2-validator, Apache-2.0, `9fd637c47f7ce92673f7df86e944a1570538a9ad`](https://github.com/ftsrg/sysmlv2-validator/tree/9fd637c47f7ce92673f7df86e944a1570538a9ad) | [`model_transformer.py` lines 140–181](https://github.com/ftsrg/sysmlv2-validator/blob/9fd637c47f7ce92673f7df86e944a1570538a9ad/scripts/model_transformer.py#L140-L181): explicit metamodel typing and guarded descendant closure; [`validation_pattern_utils.py` lines 145–171](https://github.com/ftsrg/sysmlv2-validator/blob/9fd637c47f7ce92673f7df86e944a1570538a9ad/scripts/validation_pattern_utils.py#L145-L171): reject conflicting same-name definitions. | Preserve explicit typed relations and reject unknown rule kinds instead of silently merging incompatible meanings. This increment does not load or execute arbitrary Refinery patterns. |
| [arikanatakan pmcontrols, MIT, `6ae775d67c4a81b3192a89ac49f27039bf405766`](https://github.com/arikanatakan/pmcontrols/tree/6ae775d67c4a81b3192a89ac49f27039bf405766) | [`network.py` lines 28–59](https://github.com/arikanatakan/pmcontrols/blob/6ae775d67c4a81b3192a89ac49f27039bf405766/pmcontrols/network.py#L28-L59): normalize IDs, reject absent predecessors, expose a precedence cycle; lines 62–78: predecessor/successor direction and forward/backward passes. | Explicit direction and missing-reference checks are useful. CPM scheduling assumes a DAG and computes schedule duration/slack; engineering impact can contain valid cycles. No scheduling, earned-value or trade-study claim is added. |

Actual upstream execution on the pinned source:

- `pmcontrols/tests/test_cpm.py`: 9 tests passed, including missing predecessor,
  cycle and duplicate rejection, schedule reference values and JSON result shape.
- The full pmcontrols suite also ran: 52 tests passed, one plotting test was
  skipped because the optional plotting dependency was absent. A separate probe
  changed only network topology: duration changed from 1 to 2 while the reported
  `input_hash` stayed identical. [`network.py` line 121](https://github.com/arikanatakan/pmcontrols/blob/6ae775d67c4a81b3192a89ac49f27039bf405766/pmcontrols/network.py#L121)
  hashes durations alone. CSE hashes nodes and dependency records and does not
  adopt that digest as a complete input identity.
- ftsrg utilities: all eight supplied pattern files parsed to 43 definitions,
  rendered and reparsed; a conflicting duplicate was rejected; cyclic descendant
  traversal terminated and retained every reachable class. These are utility
  smokes, not a Refinery or SysML API validation run.
- A negative ftsrg probe exposed a result boundary: `parse_check_output` in
  [`check_with_refinery.py` lines 163–177](https://github.com/ftsrg/sysmlv2-validator/blob/9fd637c47f7ce92673f7df86e944a1570538a9ad/scripts/check_with_refinery.py#L163-L177)
  treated the expected consistency prefix as valid/consistent even with exit
  status 42 and stderr `crashed`. Callers must preserve and gate actual process
  exit status independently; this behavior was not adopted.
- SysML2Tools has substantive source tests for minimum hop, cycles, mixed
  reference/connector budgets, source-side ports and owning-part roll-up in
  [`QueryEngineImpactTests.cs` lines 492–889](https://github.com/demaconsulting/SysML2Tools/blob/c6aa735e75b06982cf8b1805c11c82cafeeabe3d/test/DemaConsulting.SysML2Tools.Tests/Query/QueryEngineImpactTests.cs#L492-L889).
  No .NET SDK is installed in this environment, so those upstream tests were
  inspected but not executed. The tool CLI targets .NET 10; its core library
  targets .NET 8/9/10. Do not treat source inspection as runtime qualification.

The CSE regression suite exercises deletion and retargeting across revisions,
reverse direction, cycles, missing endpoints, retained deleted targets, scope
pinning, cap exhaustion, deterministic reasons, and documentary/native adapters.
Maintain upstream forks only if a future integration needs ongoing upstream
code changes; this independent small implementation does not warrant a fork.
