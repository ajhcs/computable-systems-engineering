# Project visual profiles

A visual profile records the reference selected for a particular output. It does
not establish CSE branding, accepted engineering meaning, permission to use
artwork, or approval of a document. Use the current request and supplied template
before an example's typography. Resolve an actual ambiguity with the engineer.

Copy [the profile template](../assets/technical-document/visual-profile.template.json)
into the project and adapt its font paths, role selectors, sizes and treatments.
The template's missing font paths are intentional: preflight fails until actual
resources are selected. Its sample sizes and palette are editable examples.
An existing project standard can remain in its own format; this JSON is useful
when the shared renderer or repeatable resource checks are needed.

## Select and preflight

Run from the selected project, using the resolved installed plugin root as
`<runtime>` and the project directory as `<project>`:

```sh
python3 <runtime>/scripts/visual_profile.py validate --root <project> --profile visual-profile.json
python3 <runtime>/scripts/visual_profile.py preflight --root <project> --runtime <runtime> --profile visual-profile.json
```

The optional `--client-profile`, `--project-profile` and `--example-profile`
flags describe already selected candidate files. Whole-profile precedence is
`--profile` (an explicit current choice), client, project, then example. These
flags do not infer the user's choice or scan for profiles. A missing or invalid
selected file fails; the helper never falls through to a lower-priority profile.
Make a project-specific copy for field-level overrides; implicit merging could
combine a family name from one reference with font bytes from another.

`--out <new-file>` retains a JSON receipt without overwriting an existing file.
Exit codes are 0 for pass, 1 for a resource failure, and 2 for malformed inputs
or an execution error. `validate` checks structure only. `preflight` checks
selected files, bounded headers and identities; it does not render them.

## Version 1 record

| Field | Contract |
| --- | --- |
| `version`, `id`, `revision` | `cse.visual-profile/1`, stable identifier, nonempty revision |
| `authority` | `kind`: request, client, project or example; `source`: the selected reference/revision or current request |
| `fonts` | Nonempty list of unique `id`, `family`, `path`, integer `weight` 1–1000; optional `style` (normal/italic/oblique), `postscript_name`, `sha256`, `source`, `license` |
| `typography` | Role names map to `font` ID, `size_pt` 1–144 and a nonempty `selectors` array. Selectors apply explicitly; order resolves overlapping roles. Include table text and SVG labels where needed. |
| `palette` | Named `#RGB` or `#RRGGBB` colors; empty is permitted |
| `figure`, `table` | Optional treatments: `selectors`, optional palette token `rule_color`, `rule_width_pt` 0–12 and `padding_pt` 0–144 |
| `assets` | Selected resources only; empty is permitted. Each has unique `id`, `path`, `kind` (svg/image), `role`, `source`, `license`, and `adaptations` array. Optional `sha256` pins expected bytes. |

Identifiers start with a letter and contain only letters, digits, dots, hyphens
and underscores, up to 96 characters. There are at most 64 combined fonts and
assets, 32 typography roles and 32 selectors per role. Unknown record fields,
duplicate JSON keys, nonfinite numbers and unsupported versions fail explicitly.

All selected resources are required. A path is normalized relative to the
explicit project root, such as `fonts/body.woff2`. `runtime:` explicitly selects
an installed package resource, for example
`runtime:examples/ecosystem-diagram-reference/fonts/IBMPlexSans-Regular.woff2`.
Absolute paths, traversal and symlink escapes are rejected. The location of the
profile file does not change resource path resolution.

Font paths support TTF, OTF, WOFF and WOFF2 headers. Uncompressed TTF/OTF name and
OS/2 tables supply actual PostScript names and weights when present; a conflicting
declared name or weight fails. WOFF/WOFF2 identity requires the renderer's actual
glyph and exported-PDF checks. A file's name does not establish its font identity.
Record `postscript_name` when established from the actual font or rendered output;
do not guess it from the filename. A font loading under a CSS alias is not by
itself proof that all requested text used that font.

Asset roles are `formal-symbol`, `illustration`, `editorial-art`, `logo`,
`photograph` or `texture`. Separate formal symbols and their model bindings from
editorial imagery. Keep source/artwork IDs distinct from occurrence, DOM and SVG
IDs. Suitable library components should be selected by bounded discovery and
exact ID through [the existing component workflow](../skills/generate-engineering-diagrams/references/component-agents.md).
`source` should retain that catalog ID and revision, `license` the actual terms,
and `adaptations` any recorded color, geometry, layout or labeling changes.
Pin the source SHA-256 when later export verification needs an immutable baseline.

Preflight captures each selected resource's resolved path, bytes and SHA-256.
SVG resources additionally receive a native-geometry fingerprint that ignores
paint, IDs, metadata and text but includes transforms and primitive geometry.
The fingerprint supports a bounded comparison; it does not establish correct
notation, endpoints, complete artwork similarity or an engineer's approval.
Image resources support PNG, JPEG, GIF and WebP signatures. Each resource is at
most 32 MiB, combined reads at most 128 MiB, profile records at most 256 KiB,
and SVGs at most 10,000 XML elements.

For PDF, browser-font, asset-placement and bounds checks, use the shared renderer
described in [technical documents](technical-documents.md). Inspect delivered
pages at reading size and retain the selected profile with their sources. A
preflight pass cannot replace actual rendered checks or visual review.
