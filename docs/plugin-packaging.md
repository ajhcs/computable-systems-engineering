# Reproducible local plugin packages

Build an exact reviewed Git commit rather than copying an active checkout or
editing the installed cache. The packager reads committed blobs only; staged,
unstaged, ignored and untracked content cannot enter the package.

```sh
python3 scripts/package_plugin.py --ref <reviewed-commit> --out <new-marketplace-directory>
```

The destination must be new and outside the source checkout. The explicit
selection includes the plugin manifests, eleven skills and their shared runtime,
tests, docs, examples, prototype helpers, licensed assets and tools. Repository discovery aliases,
CI and Git metadata are omitted. `source-receipt.json` retains the source commit,
tree and per-file hashes/modes. Both plugin manifests must agree. A source export
receipt does not establish passing tests, installation, or engineering acceptance.

Run `python3 scripts/check.py --require-sysml` against the reviewed source with
an isolated pinned parser cache. Install through the supported Codex CLI only
within the user's requested scope:

```sh
codex plugin marketplace add <new-marketplace-directory> --json
codex plugin add computable-systems-engineering@cse-local --json
```

When `cse-local` already points elsewhere, preserve that marketplace and the
installed payload before replacing only its source registration through
`codex plugin marketplace remove cse-local --json`, then adding the new source.
Do not replace the user's whole configuration. Keep prior version directories
when existing chats still reference their absolute resource paths.

Verify installed bytes against the package receipt. Start fresh external skill
discovery and a new chat without repository aliases, and use the
[visual-guidance cases](visual-guidance-evaluation.md) to check the workflow.
An already-running chat can retain previously loaded instructions. Native
installation, fresh-session behavior, main-branch merge, release publication and
Directory review are distinct results.
