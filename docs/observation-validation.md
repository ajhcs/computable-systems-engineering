# Bounded observation computation

`scripts/validate_observations.py` computes interval scores, weighted descriptive
moments and conditional binomial probabilities from one explicit
`observation-validation-1.0` record. It adds no runtime dependency. `pass` means
that the supported computation and declared context checks completed; it does
not mean that a prediction, system, simulation or engineering decision passed
validation. No targets or acceptance thresholds are supplied.

```sh
python3 scripts/validate_observations.py examples/validation/synthetic-observations.json --required Intervals --required Weighted --required Tail --format text
python3 -B tests/test_validation.py
```

Use this helper after defining a measure and collecting aligned observations.
Retain the measure's ID and revision, collection boundary and input record. The
measure link is documentary: this command does not resolve a definition file,
authenticate its revision, collect observations, fit a model or establish source
truth. A definition's structural check and observed-data computation are separate
evidence. Connect the resulting discrepancy to an engineering question before
changing an accepted definition, design or threshold.

## Record and scope

All named fields are required; unknown fields are errors. Numbers are exact
integer, decimal or rational strings under the existing arithmetic grammar.
Binary floating-point values, code and expression strings are refused.

| Top-level field | Contract |
|---|---|
| `version` | Exactly `observation-validation-1.0`; another version is unsupported. |
| `id`, `revision` | Stable engineering identifier and bounded explicit revision text. |
| `measure` | Exactly `{id, revision, unit}`; unit is the existing explicit unit map with no conversions. |
| `dataset` | Exactly `{id, revision, population, boundary, window, sampling, role, basis}`. `role` is `held_out`, `training`, `calibration`, `simulation` or null. Other context fields are text or null; null prevents overall success. |
| `assumptions` | ID map of `{kind, text, basis}`. Basis is text or null. A selected null basis prevents success. Presence records an authored assertion; it does not verify that assertion. |
| `checks` | Nonempty ID map of the three supported check records below. All authored checks run. |
| `unknowns` | List of `{field, question}`. Any unresolved question prevents overall success. |

Assumption kinds are `sample_alignment`, `central_interval`,
`held_out_separation`, `weight_meaning`, `independent_trials`,
`common_probability` and `binary_outcome`. Each check selects assumption IDs
through its `assumptions` list. Selected IDs must exist. The checker requires
the relevant kinds, while the engineer supplies their actual meaning and basis.
The presence of a kind does not establish its applicability in the world.

Repeat `--required CHECK_ID` to retain an external expected set. An absent
expected check fails even if the remaining authored checks compute successfully.
Without that argument, external obligation completeness is `not_evaluated`.
The caller's selected scope remains editable and unauthenticated.

## Interval computation

An interval check has exactly `{kind, purpose, alpha, rows, assumptions}`, with
`kind: "interval"`, `purpose: "descriptive"` or `"held_out_validation"`, exact
`0 < alpha < 1`, and rows `{id, actual, lower, upper}`. Row IDs are unique within
the check. Every row uses the linked measure's same declared unit. Bounds must
be ordered; reversed bounds are errors rather than silently taking absolute
width. Missing data are errors rather than silently omitted observations.

Select `sample_alignment` and `central_interval` assumptions. The latter states
the interpretation of the supplied bounds as the central interval associated
with nominal coverage `1-alpha`; the checker does not infer a predictive
distribution. For `held_out_validation`, also select `held_out_separation` and
declare `dataset.role: "held_out"`. A training, calibration, simulation or
unknown role leaves that check unknown even when descriptive metrics compute.
Descriptive summaries can use those roles without claiming held-out validation.

For `n` rows, the helper reports closed-endpoint coverage
`count(lower <= actual <= upper)/n`, nominal coverage, their signed difference,
mean width, and mean central interval score. A row's score is
`upper-lower + (2/alpha)*distance`, where distance is zero inside the interval,
`lower-actual` below it and `actual-upper` above it. Width and score retain the
measure's unit; coverage and its gap are dimensionless. Below/above row IDs
retain inspectable misses. A zero-width interval is valid when bounds agree.

These are realized sample scores, not a confidence interval, a hypothesis-test
verdict or a guarantee of future coverage. Wider intervals can increase coverage
without improving prediction; retaining both width and penalized score exposes
that tradeoff. This command does not construct conformal intervals, prove
exchangeability, estimate subgroup coverage, or select a model from these scores.

## Weighted population summary

A weighted summary has exactly `{kind, rows, assumptions}`, with
`kind: "weighted_summary"`, rows `{id, value, weight}`, and a selected
`weight_meaning` assumption. Weights are explicit nonnegative dimensionless
relative masses with strictly positive total. Zero weights contribute no mass;
their rows remain in `n` and are distinguished from `positive_weight_rows`.
No missing weights or uniform weighting are inferred.

