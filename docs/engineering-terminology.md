# Engineering terms and standards alignment

CSE uses the distinctions below in recorded engineering work. They support clear
claims and tailored review; they do not certify a project or implement every
requirement of the cited standards. The reviewed public catalogues and glossary
sources are identified below; a complete normative clause-level conformity
assessment has not been performed.

| Term | CSE usage |
|---|---|
| System of interest | The particular system or system element being considered in the current question; state its boundary and environment. |
| Stakeholder need | A stakeholder outcome, concern or constraint; keep inferred needs proposed until their basis is established. |
| Requirement | A separately identified obligation with its source and applicability. Rationale, proposed implementation and observation remain distinct. |
| Verification | Assessment of specified requirements using relevant evidence and a stated method. A prototype trace supports only its selected requirements and conditions. |
| Validation | Assessment of suitability for intended use and stakeholder needs. Parser acceptance and a passing prototype trace do not establish this. |
| Architecture description | An expression of an architecture, with selected concerns and views; distinguish the description from the system/architecture itself. |
| Baseline and configuration identification | Identify the selected model, obligations, sources, implementation and evidence revisions. A digest identifies bytes; it does not approve intent or authenticate a decision. |
| Record disposition | The selected treatment of a record. This reference exercises authorized logical removal of declared SQL content/copies; distinguish it from physical item routing and the complete system-disposal life-cycle process. |
| Evidence | Identify origin, observation/measurement method, conditions, uncertainty and limits. Authored samples and executed prototype observations support different claims. |

The verification/validation distinction is cross-checked against the public
[NIST verification glossary](https://csrc.nist.gov/glossary/term/verification),
[NIST validation glossary](https://csrc.nist.gov/glossary/term/validation) and
[NASA product-realization guidance](https://www.nasa.gov/reference/5-0-product-realization/).
NIST identifies its source/adapted definitions; CSE does not treat one short
glossary entry as universal authority outside its context.

## Selected ISO/IEC/IEEE basis

- [15288:2023](https://www.iso.org/standard/81702.html): system life-cycle process
  framework and terminology, including acquisition/supply and system elements.
  Select relevant processes and tailor their application; the standard does not
  prescribe one life-cycle model, development method or modeling technique.
- [29148:2018](https://www.iso.org/standard/72089.html): requirements-engineering
  processes and information items. Keep requirement identity, source, content,
  applicability and evaluation evidence explicit. The ISO catalogue identifies
  this published edition as current/confirmed in 2024 and also lists a successor
  draft; CSE pins the published edition rather than treating a draft as adopted.
- [42010:2022](https://www.iso.org/standard/74393.html): structure and expression
  of architecture descriptions, viewpoints and model kinds. A diagram or parsed
  model alone is not a demonstrated conforming architecture description.
- [24765:2017](https://www.iso.org/standard/71952.html): shared systems/software
  engineering vocabulary and references to originating standards. The catalogue
  reports confirmation in 2026. Preserve project/domain definitions and unresolved
  mappings rather than substituting casual synonyms.

These are selected alignment references, verified on 2026-10-27. No normative
text was purchased or silently inferred from a catalogue abstract. Full conformity
would need the applicable normative provisions, declared tailoring and evidence
for the selected conformity claim. Missing access to those provisions remains a
limit; it is not a reason to halt ordinary concept exploration.

## Stricter review without automatic bureaucracy

For a selected verification, name the system of interest, purpose, requirements,
method, configuration, evidence origin and claim limits. Retain missing evidence,
unsupported analysis and unresolved applicability as non-successes when they
affect that selected scope. Keep actual performance, assumed parameters, targets
and proposed thresholds distinguishable and bound to their entities/units and
conditions. Engineer authority over intent and acceptance remains unchanged.

For substantial human-readable output, read it once as a standalone result, then
check its claims against the supplied evidence separately. Make local edits that
repair an actual meaning/flow problem; delete repeated setup when it adds no
useful distinction. Report conformance to the selected contract, source/factual
correctness and usefulness as separate judgments when a review is requested.

This writing adaptation follows the concepts-and-claims discipline in
[write-with-purpose](https://github.com/ajhcs/write-with-purpose/blob/main/skills/write-with-purpose/SKILL.md)
and the targeted semantic edits in
[edit-with-purpose](https://github.com/ajhcs/write-with-purpose/blob/main/skills/edit-with-purpose/SKILL.md).
It adds no external skill installation, grammar-engine dependency or automatic
rewriting hook. Source versions reviewed: writer 0.3.2 / editor 0.2.0, retrieved
through the repository connector; blob identities are retained in the private
implementation evidence. No third-party source code was copied.

## Open conformity questions

Use an applicable provision and its authorized normative text before treating a
standard as a computed obligation. Public catalogue scopes and selected textbook
notes support method selection, not complete clause coverage. The following is
an alignment/evidence map, not a conformance matrix or a new review gate:

| Selected basis | Existing CSE support | Still needed for a stronger claim |
|---|---|---|
| 15288:2023 | Tailored question, boundary, life-cycle support and purpose-specific verification/validation plans. | Applicable normative provisions, declared tailoring, actual process outcomes and objective evidence. |
| 29148:2018 | Requirement identity, source, separately retained selection, bounded grammar and evidence binding. | Applicable information-item/requirement-quality provisions and content/sufficiency review; grammar acceptance alone is insufficient. |
| 42010:2022 | Native-bound descriptions, explicit concerns and documentary views with retained cross-view links. | Applicable viewpoint/model-kind/correspondence and stakeholder-concern provisions; documentary view composition alone does not establish conformity. |
| 24765:2017 | Explicit project terminology and the verification/validation distinction. | Review of applicable normative definitions and project/domain mappings; a shared word is not proof of equivalent meaning. |

An unresolved normative-text or applicability question remains unassessed. Ordinary
concept drafting can proceed with that limit. Do not invent clause numbers,
substitute another edition silently, or call a tailored software check an ISO
certification. Project authority and acceptance remain engineer decisions.
