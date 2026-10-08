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

Requests are bounded to 1,000,000 UTF-8 bytes. The persisted ledger has its own
16 MiB limit and retains all admitted records. Before returning a pending ID,
the writer reserves room for an answer of up to 64 KiB of serialized JSON.
Capacity rejection preserves existing state; it does not create a pending
question. Choice labels must fit the answer bound. Resolving a valid pending
answer or cancelling it cannot exceed the ledger's read limit. Cancel/decline
does not read the model, so it also works after the source changes or disappears;
accepting an answer still requires the matching current revision. These byte
bounds do not turn a cancelled or stale question into an accepted answer.

Answers are returned as scoped facts for a subsequent proposal. The helper
never edits models, grants acceptance, expands review scope or changes host
permissions. Provider safety confirmations belong to the provider's approval
channel and are counted separately in benchmarks. The caller must keep known
facts current; code cannot prove that a natural-language question is relevant
or that a same-user ledger came from an authorized engineer. Review those
properties in actual end-user trials. Store ledgers in ignored/private work.
