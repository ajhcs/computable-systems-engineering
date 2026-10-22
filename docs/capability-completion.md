# Supported capability completion and verification

This records the bounded completion increment against base `e9221108092311a70c26195e72caa7b39acb7f99` (2026-10-22). It is a capability audit and reproducible verification contract, not engineering acceptance, a full SysML implementation, or completion of every phase in the architecture plans.

The model-first plan supersedes the earlier JSON-primary architecture proposal. Native SysML remains authoritative in the default drafting workflow. The finite JSON verifier is an explicitly separate opt-in model: no command here translates native actions, prose scenarios, or V1 records into executable finite behavior.

| Workflow | Implemented computation | Command / evidence | Remaining boundary |
|---|---|---|---|
| Three independent V1 drafting skills | Record structure, references, completeness and explicit numeric observations | `python3 scripts/check.py`, standalone concept/CONOPS/scenario suites | Prose exchanges have no executable guards/effects; assessments are declared findings. |
| SysML concept, CONOPS, scenario drafting | Pinned Pilot syntax/reference validation and minimal selected draft shape | `python3 scripts/sysml.py examples/sysml/concept.sysml --syntax-only --kind concept` (substitute conops/scenario) | Shape is not realistic operations, complete coverage, or engineer acceptance. |
| Native controlled sampled requirements | CSE controlled grammar, bound Boolean/bounded integer observations, exact clock and finite-window monitor | `python3 scripts/sysml.py examples/sysml/ack.sysml --manifest examples/sysml/ack-manifest.json --evidence examples/sysml/ack-evidence.json --review` | A passing supplied trace is not state-space consistency, realizability, implementation correctness, or native constraint evaluation. |
| Native correlated events | Exact timestamps, correlation IDs, distinct pending triggers, inclusive deadlines and explicit capture horizon | Same command with `correlated-events` files | No-trigger, incomplete capture, unfinished deadline and limits remain non-success. |
| Native bounded quantities and bundles | Integer ticks, exact declared unit/scale checks; supplied cross-file namespace/import resolution and per-file provenance | Same command with `quantity` files; `composed-parts.sysml composed-requirement.sysml` plus composed manifest/evidence | No implicit conversion, native unit-expression evaluation or unrestricted inheritance. |
| Finite JSON consistency | Every allowed input assignment has some jointly satisfying controlled assignment under input-only applicability | `python3 scripts/verify.py examples/verifier/valid.json --review --json --detail` | Single-instant joint satisfiability, not a reactive controller or temporal realization. |
| Finite JSON scenario execution | Explicit guards, effects, persistent data availability, external change points, terminals and existential completion from every reachable state | Same command; `--scenario S1` focuses scenario execution | No payload evaluation or fairness/inevitable completion; no native SysML scenario compilation. |
| Finite independent review inventory (this increment) | Exact external requirement/scenario inventory, global checks under focus, artifact/dependency identity and explicit analyzed scenario IDs | Same command with `--manifest PATH` | Scope identity is not authenticated acceptance; candidate/source revisions and semantic requirement meanings still need independent governance. |
| Native identity refusal (this increment) | Missing resolved identity on a short-ID element reports an error; unnamed computational bindings report unsupported; malformed extracted record/diagnostic collections report contract errors | `python3 -B tests/test_sysml_contract.py` | Pilot warning severity alone does not imply valid usable extraction. No qualified names are synthesized. |
| Context, changes, human views | Parsed selected context, conservative structural/documentation diff and generated presentation | `scripts/sysml_view.py`, `scripts/sysml_diff.py`, `scripts/sysml_present.py`; their existing suites | Context is not a verification input; diff impact is conservative and views do not override native model meaning. |
| Synthetic variable influence | Bounded one-property/one-sample witness pairs replayed through a monitor | `python3 scripts/sysml_testgen.py examples/sysml/ack.sysml --manifest examples/sysml/ack-manifest.json --output .tmp/ack-synthetic-tests.json` | Synthetic clause-local witnesses, not observed evidence or FLIP parity; events unsupported. |


## Connected example and verification coverage

The [synthetic water-sampling station](../examples/engineering-gallery/water-sampling/README.md) demonstrates the supported paths together without merging their semantics. Its SysML model supplies concept, CONOPS, operational scenarios, components, functions and native controlled clauses; a separately authored finite model supplies its own executable guards, effects and data availability. Fictional responsibilities and stable IDs connect the readings. The [gallery method](gallery-method.md) records official terminology and authority boundaries.

| Promised check class | Connected demonstration / negative control | Actual result boundary |
| --- | --- | --- |
| Statement grammar and declarations | Native short IDs/names, three controlled clauses, typed finite symbols; malformed native extraction and invalid finite declarations are exercised by tests | A valid grammar or declaration is not validated stakeholder intent. |
| Types and units | Receipt-time quantity bound, exact integer ticks and clock/deadline conversions; wrong Boolean/quantity types and mismatched finite fields remain errors | No implicit conversion, physical model or inferred measured duration. |
| Typed traces and responsibility | Requirement-to-concern, use-case-to-requirement and separate finite-to-native mappings; wrong-kind scope and unknown function/performer controls | Only the declared ID/kind correspondence is checked; allocation is documentary, not native topology or implementation proof. |
| Requirement consistency | Finite model's globally quantified input contexts, including focused review; existing conflict and vacuity controls | Single-instant joint satisfiability, not execution conformance or reactive realizability. |
| Scenario execution and progress | Nominal, label-recovery and maintenance finite scenarios; missing data, disabled release and exploration-cap controls | Guards/effects and data availability under finite semantics; completion remains existential. |
| Supplied behavior review | Receipt, elapsed-observation and correlated-event traces; late, incomplete, absent-receipt and over-limit observations | Finite supplied windows, distinct from all possible behavior and real measurements. |
| Scope completeness and provenance | Independent native and finite manifests; deleted/unclassified/duplicate/wrong-kind/null scope controls | Exact supplied inventories and byte/semantic digests, not authenticated approval. |
| Human/documentary views | Scoped README overview, full scrollable function tree and three ordered exchange readings | Selected native identities/edges/order are preserved; the diagrams are not native executable interactions. |
| Reproducible artifacts and delivery | Fresh report/SVG/HTML regeneration, exact inventory, source/result mutation refusal, checked local links and source-bound optional PNG | Deterministic artifact/source correspondence plus separate actual pixel inspection; no graphical-editor roundtrip. |

