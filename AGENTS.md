# Working on this project

- The repository registers its three skills through `.agents/skills/`. For a user request to use the system-concept, CONOPS, or operational-scenarios skills, read the matching local `skills/develop-*/SKILL.md` instructions. Accept natural skill names; do not require exact identifiers. When multiple skills are requested, apply them to one shared model and run each relevant draft-shape check. Concept plus scenario work does not require a complete CONOPS. Handle model files and commands for the engineer.
- Read `docs/first-version-brief.md` and the relevant skill's record contract before changing semantics. Use `python3 scripts/check.py` for the current regression suite.
- Preserve engineer authority over accepted intent, obligations, applicability, units, thresholds, and selection. Routine implementation and draft repairs proceed within the requested scope. Surface consequential meaning changes as proposals.
- Keep the three skills independently invocable. Their existing version-1 records are structural drafting formats; do not claim they already encode executable scenario logic.
- Use explicit, bounded semantics for computable verdicts. Unsupported, incomplete, timed-out, and errored checks cannot produce an overall successful required review. Do not use an LLM to supply a deterministic verdict.
- Keep runtime dependencies small. Add libraries only for a concrete capability with meaningful tests. Do not implement an unrestricted natural-language parser or execute code supplied inside a model record.
- The CONOPS and scenario helpers are identical copies so each skill can run independently. Update and verify both when changing that shared implementation. Keep record contracts aligned.
- Keep private annotations, course materials, credentials, user models, and raw source documents out of Git. Use synthetic tests and small attributed public-source derivatives. Do not claim third-party endorsement.
- Keep implementation status honest. Hashes identify inputs; they do not authenticate an engineer decision or establish a protected runner. The trusted execution boundary requires independent enforcement and testing.
- The kickoff prompt authorizes the first verifier increment, not an automatic complete engineering design. Preserve unrelated work and check repository state before commits or publication.
