# Computable Systems Engineering

Small, independently invocable skills that help a systems engineer develop a system concept, a concept of operations (CONOPS), or an operational scenario. The engineer directs consequential decisions; the assistant helps investigate, draft, run checks, and revise.

**Status: alpha.** Three skills and their version-1 structural helpers remain available. An opt-in version-2 finite verifier now checks typed declarations, traces, supported requirement consistency, and step scenarios. It does not provide temporal realizability, a protected acceptance service, or a modeling-tool exporter. The source is offered under the [MIT license](LICENSE); publication details are tracked in [the release handoff](docs/release-handoff.md).

| Skill | Useful work unit |
|---|---|
| `develop-system-concept` | Frame a problem, identify functions, explore alternatives, and assess evidence for a concept decision. |
| `develop-conops` | Connect stakeholder needs, boundaries, scenarios, responsibilities, and evaluation plans. |
| `develop-operational-scenarios` | Develop or investigate one scenario or a selected set. |

A complete document is optional. Missing information can remain an explicit unknown. The skills use structured records and selected views rather than requiring the entire model in every model context.

## Try the current helpers

Python 3.10 or newer; the helpers and regression suite use only the standard library. Run from this directory:

```bash
python3 scripts/check.py
python3 skills/develop-conops/scripts/conops.py check examples/workshop/conops.json --review
python3 skills/develop-operational-scenarios/scripts/conops.py view examples/workshop/conops.json S1
python3 skills/develop-system-concept/scripts/concept.py --help
python3 scripts/verify.py examples/verifier/valid.json --review
python3 scripts/verify.py examples/verifier/valid.json --scenario S1 --review --json --detail
```

On systems where Python is named `python`, substitute that executable. See each skill's `references/record.md` for its record and command contract.

The workshop example is synthetic. Passing its checks establishes only the conditions that the helper actually checks. Textual feasibility assessments, source truth, stakeholder acceptance, and implemented-system behavior are not independently verified.

The [synthetic tool-library example](examples/tool-library/README.md) includes a system-concept record, a human view, and a small reproducible calculation. It illustrates explicit unknowns and engineer decisions without creating a full CONOPS.

The [version-2 contract](docs/verifier-v2.md) and [synthetic fixture](examples/verifier/valid.json) specify the finite semantics. Use `--scenario S1 --view` to retrieve a context slice, while running checks against the full model. The [FHWA slice](docs/fhwa-merge-slice.md) is an unaccepted formalization proposal. [FRET reuse](docs/fret-spike.md), [context measurement](docs/context-measurement.md), and the separate [protected-runner boundary](docs/protected-runner.md) record limits and next work.

## Use the skills

The repository includes a Codex plugin manifest at `.codex-plugin/plugin.json` and three skill folders under `skills/`. Plugin packaging is validated; installation through a public marketplace has not been exercised. Each skill is also self-contained: copy the selected folder into your supported personal skills directory and invoke it by name. Avoid installing duplicate copies if the plugin already supplies it.

Example requests:

- “Use develop-system-concept to help compare these two approaches. Keep the current constraints and show unresolved evidence.”
- “Use develop-conops to investigate who operates and maintains this service.”
- “Use develop-operational-scenarios to develop the communications-loss scenario only.”

## Build the next version

Start with [the first-version brief](docs/first-version-brief.md), [the model and verification design](docs/model-and-verification.md), and [the implementation prompt](docs/kickoff-prompt.md). The brief separates agreed objectives from implementation defaults and defines evidence required for completion.

The project uses deterministic program results for computable claims. Broader validation still requires evidence and engineering judgment. JSON is a transport format, not a token-efficiency claim; measure context and repair costs before making such claims.

See [public references](docs/references.md) and [contribution guidance](CONTRIBUTING.md). External publications and tools remain under their own terms; none is bundled here.
