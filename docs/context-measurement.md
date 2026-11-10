# Focused context and repair probe

Run `python3 scripts/measure_context.py`. The script duplicates the synthetic valid fixture into a two-scenario model, removes S1's `gap` producer, then compares full-model and S1-focused candidate-plus-diagnostic payloads for the **same S1 repair**. It restores that producer and reruns both reviews. The focused view retains every global declaration, requirement, and trace; verification itself still reads the complete model.

On Linux, 2026-09-29, the `regex-wordpunct-v1` tokenizer counted 1,235 tokens for the whole payload and 1,150 for the focused payload. Both failed before and passed after one scripted repair turn. This tokenizer counts Unicode word runs and individual punctuation characters; it is **not** an LLM tokenizer, so these numbers are a reproducible context-size proxy, not billed model tokens. The scripted edit measures neither human repair time nor model success rate. This one small case supports no universal token-savings claim.

## Compact assembled-context transport

The existing model-view command supports an optional byte-bounded presentation:

```sh
python3 scripts/sysml_view.py examples/meaning-context/handoff.sysml \
  --profile examples/meaning-context/handoff.english.json --element S_HANDOFF \
  --source SYN_HANDOFF=examples/meaning-context/brief.txt \
  --compact --max-bytes 40000
```

`--compact` retains the complete selected assembled report and deduplicates
repeated JSON values into a readable `records` table. An object containing only
`$ref` names an exact table value. `$literal` escapes an authored object with a
reserved marker key. Definitions, namespaces, revisions, native identities,
engineering roles, directed relationships, conditions, quantities, evidence
stages, unresolved mappings, coverage warnings and source pins remain unchanged
after expansion. No natural-language summary or inferred meaning is introduced.

`--max-bytes` enables this format and accepts 1,024 through 8,000,000 bytes. The
limit covers the exact emitted UTF-8 JSON, all transport metadata and its final
newline; `budget.emitted_bytes` records that count. The compact response uses
`assembled-context-compact-1.0`. Existing invocations keep the full
`assembled-context-1.0` format and its historical rendering. A package's
`status` retains the source report's status: successful packaging does not make
an incomplete view or an unperformed semantic review successful.

If the entire selected report does not fit, the command returns a bounded
non-success result with no partial `context` or `records`. It does not cut a
definition, silently remove a dependency, or lower the requested element limit.
Increase the byte allowance or deliberately request a narrower view and inspect
its omissions. A narrow view never changes an independently supplied required
obligation set. Reserve room for that scope and relevant raw evidence before
spending a retrieval allowance on additional context.

Python consumers can call `verifier.context_budget.expand_context(package)` to
recover the original report. Expansion rejects missing/cyclic references,
excessive expansion and a changed source-report digest. This is a transport
integrity check, not authenticated source truth, engineer acceptance or a new
checker input route. Do not rewrite paths or other packaged values without
repackaging the expanded report, because its digest covers those exact values.
The full model and the raw source notes remain available through the existing
retrieval routes. Inspect the expanded coverage and workflow evidence fields
when following those routes.

The byte limit controls this command's delivered source representation. It is
not an LLM token cap or a change to a model's native context window. Repetition,
source shape and reference overhead affect savings; short reports may not get
smaller. Compare the actual bytes sent to the consumer, including any enclosing
packet, and measure generation and review outcomes separately.
