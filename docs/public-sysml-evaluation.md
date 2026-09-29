# Public-source SysML alpha evaluation

These small models are **candidate interpretations** of public passages, not
adopted requirements or evidence about deployed systems. All observations are
synthetic. They test whether the SysML parser, controlled-text compiler,
binding, and finite-trace monitor behave as declared.

| Source and selected slice | Reproducible result | Meaning and remaining gap |
|---|---|---|
| [FHWA-HOP-13-047 §3.6.2](https://ops.fhwa.dot.gov/publications/fhwahop13047/sec3.htm), [candidate model](../examples/sysml/public/fhwa-response-candidate.sysml) | Two overlapping request IDs with responses at 1 s and exactly 60 s pass. Wrong ID or 60.001 s fails. A prefix ending at 59 s is unknown. | Exact event timestamps and correlation address a limitation of the earlier sampled-Boolean candidate. The source also requires processing the request and initiating an appropriate response; this checker only tests the first-byte timing slice. `requestId` and complete capture are explicit modeling assumptions. |
| [NASA Love and Hill CONOPS, printed p. 9](https://ntrs.nasa.gov/api/citations/20150019623/downloads/20150019623.pdf), [candidate model](../examples/sysml/public/nasa-low-power-candidate.sysml) | A low-power hold through the first later supplementary-power sample passes; early loss fails; no observed release is unknown. | The candidate `until` clause does not establish docking, causal power transfer, or the larger mission sequence. A trace with supplementary power already available before trans-lunar injection can still pass. |

The [synthetic variable-influence generator](variable-influence-tests.md) finds
pass/fail pairs for all three referenced properties in the NASA sampled clause.
It reports the FHWA correlated-event clause as unsupported for test generation;
the supplied event trace checker still handles that clause. Neither result
establishes the correctness of either source interpretation.

Run `python3 -B tests/test_sysml_public.py` or inspect each candidate with the
`scripts/sysml.py` commands in the [profile](sysml-v2-profile.md). A local pass
is scoped to the modeled clause and supplied observations. The engineer would
need to decide whether these interpretations and assumptions are appropriate
before applying them to an actual system baseline.
