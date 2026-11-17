# Physical diagrams over saved project state

The physical renderer reads an actual `CompositionProject.snapshot()`: exact
SysML, the stable registry, retained scopes and presentation companions. Its
offline reader supports selecting a drawn element and inspecting that element's
native properties. It is a read-only saved artifact, not the connected workbench
or proof of Codex/ChatGPT integration.

## Authoritative meaning

The existing package-owned `doc cseViews` record uses `CSE-VIEWS/1.1`. A physical
view has exactly `id`, `kind: "physical_composition"`, `mode` and `nodes`.
Each node has `id`, `element`, `parent`, `level` and `edge`. Nodes bind uniquely
to native part definitions in `definitions` mode or native usages in `usages`
mode. The single root has null parent/edge and level zero. Non-root levels are
their parent's level plus one, at most 16. Each edge retains its own identity.

The parent must be the native declaring owner. A selected inherited member does
not acquire the selected context as its native owner. Usage-composition children
must be composite. A package-level root is the selected diagram context; it need
not itself be composite. These rules preserve the earlier physical projection's
distinction between definition hierarchy and usage composition.

Literal multiplicities now appear on usage frames, including optional `[0..1]`
and suppressed `[0]` declarations. Default bounds remain available in properties.
Inherited or unsupported bounds retain their status. When a bound has explicit
syntax, the native parser supplies its UTF-16 source span: `[1..*]` remains
visible alongside `multiplicity: unsupported`. This does not evaluate an
expression or establish installed presence. No regular expression parses SysML
to supply these facts.

Supertypes, redefinitions and subsettings remain native facts and appear as
annotations/properties. Retained configuration checks run independently and keep
their own scope bytes and statuses. The reader lists declarations outside the
chosen view. A valid diagram is not a successful required configuration review.

The [native bound edit](composition-multiplicity.md) can author finite literal
lower/upper bounds on selected usages. Saved graph and inspector values derive
from its independently reparsed source. Defaults, inherited status and unsupported
expressions are not invented numeric values; preview and configuration findings
remain distinct from a saved transaction receipt.

## Original artwork and typography

The renderer reuses the preserved `kit_fonts.py` and `kit_templates.py`
implementations byte-for-byte. Their [source pins](composition-kit-source.json)
identify the reused unpublished revision G files. It uses actual catalog-pinned
rectangle frames, patterns, opaque text backing, compact figure-heading rules
and nonconnecting crossing-gap artwork. No arrowhead is assigned to native
ownership. Unrelated overlapping routes are refused rather than joined.

DejaVu Sans and Mono use the exact saved TTF bytes, real advance metrics and
notices. A physical-view adapter delegates original ASCII measurements unchanged
and adds a fixed Latin, Greek, Cyrillic and engineering-symbol profile derived
from those same four TTFs. Its [metrics](../../assets/workbench/composition-font-metrics.json)
stay outside the original kit; exports include their exact bytes and hash.
Absent glyphs, combining/RTL/complex shaping and other unqualified characters
refuse explicitly. There is no automatic normalization or system-font fallback.
At the fixed 28/24-unit roles, original text keeps its eight-unit opaque backing
padding. Added glyphs use twelve units to cover detached accent overhang,
including wrapped monospace references; text advances and positions stay fixed.
Each node records that content-fit adaptation alongside its original master.
Node labels retain the prior 28-unit bold treatment, 1.4-em minimum
baseline spacing, content-fit wrapping and the preserved renderer's centering.
Node rules retain its 3-unit adaptation; hierarchy routes retain 2.5-unit rules.
Colors select saved swatch IDs. Text, boundary and pattern contrast are checked.
Pattern meaning comes from the authored local key; it does not create a material,
state or other model property. Display aliases and titles remain separate from
native names; the mode stays visible when an authored title is used.

Ownership is oriented from declaring owner to member. The projection records
`directed: true` and `arrowheads: false` separately, preserving the established
unarrowed hierarchy notation and the native asymmetric relationship.

## Presentation transactions

Two explicit linked-record roles extend the bundle:

| Role | Existing companion contract | Identity behavior |
|---|---|---|
| `composition_layout` | `cse-diagram-layout-1.0` with view, canvas, exact node boxes and exact edge point lists | Binds authored node/view/edge IDs, not native names. |
| `composition_appearance` | `cse-diagram-appearance-2.0` for `engineering-palette-complete-05` | Selects exact templates/swatches and the authored local key. |

