# Technical documents

Use this guidance when the requested result is an engineering document, manual,
or drawing set. Follow the user's document standard and template when supplied.
Otherwise use a compact technical form suited to the reader's task.

## Select the form

| Reader's task | Primary content |
|---|---|
| Understand a system or concept | Scope, system boundary, functions and interfaces |
| Follow a modeled operation | Initial condition, actors, sequence, conditions and outcome |
| Perform a task | Prerequisites, ordered instructions, expected results and applicable warnings |
| Review an interface | Endpoints, direction, signal or material, type, units and unresolved mappings |
| Review a design decision | Question, relevant evidence, decision or open item, affected model IDs |

Use only the needed sections. State a fact once. Let a labeled figure or an aligned
table carry repeated relationships. Remove introductions that restate the title,
promotional headings, repeated conclusions and explanations of CSE's own process.
Keep source quotations, annotation inventories, test logs and the assessment
against user notes in a linked evidence file unless they are the requested result.
Keep a scope limit or unresolved interface in the document when it changes the
engineering reading. Record each such item once at its point of use.

## Write the technical content

Use complete, direct sentences with the responsible actor and a concrete verb.
Use the same approved technical noun for the same item. Prefer an action or
condition label to a miniature paragraph inside a diagram.

Distinguish a description, an instruction and a requirement. For example:

- Description: "The controller waits until the conveyor is idle."
- Instruction: "When the indicator is green, press START."
- Requirement: retain the source's approved modal and condition.

Preserve modality, negation, conditions, identifiers, numbers and units when
shortening text. Keep verification and validation distinct. Do not change an
observation into an instruction or requirement. Review wording against the
project terminology and applicable STE rules during drafting.

Select explicit prose budgets appropriate to the document. Run the
[prose checker](prose-checks.md) on text extracted from the delivered artifact,
including captions, tables and diagram labels. Preserve row and paragraph
boundaries. Report extraction gaps; an unchecked diagram cannot be covered by a
body-text pass. Repair excess wording without dropping engineering conditions.
Counts enforce the selected lexical budgets; they do not establish grammar,
complete STE conformity, completeness or technical correctness.

## Typeset the document

Use a functional title, document identifier, revision and page numbers. Record
approval or release status only when established. Choose normal technical body
sizes and a small heading hierarchy. Size the page to the content and print use;
do not shrink text to meet an arbitrary page count.

Use white paper, dark text, restrained rules and aligned fields as a starting
point. Add color, shading, texture or dimensional detail when it communicates a
defined engineering distinction. Select the notation from the model's meaning.
Keep decorative iconography out of formal symbols. A connector, state transition
and workpiece route need their own meanings and keys.

Keep content separate from layout. Generate editable diagrams and exports from
the same selected records. The optional [technical note stylesheet](../assets/technical-document/technical-note.css)
provides A4 landscape pages, a compact hierarchy and page footers. Supply the
project's embedded fonts and adjust the page or figure sizes to fit the content.
Inspect the actual PDF or image at reading scale for
clipping, font substitution, crossed labels and incorrect endpoints. Preserve
source/model links and the detailed check receipt beside the document. Return
the primary document first, then a short change and check summary.

The [adaptation record](technical-document-sources.md) identifies the inspected
references and the techniques retained from them.

## Retain current exports

Use [artifact freshness](artifact-freshness.md) when several model, calculation and rendering files produce a delivery. Capture inputs before generation, use fresh output paths, and check the retained receipt before delivery. A check must not replace stale evidence with a new success label.
