---
name: plan-engineering-evidence
description: Plan verification of specified requirements or validation of intended use. Use to select evidence methods, define collection conditions or review testability of an intermediate product.
---

Identify the claim, governing source and model revision, applicable conditions and decision the evidence should inform. A plan for one claim or intermediate product can be the complete result. Preserve accepted obligations and thresholds. Keep missing intent, data and authority explicit.

Choose inspection, test, analysis/simulation or demonstration using [method selection](references/methods.md). Match the method to the intended claim. Verification compares a specified requirement with evidence. Validation addresses stakeholder needs in the intended use. Use [testability and feedback](references/testability.md) when observation points, fixtures, equipment or manual effort affect the design. Use [measure definitions](../define-engineering-measures/SKILL.md) for quantities and collection conditions.

For recorded plans, use the existing [`cseWorkflow` evidence and linked question/decision fields](../../docs/concept-review.md#authoritative-sysml-documentary-record). Record the target, purpose, method, environment, basis and limitations, with `mode: plan` and `result: not_run`. Link equipment, fixtures, definition revisions and evidence locations as needed. Keep project models and reports private. When retained concept scope exists, use the existing launcher to select the next investigation:

```sh
python3 <skills-dir>/develop-system-concept/scripts/cse.py concept-review next-evidence MODEL.sysml --scope SCOPE.json --scope-sha256 RETAINED_DIGEST --source ID=SOURCE_PATH
```

Use the absolute launcher path from the complete plugin or checkout. Supply explicit model dependencies and repeat `--source` as needed. Scenario-only plans can proceed without a concept scope.

For requested, authorized execution, choose the contract that can answer the claim:

- [Engineering analysis](../../docs/engineering-analysis.md), [behavior checks](../../docs/behavior-review.md) or [coupled calculations](../../docs/coupled-calculations.md) for supported model properties.
- [Variable-influence tests](../../docs/variable-influence-tests.md) for synthetic pass/fail pairs. Record these as generated examples.
- [Prototype observations](../../docs/prototype-evaluation.md) or [observation validation](../../docs/observation-validation.md) for evidence already collected under explicit conditions.
- [Queue analysis](../analyze-queues/SKILL.md) or [failure analysis](../analyze-system-failures/SKILL.md) for their supported models.

Use [meaning and context](../../docs/meaning-context.md) to check that evidence addresses the actual claim. A plan is reviewable when the engineer can identify the observation or calculation, its conditions and what result would inform the decision. When work was executed, report actual findings against retained scope with limitations. Use [artifact freshness](../../docs/artifact-freshness.md) for generated outputs and [change review](../../docs/engineering-change-review.md) when a finding changes dependent work. Preserve failed findings, rerun affected checks and keep engineer acceptance explicit.
