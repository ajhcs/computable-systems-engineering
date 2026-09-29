# Readiness review before using the language on a private system

**Current disposition, 2026-09-29:** the review findings below are a historical
record of the earlier language candidate. The running alpha now has a linear
sampled monitor, work/evidence limits, bounded diagnostics, independent SysML
scope manifests, explicit compilation/trace claims, dependency-aware missing
data, parser boundary fixes, and committed short-trace oracle tests. See
[the current profile](sysml-v2-profile.md) and
[the end-user test guide](end-user-test.md) for what is available. These repairs
support a draft trial; they do not supply source-intent acceptance or general
SysML behavior computation.

**Review date:** 2026-09-29. An independent Astra Max agent read the profile,
implementation, public-case evaluation, and source references without editing
code. It reproduced the 131-test regression suite and compared 12,288 fully
observed short traces with a separate set/interval evaluator. No wrong temporal
verdict appeared in that bounded comparison. The comparison harness was an
exploratory probe, not part of the committed regression suite. All public-case
observations remain synthetic and their candidate interpretations unaccepted.

The current checker is usable as a **draft, sampled-trace exploration tool**.
The following adjustments are prerequisites for relying on its *review* output
when examining an actual system concept, CONOPS, or scenario.

1. **Bound the analysis and evidence report.** In
   [`_evaluate`](../verifier/language.py), every `until` trigger can scan the
   remaining trace. Missing held values create one pending entry per trigger
   per observation. An alternating-trigger, no-release, missing-response case
   with 500 observations produces **63,000** pending entries; this was
   independently reproduced. At the currently permitted 10,000 observations,
   that pattern implies **25,010,000** entries for one requirement. Add an
   explicit work budget, bounded diagnostics with counts and representative
   locations, and a visible `unknown` or incomplete result when analysis work
   is exhausted. Diagnostic truncation must preserve any known failure.
   Prefer a linear or amortized monitor, but retain a budget even then.
2. **Bind expected obligations outside the candidate file.**
   [`check_document`](../verifier/language.py) treats the candidate's own
   `requirements` map as the entire review scope. Deleting a failing clause can
   therefore produce `pass` for a reduced file. Introduce a small separate
   review manifest with expected source obligations, selected candidate clause
   IDs and revisions, and explicit unresolved/unsupported parts. Compare the
   file against that manifest. This prevents accidental omission; it does not
   constitute a protected or authenticated acceptance boundary.
3. **Separate compilation from trace satisfaction in every output.** The
   [CLI](../scripts/requirements.py) currently prints the same bare `pass` for
   syntax-only compilation and a successful trace review. Always show check
   mode and claim scope. In compilation mode, say that grammar and types passed
   and no behavior was evaluated. In review mode, show the observation window,
   completeness, exercised conditions, counterexample/pending indices, and
   concise reasons. Keep JSON and plain-text meanings aligned.

The following corrections should be made before freezing profile 1 and are
worth including in the same preparatory change:

4. **Decide missing-data semantics by dependency.** A missing trigger value
   outside a known-false scope currently turns an otherwise demonstrated
   invariant into `unknown`. A missing earlier response also makes a `within`
   obligation `unknown` even when a known response arrives by the deadline.
   These are conservative false unknowns. Distinguish logical satisfaction,
   evidence completeness, and coverage; only missing values that can change
   the verdict should block it. Give exact property/index diagnostics. Update
   the existing test that encodes the earlier-response rule.
5. **Close parser/schema inconsistencies.** The parser accepts a 64-digit
   minute duration that its canonical millisecond renderer cannot reparse;
   it accepts `language_version: true` or `1.0` as version 1; and it accepts
   unscoped lowercase `upon` despite the documented capitalization rule. Add
   boundary and round-trip tests, then enforce one consistent contract.
6. **Extend transition-focused tests.** Include scope entry and re-entry with
   an already-true condition, overlapping triggers, scope exit during `until`,
   relevant versus irrelevant missing values, work/evidence limits, parser
   boundaries, and an independent short-trace oracle. The current 131-suite
   count includes 114 tests outside this new language and public evaluation.

Before formalizing any private work, create a source-to-clause map for the
selected slice: exact source locator and revision, candidate interpretation,
assumptions, what was omitted, unsupported portions, and the engineer's
decision. The [public evaluation](public-language-evaluation.md) illustrates
why. The [FHWA request requirement](https://ops.fhwa.dot.gov/publications/fhwahop13047/sec3.htm)
also concerns request processing and appropriate responses beyond the one-minute
interval; IDs and timestamps would still not prove the full source. The
[FHWA adaptive-signal template](https://ops.fhwa.dot.gov/publications/fhwahop11027/ap_d.htm)
leaves a threshold unresolved and has neighboring fallback, delivery, and
logging obligations. In the [NASA CONOPS](https://ntrs.nasa.gov/api/citations/20150019623/downloads/20150019623.pdf),
`tli_complete` is recorded but not referenced by the candidate clause, docking
is not a declared property, and the chosen activation event is an
interpretation. Warn when seemingly relevant declarations do not influence a
checked clause.

For the first supervised private trial, mark requirements needing correlated
events, exact timestamps, or mission sequencing **unsupported** unless those
features are implemented and tested. Do not expand the grammar solely because
the public examples contain richer meaning. Preserve the language's
**FRET-inspired** attribution: [FRET's condition guide](https://github.com/NASA-SW-VnV/fret/blob/master/fret-electron/docs/_media/user-interface/examples/condition.md)
distinguishes triggers from holding conditions, while its
[timing guide](https://github.com/NASA-SW-VnV/fret/blob/master/fret-electron/docs/_media/user-interface/examples/timing.md)
does not itself convert time units; no executable equivalence has been tested.
