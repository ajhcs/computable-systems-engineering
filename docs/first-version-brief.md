# First-version brief

**Readiness:** ready to start a bounded implementation and review its first examples. The purpose, users, workflow, first defect classes, reference case, and limits are defined. The exact grammar, state semantics, and review profile still need to become an executable contract. The defaults below are implementation proposals; they are not accepted engineering requirements for a real system.

## Purpose and authority

Help a systems engineer develop concepts, CONOPS, and operational scenarios with less repetitive checking. The LLM elicits and investigates proportionately, proposes a structured model change, invokes a deterministic program, and repairs reported defects. The engineer directs consequential interpretations, assumptions, thresholds, priorities, tradeoffs, and selection. A discussion, small change, or unresolved question can be the whole work unit.

The shared model is the durable representation. Human documents, diagrams, and machine exports expose scoped views. Computability comes from explicit types and semantics, not from the file extension. Plain language remains useful for intent and qualitative evidence; it is not silently treated as an executable predicate.

## Existing baseline

The repository contains three independent skills and their version-1 JSON helpers. They check structure, references, review completeness, and certain explicit numeric observations. Concept assessments are declared findings, not independently verified feasibility. Current operational steps describe exchanges but have no executable guards or effects.

The next work adds a small logical verifier. It does not require replacing the skill methods or converting every conceptual-design statement into a mandatory requirement. Keep compatibility with existing records through explicit versioning or a documented adapter.

## First computational scope

| Check | Required representation | Useful result |
|---|---|---|
| Statement syntax | Statement category and a documented structured grammar | Missing subject, malformed predicate, or incorrect normative modality. |
| Declarations | Stable IDs and a symbol table | Undeclared actor, property, state, exchange, or duplicate identifier. |
| Types and units | Declared property/value types and exchange fields | Incompatible connection, invalid value, or incompatible unit. |
| Trace structure | Typed directed links and an explicit review profile | Broken link, wrong target kind, or missing required coverage. |
| Requirement consistency | Applicability conditions and predicates with defined semantics | Unsatisfiable supported obligations under an applicable context, with affected IDs and evidence. |
| Scenario execution | Initial states, guards, effects, external inputs, and terminal states | Unreachable step, failed precondition, missing data, or reachable unintended dead end. |
| Required progress | Explicit completion obligation and analysis scope | A branch cannot reach required completion within the modeled scope, or analysis is incomplete. |

Apply SHALL rules to mandatory requirement statements. Needs, goals, facts, assumptions, and observations have distinct roles. A correct trace structure does not prove that a requirement satisfies the linked need. A well-formed declaration does not establish source truth.

## Proposed defaults to make the first increment small

1. **One Python CLI and a small library.** Separate parsing, declarations/types/traces, finite logic/scenario analysis, and report generation. Add no server, UI, database, agent framework, or modeling-tool exporter to this increment. Use only the standard library unless a solver demonstrates a concrete simplification.
2. **Structured predicates first.** Use references, literal values, Boolean connectives, and typed comparisons. Render controlled requirement statements from the structure. Free-form source text remains linked evidence; do not claim to parse its meaning automatically. Do not execute Python, JavaScript, or other code embedded in a model.
3. **A finite first state model.** Start with booleans, finite enumerations, and bounded integers. Quantities use declared units and explicit scales; require compatible units initially, with no silent conversion. Avoid binary floating-point equality as requirement semantics. Unbounded arithmetic and continuous behavior are outside the initial analysis.
4. **Step-based scenarios.** Define the initial set, guard evaluation, atomic effects, unchanged properties, data availability, and the points at which external inputs may change. Declare intentional terminal states. Loops and waiting for external events are not automatically defects. Distinguish structural connectivity from executable state reachability.
5. **Document quantifiers.** Separate environmental inputs from controlled responses. Check whether applicable obligations can be satisfied together for each allowed input context; do not obtain a pass by selecting one convenient environment. Detect unsatisfiable sets, including conflicts requiring more than two requirements. Report the implemented scope instead of claiming full reactive realizability.
6. **Explicit analysis limits.** A finite exploration cap or timeout returns an incomplete result. An exhaustive result over a complete declared finite state space may support a proof within that model. A search to depth N establishes only the stated bounded property. “Some path reaches completion” differs from “every allowed execution eventually completes”; do not conflate them or invent fairness assumptions.
7. **Explicit review profiles.** A draft can be incomplete. A required review has a separately identified obligation set and scope. A focused review includes transitive dependencies and retains relevant global checks. The draft cannot redefine what a required review was supposed to cover.

