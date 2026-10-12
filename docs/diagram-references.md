# Selecting and validating a diagram reference

**Rejected experimental draft, 2026-10-01.** Cole rejected this source type. This material is preserved as historical evidence, not approved professional references, current selection guidance, or publication/rollout material. See [draft status](diagram-reference-draft-status.md). Wait for genuine attributable project bundles before adaptation.

## Historical draft content

Choose the smallest [matched example](../examples/diagram-reference/README.md) that answers the current question: boundary/item direction, action order, supported obligation, or code-grounded architecture. Preserve the formal model's IDs, types, boundary, source/target direction, order, and uncertainty in the image and explanation. Keep the view scoped; omitted elements are not absent from the system.

A custom view of SysML elements is different from a conforming SysML graphical diagram. State the notation and claim boundary. An unlabeled arrow cannot safely stand for item transfer, control succession, allocation, and a dependency at once. Opposite directions carrying different items need distinct arrows. Narrative questions do not supply executable decisions.

Use parser and supported semantic checks before rendering, then inspect the actual image at reading size. Check endpoint direction, labels, crossings, clipping, and implied claims against the source. Editable draw.io carries presentation geometry; revise engineering meaning in the authoritative model and regenerate. Report parser acceptance, bounded evidence results, visual inspection, and untested editor interchange separately.

Prefer a selected pair of image plus text/model over a large instruction catalogue. Use the existing contracts on demand; do not force a model to follow a drawing recipe when another view explains the engineering question better.

