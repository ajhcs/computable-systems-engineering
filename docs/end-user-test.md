# Test the engineering skills as an end user

Open this repository as the Codex project and start a new conversation. The
three skills are registered under `.agents/skills/`; they are available only
in this repository. Their source remains under `skills/`, and the shared
parser and computation engine remain in this repository. No global skill or
plugin installation is required.

For a concept and scenario, write:

> Use the system-concept and operational-scenarios skills on the material below.
> Keep my raw materials out of Git.

Then supply the material. For a concept and broader CONOPS, use your original
“system-concept and CONOPS” wording. Natural names are sufficient. You do not
need to choose files, write SysML, install Java packages, or run checker
commands. The assistant handles local files and the pinned parser setup;
missing runtime prerequisites must be reported rather than silently skipped.

## What you should receive

- One saved SysML model or imported bundle with shared definitions and stable
  IDs, plus readable views of the concept and requested operational work.
- A concise explanation of source interpretations, proposals, assumptions,
  and unresolved questions. Consequential choices stay with you.
- Actual parser and draft-structure findings for each requested skill.
  Supported controlled clauses also receive grammar, binding, type, and unit
  checks; supported sampled clauses receive synthetic variable-influence tests.
- A separate account of what remains qualitative, unsupported, or untested.
  A successful parser check does not imply that every requirement or scenario
  has been behaviorally verified.

Raw material is read in place or from the conversation rather than copied into
the public repository. Private source references, the user-specific model,
and reports belong in ignored `work/` paths on `/workspace`. This keeps normal
Git staging from including them; it is not a protected data-loss prevention
boundary. Nothing in an ordinary authoring request authorizes publication of
your material.

If the material contains no precise checkable obligation, the assistant should
keep the draft useful, explain the missing detail, and mark a proposed
formalization for your review. It must not invent a threshold to produce a
pass. A genuine supplied-behavior review needs independent scope and trace
evidence. Generated synthetic tests are examples, not measured system behavior.

## How to judge your first trial

Check whether the concept captures your intent, whether the actors and boundary
make sense, and whether the scenario preserves the sequence and exceptions you
described. Inspect the proposed controlled clauses and their assumptions before
treating them as your requirements. Try a follow-up that changes one threshold
or scenario outcome and see whether the assistant updates the same model and
reruns the affected checks.

The current alpha can draft broad systems concepts and operational models. Its
computation covers the bounded profile in [sysml-v2-profile.md](sysml-v2-profile.md).
General SysML scenario execution, inherited-property computation, arbitrary
native constraints, full FRET semantics, formal FLIP coverage, Jev, and
protected acceptance remain future work. The separate JSON finite verifier is
still available, but prose or SysML scenarios are not silently converted into
that executable format.
