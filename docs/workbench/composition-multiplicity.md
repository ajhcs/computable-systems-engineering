# Native multiplicity editing

This operation stays within physical composition. It authors explicit finite
bounds on a selected native part usage. A definition has no usage multiplicity.
The original diagram reader, kit masters and property inspector remain the
presentation path; the edit does not introduce a second engineering model.

## Inspector mapping

The existing [selection/details precedent](composition-walkthrough.md#inspected-precedent)
supports separate properties instead of compound label replacement. The added
low-fidelity control group is:

```text
Selected saved element: current::left         Saved revision: 5
Editing target: current::left                Base revision: 5

Saved multiplicity: [2] — literal
Lower bound [2           ]   Upper bound [2           ]
[Preview multiplicity]

Unsaved change: current::left → [0..1]
Retained configuration: unknown
[Save change] [Discard pending change]

Saved diagram and native properties remain below.
```

The bounds edit never changes a declared name, type, native owner, alias or
retained configuration scope. Default bounds display their native 1/1 values;
inherited or unsupported bounds display their source/status with empty editable
fields. The engineer must explicitly supply both bounds. Empty input is not zero.
Definitions disable this control group. Inspection and a retained edit target
remain distinct through refresh, conflicts and lost-response recovery.

## Source and transaction contract

`set_multiplicity` accepts an engineering UUID and exact integers
`0 <= lower <= upper <= 2147483647`, matching the pinned native literal type.
It inserts or edits local bounds using Xtext name/keyword and expression-token
coordinates. Hidden notes, Unicode, whitespace, CRLF, original file boundaries,
other native facts and persistent identities must survive. Native diagnostics or
an unexpected semantic/reference delta refuse the edit.

Named and unnamed redefining declarations keep their existing native identities.
An explicit edit on an inherited declaration is a local override; the base stays
unchanged. Unbounded or feature-reference bounds may be replaced by the supplied
finite literals. Expressions are not evaluated to guess those values. The pinned
grammar does not admit arbitrary arithmetic bounds. Definitions and unresolved
identities refuse explicitly. The existing registry's inability to import an
anonymous/short-name-only declaration without a native qualified name remains
an open identity/import obligation for the full physical capability.

The source-candidate CLI, typed project operation, visible controls and site
callback invoke the same native edit. Preview never publishes. Save reparses and
validates all retained presentations, then returns the existing durable Git
receipt. Retry uses the exact request UUID and values; stale commands cannot
overwrite a newer revision. Whole-snapshot restore recovers prior bounds without
rewinding the monotonic revision. Configuration findings retain their own scope
and status; a successful edit or commit cannot turn unknown/fail into pass.

The saved diagram displays the resulting literal bounds through the existing
SVG/font path. Each literal annotation stays whole at the saved Mono font size;
default frames widen using its actual advance metrics and padding. A manually
saved frame that cannot fit the whole bound must be enlarged before the change
can be saved. Bounds are never truncated or split across lines. Actual
Codex/ChatGPT, MCP Apps, remote persistence and full physical-capability parity
remain separately required gates.
