# Visual guidance evaluation

The [case inventory](../examples/visual-guidance-evaluation/cases.json) maintains
direct and indirect engineering-document requests, a client override, a missing
required font, editorial artwork with an unchanged body, and a text-only negative.
All source wording and the small procedural PNG are synthetic. The trials use
selected runtime resources; they do not require private client work or a source
checkout in the fresh project.

## Prepare and run a behavioral trial

Resolve the installed plugin directory as `<runtime>`. Prepare a new private
project on a writable volume:

```sh
python3 <runtime>/scripts/evaluate_visual_guidance.py list
python3 <runtime>/scripts/evaluate_visual_guidance.py prepare \
  --case indirect-profile --output /private/new-project --runtime <runtime>
```

Give `prompt.txt` to a new Codex session in that directory with its normal skill
catalog and existing permissions. Keep the observable command/event JSONL outside
the project. Record the invocation, installed package identity and session origin
separately. A fresh session has no inherited conversation or project-local skill
aliases. This helper does not start a model, modify permissions or install tools.

The render cases request `output/document.html`, `output/document.pdf` and
`output/figure-1.svg`. Use the selected profile with the
[shared renderer](document-rendering.md), keep its receipt in
`output/render-receipt.json`. Keep selected illustrations in their intended
document roles; a separate documentary flow need not contain an illustration.
Each identified selected SVG occurrence in the delivered HTML or standalone SVG
must retain the selected master's native primitives. After the session completes:

```sh
python3 <runtime>/scripts/evaluate_visual_guidance.py check \
  --case indirect-profile --project /private/new-project \
  --runtime <runtime> --trace /private/observable-session.jsonl
```

Use `--render-receipt` when the renderer receipt is kept at a different
project-relative path. If the default interpreter lacks PyMuPDF, use `--python`
with the same existing interpreter selected for rendering. Its path is recorded
under `tooling.python` in the render receipt; the evaluator does not automatically
execute an interpreter named by artifact data. Missing PDF tooling cannot pass.
Existing project directories are refused by `prepare`.
Supplied inputs are hashed before the trial and checked afterward.

## What the verdict covers

The evaluator checks successful observable commands that consumed an applicable
installed skill and invoked the shared renderer. It ignores reasoning and final
assistant claims. It checks output existence, current output hashes, actual
glyph font names in renderer evidence, selected graphic identities and roles,
retained native SVG geometry, and the accepted body's normalized text. Color,
occurrence IDs, containing transforms and added labels may change; deleting or
changing a selected native shape fails the geometry comparison. Geometry is
checked separately for every `svg[data-cse-source="comp-process"]` occurrence
across delivered HTML and SVG. A complete unrelated SVG, or pieces of the master
split across several incomplete occurrences, cannot satisfy that check. The
identified occurrence count must match the renderer's inspected inventory;
source hashes and visibility/bounds checks remain required.

The current HTML, PDF and SVG must all match the renderer's output hashes. The
PDF receipt must match the current file, contain completed checks and match the
selected embedded font names and weights. The evaluator also reruns the PDF
inspector against the delivered PDF; a previously passing receipt is insufficient.
The preserved body's normalized wording must occur in that PDF's extracted text
in order. Retaining hidden HTML while omitting the body from the delivered PDF
does not pass preservation.

The missing-font case independently checks that the selected required resource
is actually absent and that no final PDF was delivered anywhere in the project.
It also requires a typed failed profile preflight, recorded in
`output/profile-preflight.json` (or the project-relative `--failure-receipt`) or
captured JSON from a failed helper command. The recorded profile object, original
profile hash/path, resource records and missing-font findings must match the
selected profile and an independent current preflight replay. Generic help,
argument or environment errors do not establish a missing selected resource.
This is a recorded and rechecked local result, not authenticated process origin.
The text-only case checks
that no visual skill or renderer was invoked and no graphical artifact was
created; it does not judge the arithmetic answer.

Missing, unsupported, malformed or incomplete evidence cannot become a passing
render review. Unit tests exercise checker behavior with synthetic defect
evidence. They never invoke a model and do not establish that skill selection
works in a live session. A real run needs both the recorded invocation and the
actual artifact checks. The receipt is a same-user local record; it does not
authenticate a protected runner, prove engineering semantics or record client
acceptance. Human inspection of completed pages and diagrams remains separate.
