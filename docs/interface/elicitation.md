# Domain elicitation

Use an existing source bundle and known facts. When a missing interpretation,
threshold, unit, priority or selection affects the current edit, decomposition,
migration proposal or comparison, prepare one concrete question with its reason.
Run `cse.py elicit-help` for the small request contract and pipe requests to
`cse.py elicit --state work/draft.cse-questions.json`.

The ledger derives a revision from source bytes, operation and supplied facts.
It refuses invalid answer types/choices, stale revisions, replayed answers and
multiple pending questions. Cancel/decline supplies no answer or default.
Read-only inspection, validation and explanation need no domain question;
unrelated or already answered needs are suppressed. Correct invalid inputs
using the error's recovery action rather than asking about routine mechanics.

Answers are returned as scoped facts for a subsequent proposal. The helper
never edits models, grants acceptance, expands review scope or changes host
permissions. Provider safety confirmations belong to the provider's approval
channel and are counted separately in benchmarks. The caller must keep known
facts current; code cannot prove that a natural-language question is relevant
or that a same-user ledger came from an authorized engineer. Review those
properties in actual end-user trials. Store ledgers in ignored/private work.
