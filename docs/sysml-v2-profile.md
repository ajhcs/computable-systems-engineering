# SysML v2 model-first profile (alpha)

The `.sysml` file is the authoritative engineering model for new work in the
three skills. The existing version-1 JSON records remain supported for edits to
existing records and explicit legacy workflows; they do not acquire executable
behavior when migrated. The JSON dictionaries inside `verifier/sysml.py` are
temporary compiler inputs, not a second saved model.

## Install and run

The adapter uses the actual [OMG SysML v2 Pilot Implementation](https://github.com/Systems-Modeling/SysML-v2-Pilot-Implementation), release `2025-09`, kernel
`0.52.0`. `python3 scripts/install_sysml_parser.py` downloads a pinned archive,
verifies its SHA-256, extracts the jar and model libraries into ignored `.cache`,
and compiles the small Java bridge for Java 21. It requires Java 21+ and `javac`
21+ (tested locally with Java 26 on Linux; CI explicitly uses Java 21). The
upstream jar and libraries are not committed here.
The adapter checks the compiled bridge against its source hash and requires
rerunning the installer after bridge changes.
See the upstream license files in the extracted cache; the pilot repository
labels its code EPL-2.0. The installer does not run automatically during a
check and does not download or send an engineering model.

```text
python3 scripts/install_sysml_parser.py
python3 scripts/sysml.py examples/sysml/concept.sysml --syntax-only --kind concept
python3 scripts/sysml.py examples/sysml/conops.sysml --syntax-only --kind conops
python3 scripts/sysml.py examples/sysml/scenario.sysml --syntax-only --kind scenario
python3 scripts/sysml.py examples/sysml/ack.sysml --manifest examples/sysml/ack-manifest.json --evidence examples/sysml/ack-evidence.json --review
python3 scripts/sysml_testgen.py examples/sysml/ack.sysml --manifest examples/sysml/ack-manifest.json --output .tmp/ack-synthetic-tests.json
python3 scripts/sysml.py examples/sysml/correlated-events.sysml --manifest examples/sysml/correlated-events-manifest.json --evidence examples/sysml/correlated-events-evidence.json --review
python3 scripts/sysml.py examples/sysml/quantity.sysml --manifest examples/sysml/quantity-manifest.json --evidence examples/sysml/quantity-evidence.json --review
python3 scripts/sysml.py examples/sysml/composed-parts.sysml examples/sysml/composed-requirement.sysml --manifest examples/sysml/composed-manifest.json --evidence examples/sysml/composed-evidence.json --review
python3 scripts/check.py
```

`--syntax-only` uses the pinned parser/validator. `--kind concept|conops|scenario`
adds a minimal draft shape check: a concept has a part definition and concern;
an operational model has a use case and part use. This is not a CONOPS
completeness or content claim. Without
`--syntax-only`, the compiler checks the bounded controlled-requirement profile
below. `--review` requires an independent manifest; evidence is required for a
successful sampled-trace result. `--json` returns details. The default plain
report names its claim scope.

The repository registers the three skills under `.agents/skills/`. Their
`scripts/cse.py` launchers resolve the shared runtime from the real skill
location, preserving user model paths relative to the caller's working
directory. A combined concept/scenario request reuses one model and runs both
relevant draft-shape checks. See [the end-user guide](end-user-test.md).

Multiple `.sysml` files can be supplied together. The adapter sorts the files,
parses their concatenated text as one SysML namespace, and resolves explicit
imports between them. Every user model file needed by an import must be listed.
The report gives a digest for each file and a bundle digest; evidence binds to
the bundle digest. Parser issue and clause locations map back to the original
files. Short IDs on concerns, use cases, and requirements must be unique across
the supplied set.

`scripts/sysml_view.py MODEL.sysml --id R_ACK` retrieves one parsed element,
its owned documentation/constraints, and directly bound part attributes/events.
Pass multiple model files before `--id` for a bundle. The output is a context
view, not a separate editable model. `scripts/sysml_diff.py --before OLD.sysml
--after NEW.sysml` compares parsed records and documentation while ignoring
source line/formatting changes. Repeating either file flag compares bundles.
Its `potentially_affected` list follows direct part/subject/constraint links
conservatively; it does not prove semantic equivalence or identify every
engineering consequence.

## Model conventions

Use standard SysML v2 packages, parts, actions, concerns, requirements, use
cases, and documentation. The parser validates syntax and supported reference
resolution. It does not know whether a stakeholder's need was captured or a
scenario is realistic. A skill keeps a stable short ID on reviewed needs,
requirements, and cases. Use `concern` for stakeholder concerns/needs and
`requirement` for an actual obligation; do not turn every goal or assumption
into a `requirement`. Keep qualitative rationale in ordinary `doc` blocks.

The first executable profile uses project-named SysML documentation, not new
SysML keywords:

```sysml
doc cseClock /*
CSE-CLOCK/2.0
period 1 second
*/

requirement <R_ACK> TimelyAcknowledgment {
    doc cseSource /* CSE-SOURCE/2.0
    SYN-01 */
    subject unit = controller;
    require constraint responseTime {
        doc cse /* CSE-REQ/2.0
        Upon unit.request = true, unit shall within 2 seconds
        satisfy unit.acknowledged = true. */
    }
}
```

The full [synthetic model](../examples/sysml/ack.sysml) is parsed and tested.
The package has exactly one `cseClock`; `period` is a positive exact decimal
in milliseconds, seconds, or minutes. The requirement has a short ID, exactly
one subject bound to a typed part usage, and a `cseSource` ID. The subject part
definition declares Boolean attributes with `in` (input) or `out` (controlled)
direction. A `cse` block lives inside a named **required** constraint. It starts
with `CSE-REQ/2.0`; remaining lines form one controlled sentence. Names such as
`unit.request` are resolved against that requirement's subject and declared
attributes. Trace evidence uses the resolved part path, such as
`AckExample::controller::request`. The checker rejects unknown attributes,
wrong direction for the response, unsupported types, malformed text, and stale
model hashes. Arbitrary code in documentation is never executed.

The [correlated-event example](../examples/sysml/correlated-events.sysml) uses
`CSE-EVENT/2.0` on a required constraint:

```text
Each unit.requestReceived shall within 2 seconds have unit.ackSent with matching correlationId.
```

The bound part definition declares `in event occurrence requestReceived` and
`out event occurrence ackSent`, each with a `String` correlation attribute.
Evidence supplies `events`, exact decimal `time` and `unit` fields,
`observed_until`, and `complete`. Trigger IDs must be unique; a later response
with the same ID at or before the inclusive deadline discharges that trigger.
Overlapping requests remain distinct. Unrelated declared events may be present
in the same trace. No trigger, an unfinished deadline, incomplete capture, or
an event limit produces `unknown` rather than a required pass. Event time is
checked independently of the sampled `cseClock`; a clock declaration remains
required for this alpha profile.

The [bounded-quantity example](../examples/sysml/quantity.sysml) declares an
`ISQBase::DurationValue` attribute with owned `doc cseType`:

```sysml
doc cseType /*
CSE-INT/2.0
range 0 100 scale 1 unit second
*/
```

`ISQBase::LengthValue` is also accepted with a length unit. This annotation
defines a bounded integer-tick observation domain and an exact decimal scale.
The checker validates the SysML quantity family, literal unit, range, and
evidence values, with no implicit conversion. The annotation is a project
convention; the adapter does not yet validate a native SysML unit reference or
evaluate quantity expressions in the model. Evidence integer `2` means two
declared scale ticks.

This is a deliberately small first profile. Native SysML constraint
expressions, assumed constraints, general quantity arithmetic, generated
scenario logic, and inherited attributes
are not yet computed by this adapter. A legal model using one of those remains
valid SysML but is **unsupported for that computation**. A `require constraint`
with ordinary `doc` text is not a checked requirement. Native constraints outside
the CSE required-constraint profile are reported as uncomputed rather than
silently ignored. A subject or referenced attribute with explicit inheritance,
specialization, or a native value also blocks a successful computational review.
Syntax checking and qualitative drafting remain available for those models.
A constraint cannot
have both authoritative CSE text and an independent native expression. The
project's controlled language is FRET-inspired, not a FRETish parser or an
equivalence claim. [FRET semantics](https://github.com/NASA-SW-VnV/fret/blob/master/fret-electron/docs/_media/semantics/semanticsOverview.md) and
[OMG SysML requirement and documentation syntax](https://www.omg.org/spec/SysML/2.0/Language/PDF) are the relevant source material.

## Independent scope and evidence

The manifest is a separate JSON file with `version: 1`, a `source_revision`,
and expected `{id, constraint, source}` entries. The model's `cseSource` must
match. A missing expected clause or a new unclassified required constraint
cannot produce a successful required review. The manifest is a scope binding,
not an authenticated engineer approval. Put raw source documents and private
annotations outside Git; source IDs refer to a separately governed inventory.

Evidence is a separate JSON file with `model_sha256`, `complete`, and either
`observations` or `events` plus `observed_until`. For one model file,
`model_sha256` is its raw-byte SHA-256; for several, it is the reported bundle
digest of their paths and byte hashes. Each sampled observation maps resolved
part-attribute paths to typed values at the declared clock period. Event
records map to declared part-event paths and carry exact decimal timestamps.
A hash detects drift; it does not authenticate who
collected the trace. A passing trace result covers only its finite sampled
window. Missing data, no exercised condition, unfinished obligations, work
limits, parser failures, and unsupported constructs have distinct non-success
outcomes. Reports include source IDs, model digest, bound property paths,
parsed clause, parser diagnostics, analysis claim, and counterexamples when
available.

The parser adapter has a 60-second timeout and serializes its local pilot
library-index access. The language monitor is linear in trace length for its
supported operators, caps observations and work, and bounds pending examples
while retaining their count. The protected acceptance runner described in
[the boundary design](protected-runner.md) is still a separate milestone.

## Synthetic variable-influence tests

`scripts/sysml_testgen.py` can now inspect and export bounded pass/fail trace
pairs for each property referenced by a supported sampled controlled clause.
Each pair differs in one property at one sample and is replayed against the
same deterministic monitor. Its `pass` means witness coverage for those
properties of that **one clause**, not observed system behavior or a required
review. An uncovered property is `unknown`, not proved redundant; correlated
event test generation is explicitly `unsupported`. The exported JSON is marked
synthetic and is not a valid `--evidence` file. This is a local
[variable-influence criterion](variable-influence-tests.md), not FLIP parity.

The [public-source evaluation](public-sysml-evaluation.md) exercises one FHWA
response-timing slice and one NASA low-power CONOPS slice with synthetic traces,
including failures and known gaps. Neither candidate has been accepted as the
source's full meaning.
