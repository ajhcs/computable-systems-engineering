# Computable Systems Engineering

- Read the relevant [skill](README.md#choose-a-skill). For connected work, use [coordination](skills/coordinate-engineering-work/SKILL.md), share one authoritative model, and check each requested view against it.
- Preserve engineer-approved intent, applicability, obligations, units and thresholds. Present changes to meaning as proposals. Read the [verification brief](docs/first-version-brief.md) and relevant record contract before changing checker semantics.
- Use bounded deterministic checks on declarative inputs. A required review passes only when every retained obligation has a passing result. Report draft form, executed evidence and engineering acceptance separately.
- Keep all eleven skills independently invocable. Update the [maintained standalone copies](verifier/standalone.py) together. Run `python3 scripts/check.py` for regressions and add `--require-sysml` for native qualification.
- Follow the [diagram skill](skills/generate-engineering-diagrams/SKILL.md) for diagrams and reference assets. For relevant interface design, use the [interaction walkthrough](docs/interaction-walkthroughs.md) before implementation.
- Keep private sources, annotations, user models and credentials out of Git. Use synthetic or attributed public fixtures.