`tests/test_engineering_gallery.py` runs the actual gallery rebuild when the pinned parser is installed and checks source/output tampering, allocation references and local artifact links. It is registered with both new runtime suites in `scripts/check.py`; `--require-sysml` prevents an absent parser from being reported as a successful required run. Optional browser rasterization uses an explicitly selected existing executable with private profile/temporary data on `/workspace`; it installs nothing and does not affect active browser sessions.

## Finite review scope manifest

The optional independent scope object has exactly these fields:

```json
{
  "version": 1,
  "source_revision": "synthetic-review-1",
  "requirements": ["R1", "R2"],
  "scenarios": ["S1"]
}
```

Supply it through `verify(model, review=True, manifest=scope)` or `scripts/verify.py MODEL --manifest FILE --review`. Version must be integer `1` (not Boolean); source revision must be a nonblank string. Inventories contain valid unique finite-verifier IDs. Both inventories match the complete candidate inventories exactly, including in a focused review. Missing expected IDs, wrong kinds, and new unclassified requirements/scenarios fail the `scope` obligation. Malformed records and duplicates are errors. A deleted or downgraded obligation cannot disappear merely because the candidate removed its trace links.

The manifest adds `scope` to expected/completed obligations for required review. Without a manifest the legacy finite review behavior remains available, with no independent inventory guarantee. This is intentionally different from the native SysML required review, which already requires its own different manifest schema. Neither manifest schema authenticates engineer approval, thresholds, source truth, or accepted meaning.

`dependencies.manifest_sha256` is a canonical semantic JSON digest. The CLI additionally reports `dependencies.manifest_file_sha256`, a hash of the exact file bytes. `review_manifest` carries the supplied source revision and inventories. These identify what was supplied; an agent can still rewrite a local manifest. `analyzed_scenarios` names analyses actually invoked, which may be incomplete when limits apply. An inventory match does not mean unselected scenarios executed. The existing `scope.scenarios`, per-obligation statuses and limits must be read with that list. Focus retains all global requirement consistency, declaration, type, trace and scope checks.

This increment does not detect changes to a requirement's meaning while its ID stays constant; use independently governed baseline comparison where required. No new implicit meaning is assigned to narrative or native model content.

## Correctness repairs and negative controls

1. Unsupported consistency applicability previously skipped scenario execution while reporting `scenarios: pass` and completed. Scenario execution now runs independently whenever model validation permits it. A broken data path remains a scenario failure alongside unsupported requirement applicability.
2. Exploration truncation previously discarded a definite reachable dead end already examined on another branch. The checker now preserves that counterexample and also reports the cap as unknown. Unvisited step reachability or progress is not inferred from a truncated graph. A cap without a definite failure remains unknown.
3. The library now refuses zero, negative, Boolean, non-integer and null assignment/state caps with structured errors and no completed obligations. CLI validation remains in place.
4. A native namespace collision can leave a Pilot-extracted short-ID requirement without a resolved qualified name despite only warning diagnostics. It now returns an identity error rather than raising `KeyError`; no missing name is guessed. Syntax validity, identity extraction and supported computation remain separate.

`tests/test_verifier_completion.py` proves these behaviors through mutated working models, exact-scope deletion/reclassification/addition controls, duplicate/malformed/wrong-kind inventories, focused/global agreement, and file-byte versus semantic digest controls. `tests/test_sysml_contract.py` covers malformed extraction and the real pinned parser namespace-collision case. Existing verifier tests separately cover conflicts, missing data, dead ends, permitted loops, intentional aborts, unsupported predicates, stale evidence, vacuity, and state/assignment caps.

Run both added suites directly, then the existing regression runner:

```text
python3 -B tests/test_verifier_completion.py
python3 -B tests/test_sysml_contract.py
python3 -B scripts/check.py --require-sysml
```

The native suite needs the existing pinned Pilot 2025-09/kernel 0.52.0 archive, SHA-256 `c59342cb8ff5cbf9402a4df7ea3b47108078904802718792699ad854a78a3c32`, installed in this checkout's own ignored cache, with Java/javac 21+. No model, API or solver service is contacted by these tests. Installation is explicit and separate from checking. Both added suites are registered in the central regression runner.

## Deferred plan capabilities

Native constraint expressions, metadata-library semantics, native unit conversion, inherited-attribute computation, automatic V1 migration, CSE-OPS scenario compilation, a general state/mode/event engine, formal FRET translation/parity, realizability, FLIP, hosted Jev evaluation, protected execution and authenticated acceptance remain unimplemented. None is supplied by these fixes or the finite inventory. Linux parser/regression evidence does not establish Windows installed-client or production acceptance.
