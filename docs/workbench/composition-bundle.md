# Physical-composition candidate bundle

This contract extends the existing inspect/rename candidate path. It does not
provide project storage, a successful required review or engineering acceptance.

The CLI accepts exactly one positional model file or `--bundle PATH`. The
bundle is JSON with exactly these fields:

```json
{
  "version": "cse-composition-bundle-1",
  "models": {
    "library.sysml": "package Library { part def Sensor; }",
    "context.sysml": "package Context { part sensor : Library::Sensor; }"
  },
  "linked_records": {}
}
```

`models` maps normalized project-relative names to exact UTF-8 model text. All
dependencies are explicit. Paths are labels inside the request, not disk access.
Empty, absolute, traversing, duplicate-normalized or platform-ambiguous names
are rejected. Combined input has the existing 128-file / 5 MB bound. Parsing
uses a sorted combined unit; returned files preserve original text and line
endings. Synthetic parse separators are never saved or edited as file content.

Each linked record is `{ "kind": KIND, "text": EXACT_JSON_TEXT }`. Current kinds:

| Kind | Authored facts and rename behavior |
|---|---|
| `display_labels` | Existing version-1 label records; only `labels[].element` changes. Aliases and titles retain exact wording. |
| `composition_layout` | Existing physical layout geometry; stable view/node/edge IDs, no native-name rewriting. |
| `composition_appearance` | Existing saved-kit v2 appearance; exact master/swatch IDs and local key, no native-name rewriting. |
| `retained_configuration` | Existing configuration-1.0/1.1 scope; exact bytes stay fixed. Affected native identity fields become explicit reconciliation findings. |

Native `cseWorkflow` documentation uses the existing CSE-WORKFLOW/1.0 or /1.1
record. Only each element's `native_name` binding changes. Native `cseViews`
documentation uses CSE-VIEWS/1.0 or /1.1; the adapter recognizes the existing
family-specific native binding slots. It does not execute or fully validate
those diagram records. Unknown fields/record roles need an explicit adapter.
Ordinary prose and source quotations remain verbatim, including an old name
when it is narrative rather than a declared binding.

JSON changes replace only affected string tokens at supported binding paths.
Duplicate keys, nonfinite numbers and unknown structured binding roles are
rejected. Source indentation is not reconstructed from Pilot's normalized
documentation body. The independent reparse compares the extracted native
facts and reference targets, and the expected documentary body transformation.

For inspect, supply `--project-id UUID`. For rename, also supply the saved
`--element-id UUID`, `--name NAME`, and the applicable expected digest:

- Single source: `--expected-source-sha256 DIGEST`.
- Bundle: `--expected-bundle-sha256 DIGEST`.

The bundle digest binds all supplied model names/bytes and linked record
names/roles/bytes. `--registry PATH` restores the saved element-ID mapping;
ambiguous external renames require reconciliation. The digest is an input
identity, not the future monotonic project revision or authenticated authority.
Retained scopes are explicitly supplied records; their byte hashes do not
authenticate an engineer's selection or an independent acceptance decision.

A rename returns the complete candidate files, linked records, registry,
source locations, configuration findings and scope reconciliation list.
An error publishes no partial candidate and leaves the input document intact.
The CLI never writes any supplied project file. Exit zero means candidate
preparation succeeded; configuration findings can remain unsuccessful and
must be read independently. Required-review success is not supplied by this
candidate command.

Current open edit obligations include quoted/Unicode replacement names and
reference spellings outside simple resolved namespace suffixes. The current
replacement name is bounded to 64 ASCII identifier characters. Unadapted
structured CSE records and native parser diagnostics still refuse a rename.
These are implementation gaps in the active capability; they do not narrow
the existing-support union or qualify a complete physical-composition editor.

The persistence layer must later commit these model/companion changes together,
with revision conflict checks, idempotent request receipts and history. That
obligation remains open in the physical-composition parity matrix.

[Saved physical diagrams](composition-diagrams.md) validate these companions
against actual native ownership and the source-bound selected view.