The output is `mean=sum(w*x)/sum(w)`, population variance
`sum(w*(x-mean)^2)/sum(w)`, and weight effective size
`sum(w)^2/sum(w^2)`. Variance carries squared measure units. These quantities are
unchanged by a positive common scaling of weights. A single positive-mass row
has zero population variance and effective size one. There is no unbiased sample
variance correction, confidence bound or independence claim. Weight effective
size measures weight concentration; it is not an autocorrelation-adjusted Monte
Carlo ESS or an established count of independent observations.

## Conditional binomial tail

A binomial check has exactly `{kind, n, k, probability, tail, assumptions}`, with
`kind: "binomial_tail"`, integer `1 <= n <= 256`, `0 <= k <= n`, exact
probability `p` in `[0,1]`, and tail `le` or `ge`. It needs selected
`independent_trials`, `common_probability` and `binary_outcome` assumptions.

It computes the exact sum of `choose(n,i)*p^i*(1-p)^(n-i)` for `i=0..k` or
`i=k..n`, respectively. The endpoints are inclusive. The result is dimensionless
and conditional on the authored iid Bernoulli model. It is not an automatically
chosen p-value, a fitted probability, a confidence interval, or a demonstration
that these assumptions describe collected observations. The command never
infers independence from a successful sum or supplies a decision threshold.

## Limits and evidence

Inputs are regular non-symlink UTF-8 JSON files up to 262,144 bytes. Duplicate
keys and nonfinite values are refused. Records are bounded to 12,000 value
nodes, depth 16, 2,048 characters per text/key, 32 checks, 32 assumptions, 32
unknowns and 512 rows per check. Exact rationals retain the existing 80-character
literal and 4,096-bit result limits. Binomial work is at most 257 terms per
check and has a conservative rational-growth guard before exponentiation.
Schema-limit errors and incomplete numeric computations cannot pass.

Reports retain checker version, limits, record digest, file-byte digest through
the CLI, measure and dataset identity, selected assumptions, expected/completed
checks and exact metrics. Hashes identify supplied content and authenticate no
decision. `computed_checks` retains metrics computed even when their applicability
is unknown; those unknown checks are excluded from `completed_checks`.
Unknown, unsupported, failed and errored checks prevent overall
success. At most 64 findings are retained; a reached diagnostic limit is visibly
incomplete. Text displays 12 findings; JSON retains all bounded findings.

The local tests include hand-calculated interval/weight controls; independent
enumeration of all fair-coin outcomes for `n=1..8`; both tails and degenerate
probabilities; missing applicability and required scope; training-role misuse;
malformed data, units and numeric-growth limits. They establish bounded software
behavior, not physical or statistical applicability of a real dataset.

## Source-informed rebuild and reuse decisions

The following exact upstream revisions, licenses, implementations and tests were
inspected on 2026-11-03 UTC using the GitHub connector and isolated read-only
source checkouts. CSE's routines were authored after that inspection from the
explicit formulas above. They are source-informed reimplementations, not a
claim of clean-room independence. No upstream code or skill text is copied into
the CSE runtime. Clones and execution environments retain their own licenses
outside public artifacts; these references imply no endorsement.

