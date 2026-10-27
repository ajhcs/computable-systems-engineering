# Source-grounded diagram references

Use these references to study how a selected engineering question can be presented. Start with the linked source and its version, then compare it with the explicitly scoped derivative. The examples do not authorize a new system design or establish that a real system meets a requirement.

- [TMT and APE reference slices](../examples/engineering-reference/README.md) cover a maintenance state machine, a timing boundary, composition, and an optical context.
- The [TMT action and sequence extension](../examples/engineering-reference-extension/README.md) distinguishes concurrent control and object flows from an untimed exchange order.
- [Central-fill pharmacy views](../examples/pharmacy-source-view-reference/README.md) show selected structural roles, their multiplicities, and the difference between owned parts and referenced resources.
- [Matched presentation studies](../examples/diagram-style-prototypes/README.md) apply several visual treatments to selected source-linked views. They are design studies, not a proven preference ranking.
- The [native-v2 composition study](../examples/native-v2-composition/README.md) preserves a bounded pilot-tool view and explains what its renderer does and does not show.
- [NASA, NIST and APE presentation references](../examples/ecosystem-diagram-reference/README.md) illustrate selected maintenance, smart-grid and allocation questions with their source-specific attribution.
- [Industrial NIST references](../examples/industrial-project-reference/README.md) include selected wireless-controller views and a separate MakeCoupler reading. Their scopes differ; omitted original figures and held presentations are identified in the guide.

The linked upstream archives and reports are the original sources. This repository contains selected, attributed derivatives and source notices, not the original raw XML or complete source archives. Concise fact ledgers express the selected interpretation for checking the supplied artifacts; they do not replace the original model or prove complete equivalence. Keep private source copies and historical machine-specific receipts out of Git.

Use the reference pack's checks for the named local consistency claims. The packaging screen, `python3 scripts/check_reference_release.py`, looks for specified raw-source markers, local paths, malformed diagrams and selected embedded metadata. It is not a legal review, a complete data-loss-prevention scan, a source-truth check, or engineering acceptance. Source-specific rights and the separate limits in each guide still apply.

The [TMT/APE guide](../examples/engineering-reference/README.md), [pharmacy guide](../examples/pharmacy-source-view-reference/README.md), [ecosystem guide](../examples/ecosystem-diagram-reference/README.md), and [industrial guide](../examples/industrial-project-reference/README.md) list their bounded consistency checks and any separate local-source prerequisites. The repository regression suite includes those public checks; it does not require or authenticate the withheld original archives.
