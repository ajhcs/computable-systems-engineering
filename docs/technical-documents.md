# Technical documents

Use this guidance when the requested result is an engineering proposal, report, manual,
or drawing set. Follow the user's document standard and template when supplied.
Otherwise use a compact technical form suited to the reader's task.

## Select the form

| Reader's task | Primary content |
|---|---|
| Assess a proposal | Proposed work, deliverables, responsibilities, cost basis and acceptance terms |
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

## Select the visual reference

When project branding, custom fonts, SVGs, imagery or an existing graphic kit are
requested, resolve the intended source before layout. Follow the current request
and selected template or project profile before a kit's presentation defaults.
Example typography is not automatically the project's document standard. If
equally plausible references conflict and context does not resolve the choice,
ask which governs while continuing work that does not depend on it.

Inspect the relevant specimens and actual font files, color tokens and SVG or
image masters. Read only the resources needed for this output. Record their
source, revision and intended roles in the existing output source or evidence
record. For this pack's example fonts and icon bindings, start with the
[curated examples](../examples/ecosystem-diagram-reference/README.md) and
[component library](component-library.md), as applicable.
Use other kits only when present in the selected runtime or supplied by the
project; references in another checkout do not establish package availability.

Prefer suitable existing artwork and preserve its identity, license and recorded
adaptations. Carry the selected type, spacing and color roles into body text,
tables and figures. Identify any distinct formal-notation or mathematical font
needs. A kit's diagram font does not automatically govern document prose, and
plugin listing icons and colors do not define the document's visual identity.

When editorial illustration or cover art is requested, develop that composition
as artwork while preserving the meaning of formal model views. Use fitting
existing assets and create missing artwork as needed. Tables, ruled fields and
formal diagrams alone do not establish an illustrated composition. Keep the
page count and any existing content the user asked to preserve.

Render a representative page or figure early, then inspect the completed
exports at reading size. Compare the selected font families and weights with
the fonts that actually render or are embedded, and check the selected artwork,
palette and treatments against their source. Font loading, embedding, contrast
and bounds checks do not establish that the intended visual identity was used.
Report unavailable requested resources and identify any fallback instead of
claiming the requested identity passed. Visual review remains distinct from
engineering validation and user acceptance.

## Typeset the document

Follow the selected template and requested hierarchy. When those are unspecified,
use a functional title and document identifiers, revision and page numbers as
appropriate. Record approval or release status only when established. Choose normal technical body
sizes and a small heading hierarchy. Size the page to the content and print use;
do not shrink text to meet an arbitrary page count.

When no visual identity is selected, use white paper, dark text, restrained rules
and aligned fields as a starting point. Color, shading, texture and dimensional
detail may serve the selected visual identity or a defined engineering distinction;
keep decorative and semantic roles clear. Select the notation from the model's meaning.
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
