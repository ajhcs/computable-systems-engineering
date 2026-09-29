# Computable Systems Engineering

Small, independently invocable skills that help a systems engineer develop a system concept, a concept of operations (CONOPS), or an operational scenario. The engineer directs consequential decisions; the assistant helps investigate, draft, run checks, and revise.

**Status: alpha.** The three skills now default to authoring SysML v2 textual models for new recorded work. A pinned upstream pilot parser validates those models. A bounded controlled-text profile checks selected sampled Boolean/quantity requirements and correlated event deadlines against supplied evidence. A separate bounded generator now exports synthetic pass/fail trace pairs that demonstrate a referenced property's effect on one sampled requirement when it can find such a pair. Existing version-1 JSON helpers and the opt-in finite verifier remain available. General SysML behavior computation, temporal realizability, formal FLIP coverage, hosted Jev integration, and protected acceptance are not implemented. The project source is offered under the [MIT license](LICENSE); the separately downloaded pilot parser has its own license. Publication details are tracked in [the release handoff](docs/release-handoff.md).

| Skill | Useful work unit |
|---|---|
| `develop-system-concept` | Frame a problem, identify functions, explore alternatives, and assess evidence for a concept decision. |
| `develop-conops` | Connect stakeholder needs, boundaries, scenarios, responsibilities, and evaluation plans. |
| `develop-operational-scenarios` | Develop or investigate one scenario or a selected set. |

A complete document is optional. Missing information can remain an explicit unknown. The skills use a system-wide SysML model and selected views rather than requiring the entire model in every model context. The [SysML-first profile](docs/sysml-v2-profile.md) defines the supported parser and checker boundary.

## Try the current helpers

Python 3.10 or newer; the version-1 helpers use only the standard library. SysML validation additionally requires Java 21+, `javac` 21+, and the pinned pilot parser installed into the ignored project cache. Run from this directory:

```bash
python3 scripts/check.py
python3 scripts/install_sysml_parser.py
python3 scripts/check.py --require-sysml
python3 scripts/sysml.py examples/sysml/concept.sysml --syntax-only
python3 scripts/sysml.py examples/sysml/conops.sysml --syntax-only
python3 scripts/sysml.py examples/sysml/scenario.sysml --syntax-only
python3 scripts/sysml.py examples/sysml/ack.sysml --manifest examples/sysml/ack-manifest.json --evidence examples/sysml/ack-evidence.json --review
python3 scripts/sysml_testgen.py examples/sysml/ack.sysml --manifest examples/sysml/ack-manifest.json --output .tmp/ack-synthetic-tests.json
python3 scripts/sysml.py examples/sysml/correlated-events.sysml --manifest examples/sysml/correlated-events-manifest.json --evidence examples/sysml/correlated-events-evidence.json --review
python3 scripts/sysml.py examples/sysml/quantity.sysml --manifest examples/sysml/quantity-manifest.json --evidence examples/sysml/quantity-evidence.json --review
python3 scripts/sysml.py examples/sysml/composed-parts.sysml examples/sysml/composed-requirement.sysml --manifest examples/sysml/composed-manifest.json --evidence examples/sysml/composed-evidence.json --review
python3 scripts/sysml_view.py examples/sysml/ack.sysml --id R_ACK
python3 scripts/sysml_diff.py --before examples/sysml/ack.sysml --after examples/sysml/quantity.sysml
python3 skills/develop-conops/scripts/conops.py check examples/workshop/conops.json --review
python3 skills/develop-operational-scenarios/scripts/conops.py view examples/workshop/conops.json S1
python3 skills/develop-system-concept/scripts/concept.py --help
python3 scripts/verify.py examples/verifier/valid.json --review
python3 scripts/verify.py examples/verifier/valid.json --scenario S1 --review --json --detail
```

On systems where Python is named `python`, substitute that executable. Each skill's `references/sysml.md` describes new model output; `references/record.md` preserves its legacy JSON contract. The SysML integration tests run when the pinned parser is installed; otherwise they report a skip. The `--require-sysml` check and CI fail if the pinned parser is missing or stale.