Layout canvases remain bounded at 8192 units. Selected coverage, finite geometry,
text fit, frame overlap, exact endpoint contacts, route clearance and crossing
identity are checked. This physical path has no state occurrences or sequence
rows. It does not expose another engineering capability.

An authored local key reserves a full-width footer, with 32 units of clearance
above its saved legend table for frames and routes. The table reuses the original
`palette-refined-documents-documents-page1-navigation-legend` rules, with
content-fit heading/body cells and independently editable authored text. This also covers detours and shared
trunks; native endpoint validity alone cannot prevent a route from crossing a
key. A colliding candidate is refused before saving. Reroute it above the footer
or explicitly enlarge its canvas; the renderer never moves authored geometry
or hides key text to make it pass.

Unrelated routes require the saved routing policy's 15-unit visible-ink gap
(6s at s=2.5). At the current 2.5-unit connector stroke, parallel centrelines
therefore need 17.5 units of separation. The same finite-segment check covers
diagonal routes and near-missing endpoints. Intentional fanout from one native
parent and explicitly marked nonconnecting crossings retain their distinct
treatments. Crossing artwork needs room before bends and endpoints. These are
graphic clearances; they do not create engineering connections or physical
installation requirements. Invalid candidates are refused before publication.

An explicit layout operation uses the existing project transaction boundary:

```json
{
  "operation": "set_layout",
  "request_id": "e9327d11-6521-4a2d-8c72-c6dc3d8440b2",
  "expected_revision": 1,
  "layout": {
    "version": "cse-diagram-layout-1.0",
    "view": "VIEW_ID",
    "width": 1000,
    "height": 700,
    "nodes": {"Root": {"x": 56, "y": 160, "width": 360, "height": 90}},
    "edges": {}
  }
}
```

Use the actual rendered layout and its complete binding inventory. The example
above is only a one-node shape. Moving or resizing frames changes the layout
companion, not SysML, the registry or configuration obligations. The server
checks the whole candidate and commits it atomically with the usual monotonic
revision and idempotent receipt. Reload and restore retain the saved geometry.

Renames retain presentation IDs and update native view bindings. Every declared
version-1.1 physical view is rendered before project preview or publication,
including default layouts without appearance/layout companions. Retained
presentation companions are revalidated through that same path. A rename that would
clip an explicitly saved frame currently returns `presentation_conflict` without
advancing the head; enlarge the saved frame first. Automatic content-fit repair
of manually authored layouts remains an open obligation, not a reduced name
support target.

## Export and independent checks

```sh
python3 scripts/composition_project.py render --project work/private-composition.git --view-id PC_USAGE --output work/composition-view-r1
python3 scripts/composition_project.py check-render --project work/private-composition.git --view-id PC_USAGE --output work/composition-view-r1
```

The artifact contains SVG, the interactive inspection reader, source/property
bindings, layout, kit usage, registry, exact model/companion bytes, original used
masters and exact font files/notices. Its manifest binds the saved commit and
revision, sources, renderer implementation and output bytes. Fresh checking
reconstructs the artifacts from the saved authoritative project; edited drawings
or a later model/layout revision fail correspondence. An existing export folder
is never replaced. The artifact is not a project transaction acknowledgement or
a lossless external-tool import claim.

The reader keeps readable scrolling on narrow screens. Its
[overview/readable navigation](composition-navigation.md) uniformly scales the
same complete SVG for orientation, then returns to native 100% scale for reading
and selection. Screen navigation does not alter the layout companion or the
exported SVG. Native selection and mode changes lock during an active gesture.
Mouse and keyboard
selection expose a context containing project, view, UI session, saved model
revision, commit, bundle identity, element UUID and occurrence ID. That context
describes an artifact selection. It does not register WebMCP, grant project
access or replace retained review scope.

## Remaining physical-capability gates

The [local connected editor](composition-interaction.md) embeds this saved reader
and invokes existing rename, multiplicity, layout and restoration transactions. Its pointer
move/resize and keyboard bounds controls remain within the physical capability;
hosted application integration is still open. Creation, deletion, reparenting,
remaining property editing, collapse/reveal, legacy appearance compatibility, full drawing
identification/Draw.io export, quoted/Unicode glyph qualification, remote
persistence and both actual application journeys remain open. Referenced
resources need their own appropriate presentation; they are not converted to
owned composition. Current numeric/view limits do not reduce the agreed union
of existing capability support. The parity matrix remains active and incomplete.
