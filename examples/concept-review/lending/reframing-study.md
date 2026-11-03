# Synthetic evidence-driven reframing

This is an authored method example. Its situation, stakeholder statements and
results are synthetic teaching material. No borrower or operator was consulted,
no observation plan was executed, and no operational acceptance is recorded.
The original [brief](brief.md), [model](concept.sysml) and [scope](scope.json)
remain unchanged.

## Before: distinguish the complaint from its explanation

Synthetic setup: the checkout-speed explanation is a hypothesis, not an established cause.

The case describes a borrower who cannot reliably obtain a usable tool and a
desk operator who calls the process "slow checkout." The desired change remains
`N_ACCESS`: access to tools with explicit handling of reported faults. The
boundary `SYS` still covers assessment, checkout, withdrawal, maintenance
coordination and readiness evaluation.

`D_CHECKOUT` proposes prioritizing fewer checkout interactions in `R_APP`, on the
hypothesis that routine handover work `F_ISSUE` causes the access problem. The
competing explanation is that fault handoff and return-to-service responsibilities
are unclear. It matters because that would direct work to `F_WITHDRAW`,
`F_RESTORE`, `F_QUALIFY`, `R_PROC` and the maintenance interface, rather than first
changing the checkout screen. Neither explanation changes the borrower need or
supplies an accepted time limit.

In [reframing-before.sysml](reframing-before.sysml), `Q_CAUSE` connects this
uncertainty to `D_CHECKOUT` and the affected model IDs. `E_DIFFERENTIATE` plans a
comparison of normal checkout `S_NORMAL`, fault reporting `S_FAULT` and maintenance
return `S_MAINT`. Follow a tool record through each case with the desk operator
and maintenance provider; note where work stops, what information is missing and
who can decide the next action. Preserve the normal case as a comparison.

If routine checkout repeatedly stops on entry or confirmation while fault handoff
and return decisions are clear, the result would support `D_CHECKOUT`. If routine
checkout proceeds but a faulted tool has no clear next owner or release basis,
reconsider that priority and return to the fault/recovery explanation. No numeric
cutoff is needed to distinguish these findings. The evidence plan remains
`plan/not_run` in both revisions.

## Supplied results for the worked case

Supplied synthetic result: routine checkout proceeds, while fault handoff and return-to-service decisions stop on unclear responsibility and release criteria.

The authored normal-case account has a clear availability decision and handover
record. In the fault case, the desk records withdrawal but the sample work record
does not identify who accepts the next action. In maintenance return, a sample
maintenance completion record does not identify who authorizes release or the
tool-specific evidence they require. These supplied qualitative findings favor
the competing explanation within this example. They do not estimate frequency,
prove a cause in a real service, or demonstrate maintenance or readiness capability.

## After: return to the affected decision

In [reframing-after.sysml](reframing-after.sysml), the explanation in `K_SERVICE`
and `Q_CAUSE` changes. `D_CHECKOUT` is retained as superseded, with its earlier
rationale visible in the before revision. `D_RECOVERY` proposes investigating
fault ownership and release decisions first. This is a proposal for an engineer,
not an accepted allocation or release authority.

| Work affected | Response to the synthetic finding |
|---|---|
| Need and boundary | Retain `N_ACCESS` and `SYS`; the access problem still matters within the same boundary. |
| Functions and means | Clarify the information and proposed responsibility handoff in `F_WITHDRAW`, `F_RESTORE`, `R_PROC` and `R_APP` to `R_TECH`; keep implementation choices open. |
| Scenarios | Inspect the next-action owner in `S_FAULT` and the unresolved release basis in `S_MAINT`; retain `S_NORMAL` as a comparison. |
| Evaluation | Extend planned fault/readiness walkthroughs to expose missing owners, criteria and records. Keep every original evaluation plan `not_run`. |
| Next decision | Ask the engineer which role and evidence may authorize return to service; do not infer authority from the maintenance role. |

`E_SYN_FINDING` records only an interpretation of the supplied synthetic case,
with source kind `provided`. It is separate from the unexecuted observation plan
and cannot establish real-world validation or approval. Evidence returns to the
explanation and evaluation method as well as to the proposed means.

## Retained scope and local checks

[reframing-scope.json](reframing-scope.json) retains every expectation, topic,
boundary and allocation bound from the original scope, adding only this authored
study as a source. Its separately retained fingerprint is in
[reframing-scope.sha256](reframing-scope.sha256). Both model revisions use that
same scope. All decisions remain proposed or superseded; the original fixture
does not record engineer acceptance, and this study adds none.

Run each revision separately; they share stable IDs and are not an import bundle:

```bash
python3 skills/develop-system-concept/scripts/cse.py check examples/concept-review/lending/reframing-before.sysml --syntax-only --kind concept
python3 skills/develop-operational-scenarios/scripts/cse.py check examples/concept-review/lending/reframing-before.sysml --syntax-only --kind scenario
python3 skills/develop-system-concept/scripts/cse.py concept-review check examples/concept-review/lending/reframing-before.sysml --scope examples/concept-review/lending/reframing-scope.json --scope-sha256 RETAINED_DIGEST --source SYN=examples/concept-review/lending/brief.md --source STUDY=examples/concept-review/lending/reframing-study.md
```

Repeat with `reframing-after.sysml`; use the saved fingerprint as `RETAINED_DIGEST`.
These check syntax, draft shape, source binding and retained documentary coverage.
They do not decide whether the explanation is true or the revised proposal is
appropriate. The regression suite also removes the maintenance responsibility and
relabels a retained evaluation plan; both defects must still be detected against
the same scope after reframing.
