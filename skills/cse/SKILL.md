---
name: cse
description: Discover CSE engineering commands, inspect or validate models, compare revisions, and route concept, CONOPS or scenario work.
---

Use `python3 <skill-dir>/scripts/cse.py discover` for the compact command list.
Load `describe OPERATION` only for the next operation; pipe an `invoke` request
with `operation` and `arguments` on stdin. Report actual scope and findings;
`--detail` returns omitted evidence. Missing runtime, unsupported formats and
unknown checks cannot be reported as successful validation.

For engineering drafting, load only the matching sibling skill:
`develop-system-concept`, `develop-conops` or `develop-operational-scenarios`.
Combined work uses one shared model. Preserve engineer authority and raw sources;
store user artifacts in ignored `work/`. An ordinary local command needs no
domain question. For missing consequential intent, load
[domain elicitation](../../docs/interface/elicitation.md). Provider permission
confirmations remain with the host. This skill grants no acceptance or migration
authority; legacy/native format conversion requires explicit meaning review.
