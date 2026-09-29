# Public-case evaluation of controlled language profile 1

**Status:** reproducible evaluation with synthetic observations, 2026-09-29.
The three source passages below were inspected at their linked locations. Each
formal sentence is a *candidate interpretation* for testing the checker, not a
source-authorized requirement or evidence of a deployed system. `pass` means
only that the particular sampled trace satisfies the candidate sentence.
See the independent [readiness review](language-readiness-review.md) for
adjustments recommended before applying the profile to private work.

Run `python3 -B tests/test_public_language_cases.py` for all variants and
`python3 -B scripts/requirements.py
examples/language/public/nasa_low_power_candidate.json --review --json` for an
inspectable CLI example. The tests generate FHWA trace rows in Python to avoid
committing hundreds of repetitive 100 ms samples.

| Source and candidate | Expected boundary | Observed checker result | Adequacy finding |
|---|---|---|---|
| [FHWA-HOP-13-047 §3.6.2](https://ops.fhwa.dot.gov/publications/fhwahop13047/sec3.htm): last request byte to first response byte within one minute; candidate `request_complete` → `response_started` | On a declared 100 ms clock, trigger at index 1 gives inclusive deadline 601. A response pulse at 601 passes, at 602 fails, and a trace ending at 600 remains unresolved. | `pass`, `fail` at deadline index 601, `unknown` | The deadline arithmetic and finite-prefix treatment work. Boolean pulses lose request identity and exact byte timestamps. In an additional trace with two requests and one response, the checker returns `pass` because the one response discharges both obligations. That result cannot establish the source's per-request claim. |
| [FHWA-HOP-11-027 Appendix D §13.2-3](https://ops.fhwa.dot.gov/publications/fhwahop11027/ap_d.htm): alarm within a template's “XX minutes” | The placeholder must not compile. A separate **hypothetical**, engineer-supplied two-minute value can exercise pass at the inclusive deadline, failure one tick late, and an unfinished prefix. | `grammar` error for `XX`; then `pass`, `fail`, `unknown` for the hypothetical bound | The parser correctly refuses to invent the missing threshold. None of the hypothetical results validates a selected ASCT requirement. The document's “real time” fallback wording in §13.2-1.0-2 also needs a precise timing interpretation before this profile can check it. |
| [NASA Love and Hill CONOPS §5, printed p. 9](https://ntrs.nasa.gov/api/citations/20150019623/downloads/20150019623.pdf): co-manifested element stays in low-power configuration until Orion docks and supplies supplementary power after trans-lunar injection | In a candidate hold clause, low power through trans-lunar injection and up to the first later supplementary-power observation passes; early loss fails; missing release remains unresolved. | `pass`, `fail` at index 2, `unknown` | The `until` boundary works. A contrived trace that makes supplementary power available *before* trans-lunar injection also returns `pass`: the clause has no event-order or causal model. The source is CONOPS narrative, so even the candidate SHALL meaning needs engineer review. |

The FHWA response requirement measures actual byte-event times in
milliseconds. A 100 ms sampled trace can express a 60-second grid deadline but
cannot prove that real events between samples met it. Correlated request IDs,
actual event timestamps, and a declared event-capture rule would be needed for
faithful verification. The NASA case also needs either a second supported
ordering obligation or a scenario transition model connecting trans-lunar
injection, docking, and power transfer. Those changes should retain a visible
source-to-clause mapping and independent engineer decision on the meaning.

The immediate result is that profile 1 is useful for checking **bounded
sampled-trace claims** and for refusing unspecified thresholds. It is not yet
adequate to declare either the full FHWA request-processing requirement or the
NASA operational sequence verified. All trace values here are constructed
test data, not measurements.
