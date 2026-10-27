# OpenAI plugin and skill audit

> This records the earlier local working-tree audit. The later integration withholds the source-reference pack and requires its own validation; prior receipts do not qualify the integrated tree.

Date: 2026-10-27. Requested reviewer: `gpt-6-astra`, reasoning effort `max`.
Scope: the complete current working-tree plugin, its four skills, supporting
contracts, manifests, local runtime and selected workflow evidence. Existing
uncommitted work was retained. This is a local source/runtime audit, not OpenAI
approval, a published release or a fresh-client installation qualification.

**Final independent verdict:** bounded local source/runtime review passed. Astra
Max closed findings F01–F07 after reviewing the fixes and current evidence. The
release and host gates below remain open; this verdict is not universal OpenAI
compliance or public-release approval.

## Findings and remediation

| Finding | Result |
|---|---|
| Compatibility manifest supplied five starter prompts; current maximum is three. | Reduced to three existing prompts, each below 128 characters. |
| Required Codex composer/listing icons were absent. | Added an original 128-square SVG and included it through both manifest formats. |
| Skills call local Python/Java but did not declare local execution. | Added `requires_local_executor: true` in each format's documented location. |
| Only the supported compatibility manifest existed. | Added recommended root `plugin.json` with Agent Plugins 1.0.0 identity and OpenAI extension; compatibility identity/interface remain aligned. Absence of the portable manifest was not itself a failure of the legacy format. |
| The parser writes its lock/library cache below the installed package. | Added explicit `CSE_SYSML_CACHE` selection across installer, checker, runtime discovery and required-parser gate. Default source-checkout behavior is retained. |
| Private output instructions assumed the plugin's repository and `/workspace`. | Use the selected project's private/ignored work directory outside an installed plugin. This repository's `/workspace` convention remains an example. |
| Diagram instructions used caller-relative paths and mandated a full suite per ordinary diagram. | Resolve the real skill path through symlinks; use absolute runtime scripts and applicable view/source checks. Full suite applies to runtime/reference-library changes. |
| Native Windows SysML execution is unsupported by POSIX locking/classpath code. | Disclosed the qualified Linux/local-executor boundary in skill and setup guidance. No Windows parity claim is made. |
| Some supporting guidance and a diagnostic described only human-task scope 1.1 although 1.2 is also supported. | Aligned the guidance/diagnostic with accepted versions and the 1.2 requirement when ownership is selected; validation semantics are unchanged. |

The review also checked workflow separation, user precedence, engineer authority,
private-source handling, progressive disclosure, reference reachability and
bounded check claims. Names, descriptions and invocation policies remain focused
on the four existing user goals. No MCP server, hook, new engineering language,
external service or additional skill was added.

## Local evidence

- All four Skill Creator frontmatter/scaffold validators passed.
- Root manifest validation passed against validation constraints transcribed
  from the fetched Agent Plugins 1.0.0 JSON schema; OpenAI extension checks also
  covered prompts, matching interfaces, local-execution declarations and included
  square SVG paths. This was not the official client package validator.
- Three new runtime-cache regressions passed: installer/checker/launcher agree
  on the selected cache; an empty selected cache does not silently fall back;
  and the actual pinned parser checks a model from a read-only package while
  writing only to its separate cache.
- `python3 scripts/check.py --require-sysml` passed: 29 suites, 455 tests,
  zero skips. A subsequent diagnostic-only wording correction passed its focused
  existing regression and direct controls for accepted scope versions 1.1/1.2
  and rejected human-task scope 1.0.
- Baseline relocation confirmed a copied launcher's runtime discovery and
  standalone legacy scenario review work from a separate current directory.
  Clean-cache checking correctly returned non-success. A warmed, read-only
  package cache reproduced the permission failure motivating the correction.
- No broken local Markdown targets were found in the skills, their references
  and top-level README/contribution guide before remediation.

The parser-required full regression log and independent review are retained in
the local audit evidence. Private receipts and
baseline snapshots live under ignored `work/astra-plugin-audit-20261027/`.

## Remaining release and host gates

These conditions prevent an unqualified statement that the plugin is fully
qualified for every OpenAI host or ready for public Directory publication:

1. Install an exact reviewed package through a supported local marketplace and
   test its main workflows in a fresh conversation. Direct source invocation and
   metadata interpretation are different evidence. Global installation/config
   was not changed by this audit.
2. Record host-specific results. The shared SysML engine currently requires a
   suitable Linux local executor and Python/Java prerequisites. Native Windows
   SysML is unsupported; other host/runtime combinations remain unqualified.
3. Publish a truthful privacy policy and complete the actual publisher/listing
   requirements before public submission. No placeholder legal/contact URLs or
   claims of publisher verification were inserted. Optional skill UI metadata
   and MCP-specific listing/review fields are not universal requirements here.
4. Review an explicit release file allowlist and source-specific rights. The
   working tree contains local-review/publication-pending examples and an xPPU
   derivative subtree with separately documented GPL terms. Root MIT metadata
   does not relicense those assets. Exclude private work, caches and browser logs;
   preserve source notices and resolve pending publication scope before packaging
   a distributable release. No publication approval was inferred from a test.

## Sources

- [Package your plugin](https://developers.openai.com/plugins/build/plugins):
  portable layout, supported compatibility fallback and OpenAI extension rules.
- [Submission field reference](https://developers.openai.com/plugins/deploy/submission):
  prompt limits, icon requirements and skills-only metadata distinctions.
- [Desktop-only plugins](https://developers.openai.com/plugins/deploy/desktop-only):
  local-executor flag and execution/installation boundaries.
- [Build skills](https://developers.openai.com/plugins/build/skills): focused
  workflows, conditional references, inputs/outputs and behavioral evaluation.
- [Optimize metadata](https://developers.openai.com/plugins/guides/optimize-metadata):
  direct, indirect and negative evaluation cases.
- [Connect and test](https://developers.openai.com/plugins/deploy/connect-chatgpt):
  complete installed-package testing in a new conversation.
- [Plugin guidelines](https://developers.openai.com/plugins/plugin-guidelines):
  privacy, accurate claims, user intent and publication requirements.
- [Agent Plugins manifest schema](https://agent-plugins.org/schemas/1.0.0/plugin.schema.json):
  portable root manifest constraints.