| Repository and inspected implementation | Useful component and CSE decision |
|---|---|
| [MAPIE `c073876f271d28a05e4c2b53639293ff3a805203`](https://github.com/scikit-learn-contrib/MAPIE/tree/c073876f271d28a05e4c2b53639293ff3a805203), BSD-3-Clause. [`mapie/metrics/regression.py` lines 18–132](https://github.com/scikit-learn-contrib/MAPIE/blob/c073876f271d28a05e4c2b53639293ff3a805203/mapie/metrics/regression.py#L18-L132); [`test_metrics.py` lines 288–309 and 579–594](https://github.com/scikit-learn-contrib/MAPIE/blob/c073876f271d28a05e4c2b53639293ff3a805203/mapie/tests/test_metrics.py#L288-L309). | Retain closed interval coverage and width together. CSE rejects reversed bounds rather than reproducing absolute width. Defer estimator fitting/conformalization; its [theory lines 19–50](https://github.com/scikit-learn-contrib/MAPIE/blob/c073876f271d28a05e4c2b53639293ff3a805203/doc/content/conformal-prediction/theory.md#L19-L50) distinguishes marginal guarantees and exchangeability assumptions from realized coverage. |
| [Darts `406ecda0ff7d6e20cf2e19effac5024308057c9f`](https://github.com/unit8co/darts/tree/406ecda0ff7d6e20cf2e19effac5024308057c9f), Apache-2.0. [`metrics.py` lines 3664–3790](https://github.com/unit8co/darts/blob/406ecda0ff7d6e20cf2e19effac5024308057c9f/darts/metrics/metrics.py#L3664-L3790); [`test_metrics.py` lines 96–114 and 2416–2467](https://github.com/unit8co/darts/blob/406ecda0ff7d6e20cf2e19effac5024308057c9f/darts/tests/metrics/test_metrics.py#L96-L114). | Rebuild the central Winkler interval score with exact supplied bounds and alpha. Defer forecasting, quantile interpolation, time intersection and configurable NaN reductions; CSE requires aligned explicit rows. Darts supports asymmetric quantile intervals; this first CSE contract supports central intervals only. |
| [uncertainty-toolbox `6ea1fed6591923a95d49d8049a197e33d4d8092d`](https://github.com/uncertainty-toolbox/uncertainty-toolbox/tree/6ea1fed6591923a95d49d8049a197e33d4d8092d), MIT. [`metrics_calibration.py` lines 39–136 and 303–393](https://github.com/uncertainty-toolbox/uncertainty-toolbox/blob/6ea1fed6591923a95d49d8049a197e33d4d8092d/uncertainty_toolbox/metrics_calibration.py#L303-L393); [`test_metrics_calibration.py` lines 25–80](https://github.com/uncertainty-toolbox/uncertainty-toolbox/blob/6ea1fed6591923a95d49d8049a197e33d4d8092d/tests/test_metrics_calibration.py#L25-L80). | Preserve held-out role and explicit empirical-minus-nominal gap at the selected interval level. Defer aggregate calibration-curve area, Gaussian residual assumptions and recalibration fitting; a single gap is not a full-distribution calibration assessment. |
| [RAVEN `a951729093b7a80e2d8366e5d36cb1552a663cfd`](https://github.com/idaholab/raven/tree/a951729093b7a80e2d8366e5d36cb1552a663cfd), Apache-2.0. [`BasicStatistics.py` lines 437–479 and 571–589](https://github.com/idaholab/raven/blob/a951729093b7a80e2d8366e5d36cb1552a663cfd/ravenframework/Models/PostProcessors/BasicStatistics.py#L437-L479); [statistical theory lines 15–85](https://github.com/idaholab/raven/blob/a951729093b7a80e2d8366e5d36cb1552a663cfd/doc/theory_manual/statisticalAnalysis.tex#L15-L85). | Rebuild weighted population moments and concentration-based effective size, requiring explicit weight meaning. Preserve the distinction from unbiased variance correction. Defer simulator orchestration, uncertainty propagation, sensitivity and automatic default weights. A summary of simulation output does not validate the simulation. |
| [OpenTURNS `258b216a0d30bd7b2ac83310b4642852ac849028`](https://github.com/openturns/openturns/tree/258b216a0d30bd7b2ac83310b4642852ac849028), LGPL library; bundled components retain separate notices. [`Binomial.cxx` lines 125–168](https://github.com/openturns/openturns/blob/258b216a0d30bd7b2ac83310b4642852ac849028/lib/src/Uncertainty/Distribution/Binomial.cxx#L125-L168); [`t_Binomial_std.py` lines 60–126](https://github.com/openturns/openturns/blob/258b216a0d30bd7b2ac83310b4642852ac849028/python/test/t_Binomial_std.py#L60-L126). | Rebuild a finite conditional binomial sum with exact rational arithmetic, rather than reusing its native incomplete-beta numerical implementation. Preserve tail endpoint semantics and degenerate-probability controls. Defer inverse quantiles, distribution fitting, confidence intervals and the native dependency. |
| [ArviZ `8594fc879f920dce1a4d92e0241cf936f0ce65a9`](https://github.com/arviz-devs/arviz/tree/8594fc879f920dce1a4d92e0241cf936f0ce65a9), Apache-2.0. [`src/arviz/__init__.py` lines 37–117](https://github.com/arviz-devs/arviz/blob/8594fc879f920dce1a4d92e0241cf936f0ce65a9/src/arviz/__init__.py#L37-L117); [`tests/test_namespace.py` lines 24–96 and 153–172](https://github.com/arviz-devs/arviz/blob/8594fc879f920dce1a4d92e0241cf936f0ce65a9/tests/test_namespace.py#L24-L96). | Its current repository is a namespace over separately versioned base/stats/plots packages. Retain explicit dataset/revision/alignment and computation provenance rather than attributing statistical functions to the namespace source. Defer HDI, posterior predictive checks, R-hat and autocorrelation ESS until named chain/draw axes and diagnostics have their own supported contract. |

Selected upstream execution is separate from the CSE tests. Pinned MAPIE, Darts
and uncertainty-toolbox sources ran through their normal imports; focused suites
passed 3, 4 and 12 tests respectively. ArviZ's pinned namespace suite passed 15
tests; a delegated HDI smoke used separately installed `arviz_stats==1.3.3`.
Selected unmodified RAVEN method ASTs ran with NumPy/xarray and numeric controls;
its full framework was not run. OpenTURNS native release `1.27.post1` passed the
selected CDF/tail controls, while the pinned HEAD's full `t_Binomial_std.py`
failed at line 72 on a degenerate upper-tail quantile against that release. No
pinned-HEAD native OpenTURNS build or full upstream-suite qualification is
claimed. The retained private research records distinguish those executions.
