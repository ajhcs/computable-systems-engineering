# Bounded failure analysis

The failure helper checks an explicitly authored AND/OR fault tree and FMEA
record consistency. It returns complete minimal cut sets within stated bounds,
retains repeated-event identity, and can compute exact conditional probability
when the engineer supplies mutual independence, mission and event probabilities.
It adds no runtime dependency. Read the
[record contract](../skills/analyze-system-failures/references/record-contract.md)
before authoring records; the independently invocable
[failure skill](../skills/analyze-system-failures/SKILL.md) uses the same checker.

```text
python3 scripts/failure_analysis.py examples/failure-analysis/shared-event.json
python3 scripts/failure_analysis.py examples/failure-analysis/qualitative.json --required fault_tree
python3 scripts/failure_analysis.py examples/failure-analysis/qualitative.json --required probability
python3 -B tests/test_failure_analysis.py
```

The third command fails because a required probability check cannot proceed
without authored assumptions. The [incomplete basis example](../examples/failure-analysis/incomplete-basis.json)
returns unknown. A qualitative pass makes no numerical reliability claim.

For `(A AND B) OR (A AND C)`, minimal cuts are `{A,B}` and `{A,C}`. Under explicit
mutual independence, `P = pA * (pB + pC - pB*pC)`. With probabilities `1/100`,
`1/200`, `1/500`, the exact result is `699/10000000`. A appears once in each
assignment, including the overlap term; repeated appearances are not new events.
The example probabilities and bases are synthetic. Actual effects, common causes,
independence and mission applicability remain engineering judgments.

## Source inspection and reuse decision

The public repositories below were inspected at pinned revisions on 2026-11-03
UTC through the connected GitHub tools and isolated read-only source checkouts.
Their source, licenses and tests informed selection. No upstream implementation
code is copied into the CSE checker. The truth-table, subset-minimality and exact
disjoint-assignment algorithms were written directly from Boolean and probability
definitions. GPL source is neither vendored into CSE nor relicensed.

| Primary source | Useful components and disposition |
|---|---|
| [SCRAM b85b7894, BDD constructor/analysis](https://github.com/rakhimov/scram/blob/b85b78940de38996eeffec54d946824bd4280a1c/src/bdd.cc#L40-L89) and [ZBDD minimality](https://github.com/rakhimov/scram/blob/b85b78940de38996eeffec54d946824bd4280a1c/src/zbdd.cc#L613-L667) | Preserve shared event identity and distinguish Boolean function evaluation from minimal-set extraction. CSE uses a small exhaustive truth table and immediate-subset tests. BDD/ZBDD compression and MOCUS module algorithms remain outside this increment. |
| [SCRAM AB OR BC regression](https://github.com/rakhimov/scram/blob/b85b78940de38996eeffec54d946824bd4280a1c/tests/bench_core_tests.cc#L39-L54) and [input](https://github.com/rakhimov/scram/blob/b85b78940de38996eeffec54d946824bd4280a1c/tests/input/core/ab_bc.xml) | Distinguish exact probability `0.074` from rare-event approximation `0.08` with `pA=.1,pB=.2,pC=.3`; retain minimal cuts `{A,B}`, `{B,C}`. CSE tests the same mathematical control with independent exact fractions; SCRAM's native engine was not executed. |
| [SCRAM license](https://github.com/rakhimov/scram/blob/b85b78940de38996eeffec54d946824bd4280a1c/LICENSE) and [file notice](https://github.com/rakhimov/scram/blob/b85b78940de38996eeffec54d946824bd4280a1c/src/bdd.cc#L1-L15) | GPL-3.0-or-later. A future separately invoked optional SCRAM tool must retain its own license and execution/result boundary. No fork or dependency is needed for the bounded current checker. |
| [KUREAS de43fcdf, engine boundary](https://github.com/curtlsmith/KUREAS/blob/de43fcdf3c95e3a8c4c00fac118bc1ccbef8de89/FTL/KUREAS-FTL.html#L95-L105), [absorption](https://github.com/curtlsmith/KUREAS/blob/de43fcdf3c95e3a8c4c00fac118bc1ccbef8de89/FTL/KUREAS-FTL.html#L517-L543), [quantification](https://github.com/curtlsmith/KUREAS/blob/de43fcdf3c95e3a8c4c00fac118bc1ccbef8de89/FTL/KUREAS-FTL.html#L1297-L1327) | Reuse the conceptual separation of a deterministic core from UI/worker state, subset absorption, exact shared-event evaluation, and labelled approximate methods. CSE provides a library and CLI, complete bounded cuts and exact fractions; no MCUB/hybrid fallback is promoted to exact success. |
| [KUREAS shared-event test](https://github.com/curtlsmith/KUREAS/blob/de43fcdf3c95e3a8c4c00fac118bc1ccbef8de89/SYS/SQA/KUREAS-SYS-TestSuite.html#L23866-L23871) and [FMEA effect view](https://github.com/curtlsmith/KUREAS/blob/de43fcdf3c95e3a8c4c00fac118bc1ccbef8de89/SYS/KUREAS-SYS.html#L57025-L57149) | Preserve component, failure mode and recorded effects as connected data. CSE checks explicit row completeness and basic-event references, without inventing scores or claiming prose effect correctness. KUREAS's graphical and broader failure-distribution features remain upstream. |
| [KUREAS license](https://github.com/curtlsmith/KUREAS/blob/de43fcdf3c95e3a8c4c00fac118bc1ccbef8de89/LICENSE) | MIT, copyright 2026 Curtis. No source code is redistributed; source notices remain in the private upstream checkouts used for tests. |

The isolated upstream smoke executed KUREAS's unmodified `KUREAS_QUANT_FACTORY`
under Node. Its `solve` produced `{A,B}`, `{A,C}` and exact BDD probability
`0.0000699`; `minimize` removed duplicate and absorbed cuts. Its separately
reported MCUB was `0.000069999`, illustrating why the two methods cannot share an
exactness claim. The first smoke used an incorrect `model:fixed` event shape and
returned missing data; the corrected `model:prob` invocation passed. That failed
attempt is retained in the private evidence.

SCRAM's actual `BasicEvent`/`Event.add_parent`/`Event.is_common` source utility ran
and recognized one shared event with two parents. Native risk analysis was not
run: no `scram` binary or CMake executable was installed, and the attempted native
configuration stopped at `cmake: command not found`. The utility smoke is not
native solver execution. A future upstream fork would be useful only for an
actual upstream fix; this increment needs neither fork nor remote mutation.

The CSE suite covers shared events/causes, absorption/idempotence, independent
hand-derived controls, exact zero/one, qualitative analysis, retained missing
checks, incomplete bases, FMEA references and duplicate pairs, disconnected
invalid content, cycles, strict types, unsupported semantics, enumeration/output
limits, depth limits, deterministic ordering and strict CLI input. Passing these
synthetic checks supplies bounded implementation evidence, not field reliability,
complete failure coverage, source truth or stakeholder acceptance.
