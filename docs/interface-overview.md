# Compact CSE interface

The repository/plugin exposes a short `cse` skill alongside the three independent
drafting skills. Select `cse` from the host's skill picker (or use `$cse` in text);
exact slash-menu presentation is host-dependent and has not been UI-tested here.
`$develop-system-concept`, `$develop-conops` and `$develop-operational-scenarios`
retain their names. Natural engineering requests still work. The manifest points
to `./skills/`; `.agents/skills` mirrors discovery for repository use. No MCP
server, paid dependency or provider-specific approval tool is registered.

```sh
python3 skills/cse/scripts/cse.py discover
python3 skills/cse/scripts/cse.py describe validate
printf '%s' '{"operation":"validate","arguments":{"models":["draft.sysml"],"mode":"syntax","kind":"concept"}}' | python3 skills/cse/scripts/cse.py invoke
```

`describe` returns only the selected typed schema. `invoke` admits supported
fields and formats before dispatching the existing checker, with no shell string
evaluation. Core semantics are unchanged. Source files are read only. Compact
results identify omitted detail and preserve non-pass status. `--detail` returns
the original complete report. Existing direct commands and standalone v1 helpers
remain compatible. Copy the complete plugin/repository for the shared runtime;
copying a skill folder alone still supports only its legacy helper.

Load only the relevant [inspect/diff](interface/inspect.md),
[validation/test generation](interface/validate.md) or
[domain question](interface/elicitation.md) guide. Detailed engineering methods
remain in each drafting skill's `references/workflow.md`. New recorded modeling
still requires the shared SysML guidance and applicable record contract.

Executable invariants cover strict field/type validation, independent review
inputs, unsupported format admission, status preservation, explicit answers,
revision binding, cancellation, replay and question necessity by declared scope.
They do not infer real intent, authenticate a user, protect the checker from its
owner, prove semantic fidelity or replace host safety approvals.

See [benchmark protocol](../benchmarks/interface/README.md),
[measured payloads](interface-context-results.json) and
[checkpoint](interface-checkpoint.md). Neither deterministic tests nor small
payloads establish that AI can complete engineering work reliably.
