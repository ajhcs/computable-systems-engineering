# Controlled-English contract

## Delivered document prose

Check separate reports on their actual delivered text, not only native model
documents. In a CSE checkout, `scripts/prose.py` checks explicitly selected
sentence, paragraph and document word budgets; see
[counting contract](../../../docs/prose-checks.md). Its dependency-free Python
module is `verifier/prose.py`. The standalone language skill retains its existing
native terminology checker; it does not bundle this repository-level prose CLI.
Record selected budgets and rerun after the final edit. Every token counts,
including source quotations and identifiers. No text is rewritten or silently
excluded. Keep obligations and modality: never mechanically substitute `shall`,
`should`, `may` or `can`, and keep verification and validation concepts distinct.

The lexical budgets are CSE project rules, not implemented ASD word-count rules,
approved-vocabulary checks or a percentage of STE conformance. Review prose
meaning and the selected standard separately.

Use English as the authoritative authored engineering text for this CSE profile.
Choose familiar, consistent words that engineers who use English as an additional
language can understand. This is an English authoring workflow, not a translation
or multilingual-model workflow. Keep original quotations, notes, identifiers and
literal interface labels verbatim and explain them separately when useful.

## Source basis and rule coverage

The English basis is **ASD-STE100, Issue 9, 2025-01-15**, identified by the
[official site](https://www.asd-ste100.org/),
[current FAQ](https://www.asd-ste100.org/STE_faq.html) and
[Issue 9 specification](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf).
The FAQ explains the international readership, approved meanings and grammatical
roles. [Boeing's official description of its STE checker](https://www.boeing.com/company/licensing)
describes a syntactic parser and grammar checker. CSE implements the smaller,
explicit coverage below; no enterprise-wide language mandate is inferred.

| Selected rule | Implemented check |
|---|---|
| ASD-STE100 1.11: consistent technical noun for an item | A selected authored noun use must match a declared form of the same scoped concept's canonical technical noun. A different noun fails with the exact phrase and model IDs. The scope selects the uses; arbitrary prose is not parsed to discover every noun. |
| CSE-TERM-POS | Each selected use declares a noun or verb slot. Its concept has the same approved grammatical class. This checks explicit roles, not inferred parts of speech in unrestricted prose. Engineering `kind` and grammatical class remain distinct. |
| CSE identity and revisions | Check concept ID, namespace/revision, definition, approved forms, native category/binding, source bytes and selected text. Ambiguous same-scope labels and stale pins fail, including edits without a revision-string increment. Identical words in different namespaces remain separate. |
| CSE-PHRASES | Required project phrase rules fail; contextual advice stays visible. Check selected authored native text plus selected term labels/definitions. Source/literal spans remain unchanged and are reported separately. |
| CSE-LANGUAGE-REPAIR | Compare supported `language-1.0` clause meanings before and after a proposed edit. Changes to actor, scope, condition, negation, comparison, timing or unit meaning fail. Leaving mandatory `shall` grammar fails. No edit is applied. |

Rule 1.2 needs approved dictionary/part-of-speech evidence. This implementation
does not import that dictionary or infer unrestricted grammatical roles.
Selecting 1.2 or another unimplemented rule returns `unsupported`, not pass.
Project noun/verb approval is explicit project evidence, not a claim that every
word occurs in the STE dictionary. Author against applicable STE provisions and
review uncertain dictionary meanings/forms from the selected edition. Do not
report complete STE conformance from these selected checks.

## Existing vocabulary, explicit English selection

The existing `foundation-1.0` catalog remains the single concept vocabulary.
Terms retain `namespace`, `revision`, `label`, `definition` and engineering
`kind`. Optional `part_of_speech` is `noun` or `verb` (legacy default: `noun`).
Optional `approved_forms` is a list of explicit inflections/capitalizations of
that technical term, includes `label`, and has at most 32 unique entries (legacy
default: `[label]`). Do not add synonyms as inflections to bypass consistency.
Meanings, grammatical roles and forms are engineer-directed project choices.

`verifier.foundation.term_digest(term)` hashes those fields and effective
defaults. It identifies content; it does not approve a change. An icon can bind
to this same concept ID/namespace/revision/digest while keeping asset identity
separate. Neither a shared icon nor matching labels establishes synonymy.

A sibling `MODEL.english.json` is a foundation profile with the optional `english`
selection below. The three drafting launchers discover it automatically during
normal `check`, including `--syntax-only`; failures affect the exit status during
drafting, without waiting for `--review`. An absent profile means no language
conformance check was selected, not a language pass. For new authored work, the
assistant prepares/reuses the project selection and runs it; the engineer need
not manage the files or repeat a CLI opt-in on each edit.

The `english` selection contains:

- `version: english-1.0`, `revision`, and selected `rules`. The strict profile
  includes `ASD-STE100-1.11` and `CSE-TERM-POS`; select `CSE-PHRASES` when phrases
  are declared. Unknown rules cannot produce a successful selected check.
- `terms`: stable catalog IDs mapped to their retained `term_digest` values.
  Changing a definition, class or approved form invalidates the selected pin.
- `views`: stable IDs mapped to native `element`, named `document`, `text_sha256`,
  `uses` and `preserved` lists. The checker reads the actual parser document body
  with outer whitespace stripped. A use has `{term, slot, start, end}`; optional
  `element` refers to a different native element from the document owner. One
  sentence can describe several concepts without duplicating their definitions.
- `phrases`: rule IDs with literal `phrase`, proposed `repair` and
  `severity: required|advice`. Matching ignores case and respects word boundaries.
  These are declared project rules, not an unreviewed extension to STE.

Positions are half-open Unicode character indices, not UTF-8 byte offsets. Term
uses cannot overlap or match only a word prefix. Each selected term needs an
authored native use; a source quotation does not satisfy that coverage.

A `preserved` span has `{start, end, text, kind, basis}`. Kind is `quotation`,
`original_note`, `identifier` or `interface_literal`. The exact source/literal
text is checked and retained. Such a span can explain a project phrase occurrence
without rewriting history. It cannot waive identity, revisions, approved term
uses or a semantic-repair comparison. A stale source span fails. A selected term
use overlapping source text stays unresolved until an authored English
explanation is supplied separately.

The fixture's project phrase rules flag `as appropriate` and `etc.` in authored
text, and give contextual advice for `is suitable`. They request explicit meaning
or an unresolved question; they do not invent conditions, thresholds or obligations.
Tailor project rules deliberately. Do not turn a need, goal or observation into
a mandatory requirement to obtain a wording pass.

## Run and repair

### Prepare a separate profile candidate

After editing selected native prose, reuse the existing vocabulary and selection:

```sh
python3 skills/check-engineering-language/scripts/cse.py prepare EDITED.sysml --profile BEFORE.english.json --before-model BEFORE.sysml --revision draft-2 --output CANDIDATE.english.json
python3 skills/check-engineering-language/scripts/cse.py check EDITED.sysml --profile CANDIDATE.english.json
```

The same preparation route is `cse.py terminology prepare` through each drafting
launcher. A changed source requires its actual before-model matching the old
profile's source pin. If source bytes are unchanged, omit `--before-model`.
The explicit `--revision` names a proposed draft revision; term revisions and
selected term pins are retained. Previous identities, text hashes and authored
uses must be valid before refresh; an invalid old noun use cannot be rebound to
a different occurrence to hide it. Authored phrase failures remain visible.

The helper parses actual named native documents and proposes model/text hashes
and exact approved-form character spans. It neither edits model prose nor infers
concepts, grammatical roles, synonyms or source meaning. Preserved quotation,
note and literal text must still occur exactly once; it remains unchanged and
is excluded from authored term matching. An unchanged selected document retains
its previously validated spans even when other native source bytes changed.
Missing or ambiguous occurrences in edited text,
overlapping concepts and exceeded matching limits remain unresolved, with no
candidate written. Repeated uses of one binding require exactly that declared
number of matches; different element bindings are never guessed from a label.

Output is a new file, never an overwritten live profile. The compact report
shows binding changes and an authored-text diff. `operation: candidate_generated`
is separate from `language_status`: a mechanically generated candidate can
still fail a required phrase rule. A non-success exits nonzero. Review the text,
scope and bindings before adopting the candidate; prose meaning equivalence and
acceptance remain unevaluated. Its proposed scope digest is not a retained review
fingerprint: preparation never advances that fingerprint or runs a required
review. A later check against the original retained digest must still refuse a
changed scope.

For initial preparation, use a `foundation-1.0` vocabulary without `english` and
add `--selection SELECTION.json`. This explicit offset-free selection names
existing terms, native documents and noun/verb slots; no catalog is inferred:

```json
{"version":"english-selection-1.0","revision":"draft-1",
 "rules":["ASD-STE100-1.11","CSE-TERM-POS"],"terms":["T_PUMP"],
 "views":{"V_PUMP":{"element":"R_PUMP","document":"description",
   "uses":[{"term":"T_PUMP","slot":"noun"}],"preserved":[]}},"phrases":{}}
```

A preserved entry supplies `{text, kind, basis}` without offsets. Existing
English selections cannot be replaced with `--selection`; propose consequential
scope changes separately. The helper uses the existing checker and standard
library, with one native source file, 4,096-character documents and a declared
exact-matching work cap.

```sh
python3 skills/check-engineering-language/scripts/cse.py check examples/terminology/shared-pump.sysml --profile examples/terminology/shared-pump.english.json
python3 skills/develop-system-concept/scripts/cse.py check examples/terminology/shared-pump.sysml --syntax-only
```

The first command is independently invocable. The second demonstrates automatic
enforcement in ordinary drafting. All three drafting skills expose the same
`terminology` command. Use the program findings, repair the affected draft within
the accepted meaning, and rerun. An incomplete draft can continue; unresolved
selected failures/unknowns cannot be called conforming.

For a separately retained required terminology review, run `fingerprint PROFILE`
to identify its `english` scope, then supply `check ... --review --scope-sha256
DIGEST`. Required review without that digest is unknown. Deleting a term, use or
rule changes the scope and cannot silently repair the retained review. Scope
changes remain proposals for the engineer. Hashes do not authenticate assent or
provide a protected runner.

Save a proposed controlled-requirement replacement separately, then run:

```sh
python3 skills/check-engineering-language/scripts/cse.py repair examples/language/valid.json --id R_ack --replacement-file work/proposed-clause.txt
```

The existing parser compares exact supported meanings. For example, `2 seconds`
and `2000 milliseconds` are equivalent, but weakening `shall`, deleting a
negation or changing a deadline fails. Unsupported/free prose has no deterministic
equivalence verdict. Preserve source intent, modality, units, conditions and
scope; present intended changes for engineer judgment instead of applying them
as routine wording repairs.

Default output gives at most twelve findings, required failures first, with
stable IDs, exact phrase, rule, explanation and repair. Use `--json` for the
compact complete report. Phrase analysis has a declared work cap; an exceeded
cap is unknown and cannot pass. No whole-model or dictionary dump is needed.
The current automatic profile supports one native source file. A selected profile
over a multi-file check remains unsupported rather than silently skipped.
