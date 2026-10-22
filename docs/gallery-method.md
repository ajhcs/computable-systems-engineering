# Reading and reproducing the engineering gallery

The [engineering gallery](../examples/engineering-gallery/README.md) follows one fictional water-sampling station through its concept, operating scenarios, documentary views and computable checks. Its people, equipment, timing limits and evidence are authored demonstration choices. They are not measured operations, accepted requirements for real equipment, or a water-quality or safety assessment.

## Which artifact supplies which meaning?

| Artifact | Authority within this example | What a successful check establishes |
| --- | --- | --- |
| SysML source | Concept, declared parts/actions/requirements, narrative scenarios and opt-in documentary view records | Pinned native syntax/reference checks, requested draft shape and the explicitly supported CSE annotations |
| Separate finite version-2 JSON model | Its own finite properties, typed data, guards, atomic effects and completion policy | The named finite consistency and scenario obligations within declared domains/caps |
| Semantic ledger and trace mappings | Explicit correspondence, selected IDs, documentary allocation and omitted scope | Declared references and mapping kinds are consistent; a mapping does not convert one engine's semantics into another's |
| Independent scope manifests | Expected requirement/clause/scenario inventories for the selected checker | Candidate obligations match the supplied inventory; the file does not authenticate an engineer decision |
| Synthetic sampled/event evidence | Authored observations and correlation records over a finite window | The supported monitor's result for those inputs, with counterexamples or incompleteness where applicable |
| SVG/HTML/PNG companions | Human readings of the selected source facts | Reproducible source-bound presentation plus separately recorded visual inspection; no native-editor roundtrip or behavior proof |

The finite scenario model is separately authored. There is no automatic, lossless or executable SysML-to-JSON conversion here. A documentary allocation assigns an explicit illustrative responsibility; it is not a native port connection, implementation binding or proof that the assigned component can perform the function. Function decomposition, ordered messages and executable guard/effect transitions retain distinct labels.

## Definitions and primary references

The following short paraphrases locate the engineering vocabulary. They do not expand the CSE implementation's support. The linked OMG document currently identifies itself as SysML 2.0 Part 1, **formal/2026-03-02, March 2026**, inspected 22 October 2026. The runtime remains the separately pinned **Pilot 2025-09 / kernel 0.52.0**; reading the newer specification is not a conformance claim.

| Term | Meaning used when reading a model | Official reference |
| --- | --- | --- |
| Part definition / usage | A structural classifier and a declared use of it | [OMG SysML 2.0, §7.11](https://www.omg.org/spec/SysML/2.0/Language/PDF#page=90) |
| Allocation | An assignment of realization responsibility between model elements | [OMG, §7.15](https://www.omg.org/spec/SysML/2.0/Language/PDF#page=110) |
| Action definition / usage | A classifier for performances and a declared action use | [OMG, §7.17](https://www.omg.org/spec/SysML/2.0/Language/PDF#page=117) |
| Calculation | An action-like computation with a designated result | [OMG, §7.19](https://www.omg.org/spec/SysML/2.0/Language/PDF#page=154) |
| Constraint | A logical predicate with a Boolean result | [OMG, §7.20](https://www.omg.org/spec/SysML/2.0/Language/PDF#page=157) |
| Requirement | A statement of necessary conditions concerning a subject | [OMG, §7.21](https://www.omg.org/spec/SysML/2.0/Language/PDF#page=161) |
| Verification case | A case whose result judges specified requirements for its subject | [OMG, §7.24](https://www.omg.org/spec/SysML/2.0/Language/PDF#page=173) |

NASA's [Requirements Verification Matrix guidance](https://www.nasa.gov/reference/appendix-d-requirements-verification-matrix/) calls for an identifiable requirement, its source and a verification approach. The gallery follows that traceability pattern for its fictional obligations. A typed trace records the declared relation and endpoints; it does not itself demonstrate satisfaction. NASA's [Product Realization guidance](https://www.nasa.gov/reference/5-0-product-realization/) distinguishes evidence of requirements compliance from validation of intended use. Neither local program output nor populated approval fields supplies stakeholder acceptance.

## Interaction scope

The example's selected operator, courier and custodian actions are manual sample handoffs or protocol-level receipt/status exchanges. The case guide records those dispositions against its scenarios. No station screen, new GUI command, credential flow or accepted field inventory is being designed here. The offline artifact browser is read-only documentation, not the proposed station's interface. A later interface-design question would follow the [interaction-walkthrough workflow](interaction-walkthroughs.md), with applicable precedents and a trace-linked low-fidelity sketch before implementation. No wireframe or control semantics is invented merely to fill this modeling gallery.

## Reproduce and challenge the example

Start with the [case walkthrough](../examples/engineering-gallery/water-sampling/README.md), including its selected model/evidence IDs and expected outcomes. From a complete repository checkout with Python 3.10+ and the pinned parser installed:

```sh
python3 scripts/install_sysml_parser.py
python3 examples/engineering-gallery/water-sampling/build.py --output work/gallery-reproduction
python3 examples/engineering-gallery/water-sampling/build.py --check
python3 scripts/check.py --require-sysml
```

Use a fresh output directory for generation. The native parser and monitor are local; no model is sent to a hosted service. The case's negative controls are expected refusals or non-successes, not defects to hide by weakening an obligation. Read each result's claim scope, completed obligations, selected scenarios, caps and input digests. An observation ending before a deadline and an exceeded exploration cap do not establish success. A definite violation remains visible even when some other analysis is incomplete.

The [completion matrix](capability-completion.md) maps the architecture's promised check classes to actual entry points, example evidence and remaining limits. Existing [legacy concept helpers](../examples/tool-library/README.md), the [finite record contract](verifier-v2.md), the [SysML profile](sysml-v2-profile.md) and the [controlled-language contract](requirements-language-v1.md) remain independently useful. No legacy prose acquires executable guards merely because another view uses the same names.

## Inspect the views before accepting a change

Read the small overview first, then open the detailed view at its intended size. Wide formal content should scroll rather than shrink its labels. Match function parents, message order, responsibility mappings, identifiers and quantities against the selected source records. Inspect actual pixels for clipped labels, overlaps, disconnected endpoints, error placeholders and missing annotations. Keep the source model, edited view, trace/evidence and review receipt revisions together. After a bound input changes, regenerate and rerun the affected checks.

The publication receipts distinguish native parser acceptance, bounded computations, artifact reproducibility, independent code/model review and actual image inspection. They do not establish physical correctness, engineer acceptance, a protected runner, continuous behavior, temporal realizability, full SysML execution or a graphical-editor edit/save/reopen roundtrip.
