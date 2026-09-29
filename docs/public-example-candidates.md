# Public systems-engineering examples for language evaluation

These are small, attributed candidates for an engineer to formalize. They are
source material, not accepted requirements in this repository, implementation
evidence, or proof that the proposed language captures the authors' intent.
Record the exact source revision and resolve each ambiguity before promoting a
candidate to a governed requirement. Keep copied source text out of fixtures.
The [public-case evaluation](public-language-evaluation.md) now exercises three
derivatives and records the observed limits.

| Source and location | Useful operational concept | Candidate profile use | Decision needed before formalization |
|---|---|---|---|
| [FHWA Real-Time System Management Information Program Data Exchange Format Specification, §3.6.2](https://ops.fhwa.dot.gov/publications/fhwahop13047/sec3.htm) | An external request leads to a response within one minute. The source defines the interval from receiving the last request byte to transmitting the first response byte. | `Upon request_received = true, Interface shall within 1 minute satisfy response_started = true.` This exercises the inclusive deadline and a precisely defined event pair. | Define sampling, event capture, simultaneous events, and whether each request needs its own correlated response. Our Boolean level response cannot establish per-request matching. |
| [FHWA Model Systems Engineering Documents for Adaptive Signal Control Technology Systems, Appendix D, requirements 13.2-1 through 13.2-3](https://ops.fhwa.dot.gov/publications/fhwahop11027/ap_d.htm) | Communication loss leads to a local fallback or alarm. The alarm timing is a template placeholder (“XX minutes”). | `Upon communications_failed = true, Controller shall within D minutes satisfy alarm_active = true.` A fallback state could use `until`, if its release event is defined. | The document is a template. `D` is deliberately unresolved; inventing it would make a false computable claim. Define fault detection and release behavior. |
| [NASA Love and Hill, *Concept of Operations for a Prospective Proving Ground in Lunar Vicinity*, §§5 and 7](https://ntrs.nasa.gov/citations/20150019623) | Lunar mission modes, low-power operations, and off-nominal rescue or communication scenarios provide a mode and scenario context. | A scoped hold or bounded response could test mode entry, release, and incomplete observations. | Narrative CONOPS language is not a ready-made SHALL. Establish the system boundary, controlled actor, exact events, timing origin, and accepted obligations with the engineer. |

The first source offers a real boundary-timing case for a derivative fixture once
the event model is agreed. The second is a valuable rejection case: a placeholder
cannot pass grammar or unit checking as a numeric duration. The third tests
whether the language is useful for a CONOPS without treating every descriptive
sentence as a formal requirement. A separate synthetic fixture in
[`examples/language/valid.json`](../examples/language/valid.json) establishes
the checker semantics without assuming any of these sources has been accepted.