The workshop example is synthetic. Passing its checks establishes only the conditions that the helper actually checks. Textual feasibility assessments, source truth, stakeholder acceptance, and implemented-system behavior are not independently verified.

The [synthetic tool-library example](examples/tool-library/README.md) includes a system-concept record, a human view, and a small reproducible calculation. It illustrates explicit unknowns and engineer decisions without creating a full CONOPS.

The [version-2 contract](docs/verifier-v2.md) and [synthetic fixture](examples/verifier/valid.json) specify the finite semantics. Use `--scenario S1 --view` to retrieve a context slice, while running checks against the full model. The [FHWA slice](docs/fhwa-merge-slice.md) is an unaccepted formalization proposal. [FRET reuse](docs/fret-spike.md), [context measurement](docs/context-measurement.md), and the separate [protected-runner boundary](docs/protected-runner.md) record limits and next work.

## Use the skills

The repository registers its three skills through symlinks under `.agents/skills/`, which Codex discovers when you open this project. They remain independently invocable and are scoped to this repository. Start a new project conversation if the skill selector has not refreshed. [Codex skill discovery](https://learn.chatgpt.com/docs/build-skills) documents repository scope and symlink support.

Each skill's `scripts/cse.py` launcher finds the shared parser/engine from its real location, so checks work from subdirectories as well as the repository root. The repository also includes a plugin manifest at `.codex-plugin/plugin.json`; installation through a public marketplace remains untested. Copying a skill folder alone preserves its version-1 helper, but does not install the shared SysML engine. Avoid duplicate installations.

Example requests:

- “Use the system-concept and CONOPS skills on the material below. Keep my raw materials out of Git.” In this repository, the assistant uses both skills on one model, runs both draft-shape checks, and inspects supported sampled requirements with synthetic test pairs. It reads raw source in place and keeps the source and user-specific model in ignored private workspace paths; the engineer supplies material and reviews consequential interpretations, not commands or SysML syntax.
- “Use develop-system-concept to help compare these two approaches. Keep the current constraints and show unresolved evidence.”
- “Use develop-conops to investigate who operates and maintains this service.”
- “Use develop-operational-scenarios to develop the communications-loss scenario only.”

For your first combined concept/scenario trial, use “Use the system-concept and operational-scenarios skills on the material below. Keep my raw materials out of Git.” The assistant creates one shared model, returns readable concept and scenario views, runs both relevant draft checks, and reports supported computations separately from unresolved content. User-specific work stays in ignored `work/`. No command or SysML knowledge is required from the engineer. See the [end-user test guide](docs/end-user-test.md), [pre-test review](docs/pre-test-review.md), and [synthetic shared example](examples/sysml/joint-concept-scenario.sysml).

## Build the next version

Start with [the first-version brief](docs/first-version-brief.md), [the model and verification design](docs/model-and-verification.md), and [the implementation prompt](docs/kickoff-prompt.md). The brief separates agreed objectives from implementation defaults and defines evidence required for completion.

The [SysML-first plan](docs/sysml-v2-model-first-plan.md) and [implemented alpha profile](docs/sysml-v2-profile.md) describe the current migration and its limits. The [public-source evaluation](docs/public-sysml-evaluation.md) shows FHWA and NASA candidate slices with synthetic traces. The [controlled language profile](docs/requirements-language-v1.md) parses a narrow FRET-inspired subset and checks supplied sampled behavior using explicit clock and unit semantics. [Variable-influence tests](docs/variable-influence-tests.md) are a bounded precursor to formal FLIP generation. The parsed context view and structural diff support review, but general state/mode computation, FRET-backed test generation, and richer generated views remain future work.

The project uses deterministic program results for computable claims. Broader validation still requires evidence and engineering judgment. JSON is a transport format, not a token-efficiency claim; measure context and repair costs before making such claims.

See [public references](docs/references.md) and [contribution guidance](CONTRIBUTING.md). External publications and tools remain under their own terms; none is bundled here.
