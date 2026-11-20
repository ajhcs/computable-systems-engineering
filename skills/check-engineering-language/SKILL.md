---
name: check-engineering-language
description: Draft or review engineering English using project terminology and selected controlled-English rules. Use for scoped term bindings, native language checks and meaning-preserving prose repairs.
---

Use the project's approved terms and meanings in complete sentences with direct actors. Keep English authoritative. For ambiguous roles, goals, conditions or obligations, use [concept roles and intent](references/concept-roles-and-intent.md) and the existing scoped vocabulary and native bindings. Ask the engineer about consequential ambiguity and preserve unresolved intent.

- For SysML, run `python3 <skill-dir>/scripts/cse.py check MODEL.sysml --profile MODEL.english.json` after edits. Drafting checks also apply a sibling `.english.json` profile when supplied.
- For delivered documents, check the actual extracted text after the final edit, including tables, captions and labels when present. Use `python3 <skill-dir>/../../scripts/prose.py REPORT.txt --kind description --sentence-words 25 --paragraph-words 100 --document-words LIMIT` with the requested document limit. Use `--kind procedure --sentence-words 20` for instructions. See [counting rules](references/controlled-english.md#delivered-document-prose) and report extraction gaps.
- For profile changes and repair evidence, use the [controlled-English contract](references/controlled-english.md). Keep scoped concept IDs and native bindings.

Review actual wording against [defined meaning](../../docs/meaning-context.md). Preserve quotations, notes, identifiers, literal labels, modality, negation, conditions, quantities and units. Repair supported findings and rerun. Offer a proposal if a change would revise an obligation or threshold.

Return revised text or findings with affected IDs, phrases, rules and unresolved decisions. Report checked coverage. Lexical budgets and supported language rules provide bounded findings. Full STE conformity and meaning require separate review.
