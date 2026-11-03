# Selected prose budgets

Run the checker on the actual delivered text during drafting and after the final
edit. A native terminology check does not cover a separate report.

```sh
python3 scripts/prose.py report.txt --kind description --sentence-words 25 --paragraph-words 100 --document-words 1500
```

All budgets are explicit project choices, not engineering acceptance criteria.
For procedural passages, a 20-word sentence budget is a useful starting point;
for descriptions, 25 words is a useful starting point. The `kind` records the
author's classification; it never guesses grammatical roles or changes limits.
Use `--json` for complete findings. Exit codes: 0 pass, 1 selected budget failed,
2 invalid, unreadable or unsupported input. No selected budget means error.

A word is one non-whitespace token. `250 ms` counts as two words; `2.5` and
`SRC-01` each count as one. Sentence boundaries are `.`, `!` or `?` followed by
whitespace/end, optionally after closing quotes/brackets. A decimal point inside
a token does not split a sentence. Abbreviations ending in periods can split
sentences: inspect their findings. Blank lines delimit paragraphs. An unfinished
sentence still counts. Every token counts, including quotations, identifiers,
Markdown syntax and code. Nothing is silently ignored. Supply plain `.txt` text
for a rendered HTML/PDF deliverable; this checker does not extract or attest that
the supplied text matches that deliverable. Markdown is counted literally.
Preserve visible block boundaries in extraction: separate headings and table
rows/cells with blank lines, and preserve spaces between adjacent labels.
Otherwise flattened rows can appear to be one long unfinished sentence. Do not
drop table text or repeat blank lines inside real sentences to obtain a pass.
Headings and cells remain counted in document totals and are checked as their
own passages; the checker does not infer whether a passage is a grammatical sentence.

Results retain selected budgets, text SHA-256, counts and stable Unicode character
spans with 1-based line/column locations. Analysis is bounded to 1000000 characters.
Reports return at most 100 findings, with at most 240 characters of text per
finding. Each returned finding retains its complete original span and count;
`text_truncated` identifies shortened snippets. `total_findings`,
`returned_findings` and `findings_truncated` expose output truncation. Analysis
continues after the output cap; omitted diagnostics cannot turn failure into pass.
The checker reads text; it cannot rewrite it. Preserve actors, `shall`, `should`,
`may`, conditions, negation, values and units when repairing a failure. A count
does not establish meaning, clarity, approved vocabulary or full STE conformance.
Existing native terminology profiles remain separate and unchanged.

The passage distinction and pre-delivery counting adapt ideas from
[SimpleEnglish](https://github.com/AminBlg/SimpleEnglish/blob/main/skills/simple-english/SKILL.md).
The explicit heuristic limits and read-only diagnostic approach also draw on
[karpathy-ladder](https://github.com/FutureAtoms/karpathy-ladder/blob/main/skills/legible-explainer/scripts/ste_lint.py).
No upstream code or modal/word substitutions were copied. These lexical counts
are CSE rules, not ASD-STE100 word-count rules.
