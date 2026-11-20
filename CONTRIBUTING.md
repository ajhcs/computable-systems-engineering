# Contributing

Start with a small reproducible engineering defect or a valid case the tool incorrectly rejects. Identify the model revision, requested scope, actual result, expected result, and the semantics supporting that expectation. Synthetic examples are preferred for issue reports.

Run `python3 scripts/check.py`. This exercises the legacy helpers, bounded finite verifier, SysML adapter, synthetic gallery and source-safe reference checks. It does not establish engineering acceptance, original-source authenticity or general SysML behavioral execution. Add meaningful tests for new behavior, including valid exceptions and unsupported cases. A shortened record or a narrower review scope is not evidence of a more efficient method unless the same obligations remain covered.

Give each skill a clear trigger, requested result and observable review criteria. Keep fixed procedures for record contracts and checks that need them. Link specialized methods from the entrypoint and keep the skill's starter prompt and both plugin manifests consistent. Preserve the engineer's authority over consequential decisions. See the [GPT-6.2 Codex prompting guide](https://learn.chatgpt.com/guides/prompting-gpt-6-2-astra).

Before adding upstream code, record its source, revision, and applicable license notices. Public availability of a document does not automatically authorize redistributing all its contents. Reference documents by link and use original, attributed formalizations with explicit assumptions.

Contributions to this project are offered under the [MIT license](LICENSE). Preserve applicable third-party notices and distinguish proposed engineering judgments from tested program behavior. See `docs/release-handoff.md` for publication status.
