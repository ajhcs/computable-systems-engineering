# Validate and test

Run `cse.py describe validate` for just this operation's schema. Send `invoke`
an object containing `operation` and `arguments`. Syntax mode accepts optional
`kind` (concept, conops or scenario) for draft shape. Compile mode checks the
bounded CSE clauses. Review mode requires an independent manifest and supplied
behavior evidence; neither may be manufactured from the draft as acceptance.
All model bundle members must be supplied. `--detail` retrieves the full report.
The compact result preserves status, scope, findings and coverage; omitted
inventory/diagnostics are explicitly counted. Unknown, unsupported, not-run,
error and exhausted checks are not successful reviews.

Run `describe testgen` only for supported sampled clauses. Report synthetic
pass/fail influence pairs, uncovered variables and limits. Generated tests are
not observations or NASA FLIP coverage. Read `docs/sysml-v2-profile.md` for
explicitly checkable clauses; ordinary prose has no executable semantics.

Existing direct CLI commands remain supported. Read the skill's
`references/sysml.md` for model creation, pinned parser installation and shared
models. Parser absence is an environment finding, not a domain question.
