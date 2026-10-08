# Inspect and compare

Run `cse.py discover`, then `cse.py describe inspect` or `describe diff`.
Pass an `invoke` JSON object on stdin with `operation` and `arguments`.
An inspect ID identifies a concern, use case or requirement; include every file
needed to resolve imports. It returns parsed context, not a behavior verdict.
Diff returns structural/documentation changes and conservative direct impact.
It cannot decide whether a changed statement preserves engineering meaning.

Missing files and IDs are actionable errors, not questions about engineering
preferences. Read known facts first. Existing `view`, `diff`, `finite` and legacy
helpers remain available. SysML v1 archives, Simulink, Modelica and spreadsheets
require their native tools or an explicitly reviewed export. Do not relabel
them as SysML v2. The adapter refuses unsupported suffixes before parsing.
