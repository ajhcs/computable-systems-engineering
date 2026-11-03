---
name: check-engineering-language
description: Check CSE-authored engineering text against project terminology, selected Simplified Technical English rules and supported meaning-preserving repairs. Use throughout drafting or for an explicit language review; preserve source quotations and literals.
---

Use controlled English and the project's defined terms, meanings and approved
forms. Keep English authoritative. Write complete sentences with direct actors.

When terms cross engineering roles or wording implies a goal, constraint,
obligation or stopping condition, read
[concept roles and intent](references/concept-roles-and-intent.md). Reuse the
existing scoped vocabulary and native bindings; keep unresolved intent explicit.

Run `python3 <skill-dir>/scripts/cse.py check MODEL.sysml --profile MODEL.english.json`
after edits. Drafting `check` commands enforce a sibling `.english.json` profile.
Resolve findings and rerun. Keep unknown intent explicit.

Check actual delivered report text during drafting and after the final edit.
Native checks do not cover separate documents. Use the shared script relative to this skill directory:

```sh
python3 <skill-dir>/../../scripts/prose.py REPORT.txt --kind description --sentence-words 25 --paragraph-words 100 --document-words LIMIT
```

Select `LIMIT` for the requested scope. Use `--kind procedure --sentence-words 20`
for instructions. Read
[prose budgets](references/controlled-english.md#delivered-document-prose) for
counting limits. Resolve selected failures and rerun. These are lexical budgets,
not full STE or clarity verdicts.

Read the [controlled-English contract](references/controlled-english.md) when
changing profiles, interpreting coverage or comparing repairs. Retain scoped
concept identities and native bindings. Report IDs, phrase, rule and repair.

Preserve source quotations, original notes, identifiers and literal interface
labels. Keep obligations, modality, negation, conditions, units and scope intact;
consequential changes remain engineer proposals. Never replace `shall`, `should`
or `may` mechanically. Do not invent thresholds to pass. Use program verdicts
only within supported coverage; human review resolves prose meaning and source
intent. Selected checks do not establish complete STE conformance or acceptance.
