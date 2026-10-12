# Guidance evaluation and broader recommendations

**Rejected experimental draft, 2026-10-01.** Cole rejected this source type. This material is preserved as historical evidence, not approved professional references, current selection guidance, or publication/rollout material. See [draft status](diagram-reference-draft-status.md). Wait for genuine attributable project bundles before adaptation.

## Historical draft content

A bounded generation pilot on BuilderBob compared the current scenario skill plus its SysML record guidance at baseline b01ef016 with a [concise candidate](concise-guidance-candidate.md), three matched formal examples, and the context PNG. Both received the same synthetic booking-desk brief and JSON output contract. Codex CLI 0.160.0 used existing ChatGPT authentication, fresh ephemeral read-only sessions, and its default model resolver. No model identifier was returned, so this is not evidence about Astra, GPT6.1, GPT6, or Claude5.5 individually.

| Measured result | Current guidance | Concise guidance + matched examples |
|---|---:|---:|
| User prompt bytes | 12,374 | 4,865 |
| User prompt words | 1,689 | 641 |
| Image inputs | 0 | 1 |
| Harness-reported input tokens, including overhead | 22,445 | 17,255 |
| Cached input tokens | 0 | 0 |
| Reported output tokens | 1,367 | 875 |
| Wall seconds | 57.04 | 33.76 |
| SysML parser and scenario shape | error | pass |
| Supported CSE clause compilation | error | pass |
| Fixed rubric | 3 / 7 | 7 / 7 |

[Structured results](../examples/diagram-reference/evaluation/results.json) retain the rubric and parser diagnostics. Both runs preserved the two native item-flow directions and selected action order, and honestly said validation was unrun. The current condition omitted the Boolean import, used invalid action-succession syntax, and failed to encode the required CSE short ID and required-constraint profile. It also placed control successions in the boundary item-flow list; this costs one point under the declared view-separation criterion, although its prose identified them as control order. The matched condition encoded the supported obligation correctly. Generation was scored before any repair, so these are first-output results.

The combined candidate used 5,190 fewer reported input tokens (23.1%) and 492 fewer output tokens (36.0%). User prompt bytes fell 60.7%. These measurements include the harness context and, for the candidate, the image; they are not tokenizer counts for the skill text alone or monetary costs. One pair on one brief does not isolate the contributions of shorter guidance, examples, or the image, estimate reliability, or establish general speed gains. No commands were executed by either evaluated model. An inherited MCP startup emitted an authentication diagnostic; no connector call was used and no new grant was made. Private notes were excluded from the prompts.

The current comparison material reflects explicit guidance text, without reading the current skill's linked synthetic template. Thus this does not benchmark the full normal tool-assisted workflow, which may retrieve that template and repair with the parser. Repeated cross-task trials should compare equal retrieval budgets and include a concise-only arm before changing the default instructions.

## Recommended next changes, separate from this patch

1. **Keep behavioral freedom; move repeated contracts out of the main prompt.** Trial the concise candidate across concept, CONOPS, exception scenario, unknown evidence, and combined requests. Retain on-demand parser/tool contracts, engineer authority, source privacy, and honest verdict boundaries. Do not replace the three main skills based on this one pair.
2. **Improve retrieval instead of adding rules.** Retrieve one matched example for the current failure mode. The current guide adds only a small on-demand nudge; it does not prescribe a new exhaustive drafting sequence.
3. **Make diagram drift visible.** Extend bounded typed projections when a real modeling need warrants them. The new fixture checks catch endpoint, order, threshold, and stale-view changes. They are not a general semantic-equivalence checker or a lossless draw.io importer.
4. **Separate verification and validation evidence.** Keep mechanical verdicts separate from stakeholder need coverage, uncertainty, and acceptance. The current adapter already distinguishes bounded computation and unsupported content; native scenario execution and protected acceptance remain unimplemented.
5. **Qualify installation on the actual consuming harness.** Symlinks and the repository launcher work in this checkout. Marketplace installation and copying only skill folders remain unqualified; do not label those paths complete.
6. **Use repo case studies after evidence inventory.** The runtime example provides the pattern: code anchors, native model, selected dependency view, hashes, and explicit omissions. For open-informatics.org, inspect each project's actual boundaries before drafting detailed case studies. Links to Access Red Team and colelyons.com should explain real context and responsibility, not add inferred dependencies. No site content or deployment was changed here.

Reproduction artifacts and raw sessions are under ignored .tmp/diagram-evaluation. The candidate remains a proposal. The reference additions and concise selection nudge are the implemented scope.

## Post-pilot reference refinements

The context/action images now explicitly say custom view, and the runtime image qualifies the launcher under skills/develop-*/scripts/cse.py. PNG --check compares a fresh rendering with saved bytes without rewriting the baseline. Four parser checks and nine affected reference tests passed; a deliberate stale PNG copy was rejected without changing either the copy or baseline. This is separate from the original 182-test full-suite receipt. Exact measured prompts, the original context image input and token receipts are preserved. The optional rerun script strips the candidate heading absent from the measured prompt. No new model trial was run. A bounded search found no installed offline draw.io editor or mxGraph runtime on BuilderBob, so native open/render/save/reopen remains unrun; no editor-produced difference is claimed.
