# Source-informed analysis components

All twelve requested repositories were inspected at fixed revisions on
3 November 2026. The linked contracts retain exact commit/file/line references,
assumptions and execution limits. CSE rebuilds selected small mathematical and
graph operations with the existing runtime and Python standard library.
Upstream packages are isolated research tools, not new plugin dependencies.

| Repository | Useful component selected | CSE route |
|---|---|---|
| [SysML2Tools](https://github.com/demaconsulting/SysML2Tools/tree/c6aa735e75b06982cf8b1805c11c82cafeeabe3d) | Reverse dependency traversal, shortest reason paths, structured relationship metadata. | [Impact analysis](impact-analysis.md) |
| [sysmlv2-validator](https://github.com/ftsrg/sysmlv2-validator/tree/9fd637c47f7ce92673f7df86e944a1570538a9ad) | Explicit graph types, cycle guards and conflicting named-rule rejection. | [Impact analysis](impact-analysis.md) |
| [pmcontrols](https://github.com/arikanatakan/pmcontrols/tree/6ae775d67c4a81b3192a89ac49f27039bf405766) | Declared dependency direction, missing predecessor checks and structured results. | [Impact analysis](impact-analysis.md); no scheduling engine added. |
| [MAPIE](https://github.com/scikit-learn-contrib/MAPIE/tree/c073876f271d28a05e4c2b53639293ff3a805203) | Closed interval coverage with width and explicit validation assumptions. | [Observation computation](observation-validation.md) |
| [uncertainty-toolbox](https://github.com/uncertainty-toolbox/uncertainty-toolbox/tree/6ea1fed6591923a95d49d8049a197e33d4d8092d) | Empirical versus nominal coverage; separation of calibration and evaluation. | [Observation computation](observation-validation.md) |
| [Darts](https://github.com/unit8co/darts/tree/406ecda0ff7d6e20cf2e19effac5024308057c9f) | Central interval score penalizing width and missed observations. | [Observation computation](observation-validation.md) |
| [RAVEN](https://github.com/idaholab/raven/tree/a951729093b7a80e2d8366e5d36cb1552a663cfd) | Weighted population moments and weight-concentration effective size. | [Observation computation](observation-validation.md) |
| [OpenTURNS](https://github.com/openturns/openturns/tree/258b216a0d30bd7b2ac83310b4642852ac849028) | Explicit distribution support, tail endpoints and degenerate probability controls. | [Exact conditional binomial tails](observation-validation.md) |
| [ArviZ](https://github.com/arviz-devs/arviz/tree/8594fc879f920dce1a4d92e0241cf936f0ce65a9) | Aligned datasets and explicit provenance across separately versioned statistical implementations. | [Observation context](observation-validation.md); chain diagnostics remain deferred. |
| [SimPM](https://github.com/Project-SimPM/SimPM/tree/603f0997347f0fa224ee0920c4d5085b989afc96) | FIFO resource contention, per-job waiting records and integrated utilization. | [Queue analysis](queue-analysis.md), with explicit horizon accounting. |
| [SCRAM](https://github.com/rakhimov/scram/tree/b85b78940de38996eeffec54d946824bd4280a1c) | Shared-event identity, minimal cuts and exact-versus-approximate probability distinctions. | [Failure analysis](failure-analysis.md) |
| [KUREAS](https://github.com/curtlsmith/KUREAS/tree/de43fcdf3c95e3a8c4c00fac118bc1ccbef8de89) | Minimal-set absorption, repeated-event quantification, explicit solver limits and failure-mode/effect records. | [Failure analysis](failure-analysis.md) |

The rebuilds use stated definitions: reverse graph reachability across both
revisions; finite sums for scores/moments/binomial tails; FCFS timing recurrence
and interval integrals; stationary M/M/c normalization; and Boolean assignment
enumeration with subset-minimality. They are source-informed implementations,
not a claim of clean-room independence. No upstream implementation or private
engineering data was copied into the CSE runtime. Source licenses and notices
remain in the retained checkouts; the contracts record their license boundaries.

Selected upstream tests ran before rebuilding. SysML2Tools could not run without
.NET; SCRAM's native engine could not build without CMake, although its Python
identity utility ran. OpenTURNS release-wheel controls passed, but a pinned-HEAD
quantile test failed against that different release. RAVEN tests exercised
selected unchanged methods, not its full framework. These limits are retained;
source inspection and partial execution are not full upstream qualification.

The experiments also exposed behaviors deliberately excluded from CSE: accepting
a success prefix after process failure; hashing durations without topology;
omitting idle-tail utilization and unfinished waits; and silently substituting
approximate reliability results. Cross-review of CSE found and repaired a
per-check status error after the diagnostic limit was reached.

No hosted fork is needed for these separate small implementations. A fork is
appropriate only if CSE later needs maintained changes to an upstream tool.
Large forecasting, sensitivity, Bayesian chain diagnostics, routed simulation,
dynamic fault trees and protected acceptance remain separate scoped capabilities.
Quantitative trade studies and morphological alternatives remain held.
