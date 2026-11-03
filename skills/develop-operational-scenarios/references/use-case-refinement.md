# Refine use cases when reuse or an exception matters

Keep the subject, boundary, actor goal, trigger and observable outcome explicit.
Start from the selected scenario paths, with stable IDs for the steps and use
cases. A use case describes a service toward an actor goal; a scenario is one
selected path. Actor roles are relative to that subject and use case, not fixed
properties of a person or organization.

When several paths perform the same behavior, compare their actual preconditions,
steps and outcome. Factor a common fragment into an included use case only if
that behavior is required at the relevant invocation in each including case.
Retain the invocation points and parameter/item correspondence. Similar wording
alone does not establish shared behavior.

For a conditional extension, retain the base use case, extension point, activating
condition and added behavior. Confirm that the base still has a meaningful
outcome without the extension. Keep failure/exception conditions in the scenario
where they arise; do not force every exception into an `extend` relationship or
make an optional fragment required through `include`. Preserve repeated calls
and meaningful differences instead of deduplicating them mechanically.

Review affected paths after refactoring: where is common behavior invoked, what
must be true there, what changes, and which actor goal is still reached? Show
unclear or lost meaning as a finding for those IDs. Carry scenario/function
correspondence through the same IDs using [activity and function review](activity-review.md).

Keep this refinement documentary unless an explicit supported execution contract
is supplied. `foundation-1.0` admits `base`, `included` and `extension` categories
but returns `unsupported` for include/extend execution semantics. Do not relabel
an extension as a base to obtain success, silently flatten paths into the finite
model, or claim native SysML v2 execution from a SysML v1 use-case pattern.
Parser/shape checks still apply to the authored native model.

Method basis: Lenny Delligatti, *SysML Distilled*, Chapters 5–6, especially the
use-case discussion on pp. 77 and 86. This is an original procedural adaptation;
the SysML v1 descriptions are not a CSE execution specification.