Before coding the logic, write one small valid fixture and expected results for the failure and valid-exception cases below. Use them to document the semantics. If a choice changes the engineer's intended meaning or obligations, present a targeted decision; ordinary implementation choices do not require repeated permission.

## Result contract and repair loop

Every result identifies the artifact revision, dependency digests, checker/rules version, selected scope, expected and completed obligations, analysis limits, rule ID, affected IDs, status, and explanation. Supply a counterexample, conflicting set, or path when supported by the analysis.

Distinguish `pass`, `fail`, `unknown`, `unsupported`, `not_run`, and `error`. An incomplete required check is not success. A draft's “well formed” result is separate from complete review, semantic validation, real-world feasibility, and stakeholder acceptance. Return compact findings by default and detailed evidence on request; order diagnostics deterministically.

The assistant changes the affected candidate and reruns the checker. A change to accepted intent, a relaxed requirement, a deleted obligation, or narrowed applicability is an engineering proposal, not an ordinary repair. Stop an unsuccessful loop at a declared effort limit and surface its unresolved cause.

## Reference case and completion evidence

Use a small attributed slice of [FHWA's CARMA Detailed Concept of Operations](https://www.fhwa.dot.gov/publications/research/operations/20064/index.cfm), Chapter 3, highway merging. Printed pages 23–36 correspond to PDF pages 34–47 in the linked publication. Record the retrieved revision and errata. The document has identified needs, entities, requirements, operational sequences, and a traceability matrix.

Formalize a few connected statements, not the whole report. Keep every interpretation and unresolved detail visible. For example, an approximate transmission interval does not supply an exact tolerance. The source is realistic material, not a guaranteed error-free oracle or a vehicle-safety proof. Use a wholly synthetic case to settle tool semantics before the public-source adaptation.

The first increment is complete when it has:

- A documented, versioned minimal model and working CLI for the declared check classes.
- A valid connected fixture and known-defect variants: undefined entity, type/unit mismatch, broken trace, overlapping conflicting constraints, a multi-requirement conflict, missing data producer, disabled path, and nonterminal dead end.
- Valid-exception tests for mutually exclusive modes, intentional completion, a permitted loop, and explicit external inputs or waits. No blanket ban on cycles or waiting.
- Tests showing unsupported semantics, exceeded limits, malformed records, stale evidence, and missing required checks cannot become an overall successful required review.
- Focused-view and whole-model results compared on the same relevant obligations. Measure tokens under a named tokenizer plus total repair turns; report measurements without promising universal savings.
- A source-linked reference slice, with its proposed formalization reviewed by the engineer before describing it as accepted.
- Clear installation/use instructions and regression evidence on Linux. Record Windows results separately if exercised.

## FRET reuse and protection milestones

Investigate FRET's compiler and CLI as a bounded feasibility spike. Document what can actually be reused, dependency/install cost, supported semantics, and licenses. Do not fork its UI or make the first checker depend on the full application by default. Compilation, consistency, realizability, and checking a supplied behavior are different claims. Unknown or quoted informal content must remain outside a formal pass.

The protected runner is a distinct milestone with the boundary in [model-and-verification.md](model-and-verification.md). Accepted obligations, trusted checker code, and authoritative results must be outside the drafting agent's write authority. A same-user local CLI cannot enforce that separation with instructions or hashes alone. Test attempted scope deletion, checker changes, forged results, stale receipts, and unauthenticated acceptance before claiming resistance to bypass. The first logical checker may ship as an alpha while that boundary remains explicitly unimplemented.

Deferred: unrestricted natural-language understanding, unrestricted temporal logic, physical realism, implementation correctness without an implementation model/evidence, general AGI/ASI assurance, lossless SysML/Draw.io/Capella/Cameo conversion, and a universal ontology. Add capabilities when a concrete engineering case requires them.
