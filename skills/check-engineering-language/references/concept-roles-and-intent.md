# Concept roles and intent

Read this when defining vocabulary, connecting an ontology to native roles, or
reviewing wording that could change design freedom or obligations. It extends
the existing [controlled-English workflow](controlled-english.md); it does not
introduce a new vocabulary file, a new grammar checker or automatic role inference.

## Reuse identities and role bindings

First inspect the project's `foundation-1.0` terms and selected `english-1.0`
profile. Retain each term's namespace, ID, revision, definition, engineering kind,
grammatical class, approved forms and source basis. Inspect its uses, native
element identity and selected text before proposing a new concept. Identical
labels across scopes need not mean the same thing. A label match is insufficient
to merge identities, select an element category or establish synonymy.

Use the distinction needed by the current question; do not import an ontology
catalog wholesale. These are review prompts, not a mandated universal ontology:

| Concept | Question that distinguishes its role |
|---|---|
| Function | What transformation or action is performed, with what inputs and outputs? |
| Performer | Which entity performs the function in this configuration? Shared performance is possible; do not infer exclusive ownership. |
| Resource | What is used, consumed, occupied or made available, under which conditions? |
| Capability | What ability is claimed under specified conditions, and which functions/resources support it? |
| Goal | What direction or desired outcome guides choices without itself becoming a mandatory limit? |
| Constraint | What boundary limits the admissible design or behavior, under what applicability and authority? |
| Obligation | Who must do what, under which conditions, according to which accepted source? |

The current foundation kinds and native map are deliberately smaller: a function
binds to an action; resource/actor/capability/subject bind to parts; objective
binds to a concern; scenario/behavior bind to actions; use case binds to a use
case. A performer can be an actor/resource in a selected allocation; it is not a
new supported foundation kind. Goal, constraint and obligation are intent roles,
not new permitted `kind` values. Do not insert unsupported kinds or relations
into a profile to make a prose distinction look machine checked.

Keep any required distinction that lacks an executable representation in the
source-linked review record and identify the missing supported check. Route
native constraint/requirement work to the applicable existing native or
controlled-clause check. Native category agreement checks the declared binding;
it does not prove that a concept is correctly classified in the real system.

Use noun forms for entities and verb phrases for functions/operations where the
project chooses that convention. Keep engineering kind separate from grammatical
class. `approved_forms` records explicit inflections/capitalizations and includes
the canonical label; do not hide a synonym or changed meaning there. Refresh a
profile candidate after an accepted draft wording change, retain old pins and
run the existing checker. A changed meaning/class/form invalidates old term pins.

For a selected diagram, preserve the same concept ID, namespace, revision and
digest while keeping icon/asset identity separate. Matching icons do not prove
matching meaning. Read [diagram generation](../../generate-engineering-diagrams/SKILL.md)
only when producing that view; use [architecture](../../develop-system-architecture/SKILL.md)
when the question requires functions, performers, parts, allocation or interfaces.

## Elicit intent and stopping conditions

Use only the questions necessary to resolve the current uncertainty. Preserve
the author's actual modality and source wording while investigating:

- Is the statement a desired direction, a hard limit, an obligation, an observed
  fact or an assumption? Who supplied and can accept that intent?
- What actor/system boundary and conditions make it applicable? Does it limit
  the outcome or prematurely select a particular solution?
- What evidence would distinguish an improvement from an acceptable result?
  Is there an engineer-selected measure, unit, population and observation window?
- What would justify continuing, changing course or stopping this investigation
  or operation? Who owns that decision and what unresolved evidence remains?

“Reduce delay” can remain a goal. “Maximum delay” may express a limit, but needs
its actual authority, applicability and bound. Neither phrase supplies a numeric
target or a `shall` obligation. A scenario's terminal state is not automatically
an accepted operational stopping rule. Record absent criteria as open questions;
do not optimize arbitrary proxies or turn preferences into requirements to pass.

Use [measure definitions](../../define-engineering-measures/SKILL.md) when a
measure must be specified, and [evidence planning](../../plan-engineering-evidence/SKILL.md)
when an evaluation needs a plan. This workflow supports an engineer's review;
lexical matches, selected forms and native categories do not resolve arbitrary
meaning, establish full ontology coverage or prove grammar/STE conformance.
