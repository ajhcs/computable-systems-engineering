# Contributing

Start with a small reproducible engineering defect or a valid case the tool incorrectly rejects. Identify the model revision, requested scope, actual result, expected result, and the semantics supporting that expectation. Synthetic examples are preferred for issue reports.

Run `python3 scripts/check.py`. This exercises the existing helpers; it does not test the unimplemented formal verifier. Add meaningful tests for new behavior, including valid exceptions and unsupported cases. A shortened record or a narrower review scope is not evidence of a more efficient method unless the same obligations remain covered.

Keep skill instructions short. Put infrequently needed detail in references and execute scripts without loading their source into the drafting model's context. Preserve the engineer's role in elicitation and consequential decisions.

Before adding upstream code, record its source, revision, and applicable license notices. Public availability of a document does not automatically authorize redistributing all its contents. Reference documents by link and use original, attributed formalizations with explicit assumptions.

Contributions to this project are offered under the [MIT license](LICENSE). Preserve applicable third-party notices and distinguish proposed engineering judgments from tested program behavior. See `docs/release-handoff.md` for publication status.
