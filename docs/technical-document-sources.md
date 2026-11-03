# Technical document adaptation record

Reviewed 2026-11-02. CSE retains the techniques below. The implementation adds
local guidance and a standard-library prose checker; it imports no upstream
code, fonts, diagrams, templates or services.

| Reference inspected | Technique retained | Boundary |
|---|---|---|
| [SimpleEnglish skill](https://github.com/AminBlg/SimpleEnglish/blob/main/skills/simple-english/SKILL.md) and [rule catalog](https://github.com/AminBlg/SimpleEnglish/blob/main/skills/simple-english/references/rule-catalog.md) | Distinguish descriptions from procedures; use complete grammar; inspect the delivered text before handoff. | Retain engineering modality and definitions. Automatic `should`/`must` or `may`/`can` substitutions can change intent. Verification and validation remain separate concepts. |
| [karpathy-ladder STE guidance](https://github.com/FutureAtoms/karpathy-ladder/blob/main/skills/legible-explainer/references/ste-writing.md) and [linter](https://github.com/FutureAtoms/karpathy-ladder/blob/main/skills/legible-explainer/scripts/ste_lint.py) | Measure explicit prose limits with a small program; preserve conditions, negation, values and units. | No percentage STE score, guessed parts of speech or mandatory visual tiers. CSE's lexical counter has its own stated semantics. |
| [NASA-LaTeX-Docs](https://github.com/nasa/nasa-latex-docs/blob/master/README.md) | Separate technical content from reusable typesetting; inspect build diagnostics and the exported document. | No NASA branding or conformance claim. A TeX installation is unnecessary for this change. |
| [drawio-skill](https://github.com/Agents365-ai/drawio-skill) | Retain editable source, explicit graph connections and checks on generated views. | Existing CSE source/model semantics stay authoritative. Draw.io is a presentation format. |
| [text-to-cad](https://github.com/earthtojake/text-to-cad) | Keep a domain-specific authoring source separate from its drawing/export workflow. | CAD geometry and manufacturing checks require an actual CAD task. No CAD service is added to document generation. |
| [kUML](https://github.com/kuml-dev/kUML) | Keep typed model identities behind rendered views. | This review does not qualify its language/rendering claims or select a new CSE backend. |
| [WireViz](https://github.com/wireviz/WireViz) | Generate consistent diagrams and aligned detail tables from structured data. | Harness and pinout symbols apply to harnesses. They do not define process, control or material-flow semantics. |

The inspected SimpleEnglish skill and rule-catalog Git blob identities are
`18968a8a2c631b577327fde0271940335c6a375c` and
`23fd3b823e529b2e2c3f134dd51bf6e2056c88d3`. The inspected karpathy-ladder STE
reference and linter blobs are `a53f0527dfca06f88d17f8d0bf0a5c5c53a8540a`
and `3ef5b2bea949e30e25851e8fab9847c82226d81b`.

## OpenAI package guidance applied

[Build skills](https://developers.openai.com/plugins/build/skills) calls for
focused user goals, concise entrypoints, conditional references and useful
scripts. This change keeps the six existing skills. Detailed document guidance
loads for a document task; the existing language skill routes to the prose
checker. Synthetic tests and a separate document review check observable results.

[Package your plugin](https://developers.openai.com/plugins/build/plugins) and
[plugin guidelines](https://developers.openai.com/plugins/plugin-guidelines)
inform the packaging review. The root manifest and compatibility manifest retain
their identities and local-executor declaration. No MCP server, hook, external
service or runtime dependency is added. User documents and source annotations
remain outside the distributable package. Local source changes do not establish
an installed or published plugin update.
