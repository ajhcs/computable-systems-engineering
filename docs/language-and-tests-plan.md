# Computable language and tests: simple plan

Proposed build order. The detailed [language proposal](language-and-tests-proposal.md)
records the broader design. The standalone [profile 1](requirements-language-v1.md)
implements the narrow parser and supplied-trace checks in steps 2, 3, and part
of 6. Generated tests, integrated views, and protected execution remain future
work.

- **1. Select one small example.** Connect a need, a requirement, and an operational scenario. Identify what must be checked and keep assumptions, goals, and unknowns visible.
- **2. Define the first language rules.** Start with **always**, **within**, and **until**. Specify scope, triggers, clock, units, deadlines, and incomplete evidence. Evaluate reuse of a pinned FRET version, retaining attribution and applicable license notices. References: [FRET requirement language](https://github.com/NASA-SW-VnV/fret/blob/master/fret-electron/docs/_media/user-interface/writingReqs.md) and [timing semantics](https://github.com/NASA-SW-VnV/fret/blob/master/fret-electron/docs/_media/user-interface/examples/timing.md).
- **3. Compile each clause into one precise model.** Give it a stable ID and source link. A deterministic parser checks the supported grammar, declarations, types, and units. Unsupported wording remains unresolved.
- **4. Make the meaning reviewable.** Generate the sentence, explanation, and timeline from that model. The engineer resolves consequential interpretations before they become accepted intent. Reference: [FRET trace visualization](https://github.com/NASA-SW-VnV/fret/blob/master/fret-electron/docs/_media/UsingTheSimulator/ltlsim.md).
- **5. Generate meaningful tests.** Produce satisfying, violating, boundary, and incomplete examples; show which conditions each test exercises. Begin with explicitly bounded coverage inspired by FLIP, without claiming full FLIP coverage. References: [FRET test generation](https://github.com/NASA-SW-VnV/fret/blob/master/fret-electron/docs/_media/exports/testgenManual.md) and [Katis, Mavridou, and Pressburger, 2025](https://ntrs.nasa.gov/citations/20250002869).
- **6. Check actual behavior.** Evaluate supplied scenario executions or recorded observations against the requirements. Check consistency separately from behavioral satisfaction. Missing evidence, unsupported checks, or exhausted analysis limits cannot produce a successful required review. Generated examples alone are not implementation evidence.
- **7. Explain results and revise.** Return findings, counterexample timelines, coverage gaps, and exports tied to the exact revision. Repair draft behavior and rerun; route changes to intended meaning back to the engineer. Changing a clause regenerates affected tests and invalidates stale results.
- **8. Prove the complete workflow, then connect all three skills.** Demonstrate a known violation being detected, repaired, and rechecked. Compare equivalent cases with the pinned FRET/backend, then expose the workflow through concept, CONOPS, and scenario skills while keeping each independently usable. First deliverable: one requirement, its explanation and diagram, generated tests, and a reproducible behavior-check report.

The diagram shows the operating flow the plan will build. The language rules
govern compilation, rendering, test generation, and evaluation throughout.

```mermaid
flowchart TD
    A["Concept, CONOPS, or scenario<br/>Need, source, and selected obligations"]
    B["Assistant and engineer<br/>Draft a controlled requirement"]
    C["Deterministic compiler<br/>Check grammar, types, units, and clock"]
    D["One versioned meaning<br/>Generate sentence, explanation, and timeline"]
    E{"Engineer confirms<br/>intended meaning?"}
    F["Requirement baseline<br/>Meaning and review scope recorded"]
    G["Generate tests<br/>Examples, boundaries, and coverage obligations"]
    H["Candidate behavior<br/>Scenario model or recorded observations"]
    I["Deterministic evaluation<br/>Consistency and behavior satisfaction"]
    J["Evidence report<br/>Results, counterexamples, and coverage gaps"]
    K["Engineer reviews findings<br/>Decision and scoped artifact views"]

    A --> B --> C --> D --> E
    C -->|Malformed or unsupported| B
    E -->|Revise interpretation| B
    E -->|Yes| F
    F --> G
    F -->|Required properties| I
    G -->|Test cases and coverage obligations| I
    H -->|Actual modeled or observed behavior| I
    I --> J --> K
    K -->|Repair behavior or collect evidence| H
    K -->|Propose a meaning change| B

    classDef human fill:#fff4d6,stroke:#9a6815,color:#242424
    classDef program fill:#e9f2ff,stroke:#3568a8,color:#242424
    classDef artifact fill:#edf5ee,stroke:#487b53,color:#242424
    class B,E,K human
    class C,G,I program
    class A,D,F,H,J artifact
```

Yellow denotes human/assistant work, blue deterministic programs, and green
artifacts or evidence. Recording an engineer decision in this workflow does not
implement the separate [protected acceptance boundary](protected-runner.md).
